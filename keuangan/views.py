from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.db.models import Sum, Q, Value, DecimalField
from django.db.models.functions import Coalesce
from .views_laporan import compute_account_totals_for_user
from django.db import transaction
from datetime import datetime, date
from django.utils.dateparse import parse_date as django_parse_date
import json
from .models import Jurnal, Akun, Transaksi, UserProfile
from .forms import TransaksiForm, AkunForm, CustomUserCreationForm, UserProfileForm, UserUpdateForm
from .pdf_utils import (
    export_jurnal_pdf, 
    export_buku_besar_pdf, 
    export_neraca_saldo_pdf, 
    export_laporan_keuangan_pdf,
    create_pdf_response
)
from reportlab.lib.pagesizes import A4 # Import ini diperlukan untuk fungsi daftar_akun_pdf

# --- Custom Login View ---
class CustomLoginView(LoginView):
    """Custom login view dengan redirect untuk user yang sudah login"""
    template_name = 'registration/login.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return '/'

# --- Helper Function ---
def parse_date_flexible(val):
    if not val:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    try:
        return date.fromisoformat(s)
    except Exception:
        pass
    for fmt in ('%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    try:
        pd = django_parse_date(s)
        if pd:
            return pd
    except Exception:
        pass
    return None

# --- Dashboard View ---
@login_required
def dashboard(request):
    user_akun = Akun.objects.filter(user=request.user)
    # Filter Transaksi yang terkait dengan akun milik user (lebih efisien)
    user_transaksi_ids = Transaksi.objects.filter(jurnal__akun__user=request.user).values_list('id', flat=True).distinct()
    user_transaksi = Transaksi.objects.filter(id__in=user_transaksi_ids)
    
    # Kinerja: Hitung agregasi langsung di database
    jurnal_total = Jurnal.objects.filter(akun__user=request.user).aggregate(
        total_debet=Coalesce(Sum('debit'), Value(0), output_field=DecimalField()),
        total_kredit=Coalesce(Sum('kredit'), Value(0), output_field=DecimalField()),
    )
    
    total_debet = jurnal_total.get('total_debet', 0)
    total_kredit = jurnal_total.get('total_kredit', 0)
    
    total_transaksi = user_transaksi.count()
    total_akun = user_akun.count()

    today = date.today()
    transaksi_hari_ini = user_transaksi.filter(tanggal=today).count()

    # Recent transactions: perbaikan efisiensi query
    recent_transactions = []
    latest_transaksi = user_transaksi.order_by('-tanggal', '-id')[:5]
    for transaksi in latest_transaksi:
        jurnal_entries = Jurnal.objects.select_related('akun').filter(transaksi=transaksi)
        debet_entry = jurnal_entries.filter(debit__gt=0).first()
        kredit_entry = jurnal_entries.filter(kredit__gt=0).first()
        
        jumlah = debet_entry.debit if debet_entry else (kredit_entry.kredit if kredit_entry else 0)

        recent_transactions.append({
            'tanggal': transaksi.tanggal,
            'deskripsi': transaksi.deskripsi,
            'akun_debet': debet_entry.akun if debet_entry else None,
            'akun_kredit': kredit_entry.akun if kredit_entry else None,
            'jumlah': jumlah
        })

    selisih = total_debet - total_kredit

    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)

    context = {
        'total_transaksi': total_transaksi,
        'total_debet': total_debet,
        'total_kredit': total_kredit,
        'total_akun': total_akun,
        'transaksi_hari_ini': transaksi_hari_ini,
        'recent_transactions': recent_transactions,
        'selisih': selisih,
        'is_balanced': total_debet == total_kredit,
        'user_profile': user_profile,
    }

    return render(request, 'dashboard.html', context)

# --- Input Transaksi View ---
@login_required
@transaction.atomic # Tambahkan transaction.atomic untuk integritas data
def input_transaksi(request):
    if request.method == 'POST':
        form = TransaksiForm(request.POST, user=request.user)
        if form.is_valid():
            akun_debet = form.cleaned_data['akun_debet']
            akun_kredit = form.cleaned_data['akun_kredit']
            jumlah = form.cleaned_data['jumlah']
            
            if akun_debet == akun_kredit:
                messages.error(request, 'Akun debet dan kredit tidak boleh sama!')
                return render(request, 'input_transaksi.html', {'form': form})
            
            # --- Simpan Transaksi dan Jurnal dalam blok atomic ---
            transaksi = Transaksi.objects.create(
                tanggal=form.cleaned_data['tanggal'], 
                deskripsi=form.cleaned_data['deskripsi'], 
                user=request.user # Pastikan user tersimpan di Transaksi
            )
            
            Jurnal.objects.create(
                transaksi=transaksi,
                akun=akun_debet,
                debit=jumlah,
                kredit=0
            )
            
            Jurnal.objects.create(
                transaksi=transaksi,
                akun=akun_kredit,
                debit=0,
                kredit=jumlah
            )
            
            messages.success(request, 'Transaksi berhasil disimpan!')
            return redirect('jurnal_umum')
        else:
            messages.error(request, 'Form tidak valid. Mohon periksa kembali input Anda.')
    else:
        form = TransaksiForm(user=request.user)
    return render(request, 'input_transaksi.html', {'form': form})

# --- Jurnal Umum View ---
@login_required
def jurnal_umum(request):
    # Filter Jurnal berdasarkan user yang login (lebih sederhana)
    jurnal = Jurnal.objects.select_related('transaksi', 'akun').filter(akun__user=request.user).order_by('-transaksi__tanggal', '-transaksi__id')
    
    # Agregasi untuk total (lebih efisien)
    totals = jurnal.aggregate(
        total_debet=Coalesce(Sum('debit'), Value(0), output_field=DecimalField()),
        total_kredit=Coalesce(Sum('kredit'), Value(0), output_field=DecimalField())
    )
    
    total_debet = totals.get('total_debet', 0)
    total_kredit = totals.get('total_kredit', 0)
    
    # Hitung total transaksi unik
    total_transaksi = jurnal.values('transaksi').distinct().count()
    
    context = {
        'jurnal': jurnal,
        'total_debet': total_debet,
        'total_kredit': total_kredit,
        'total_transaksi': total_transaksi,
    }
    
    return render(request, 'jurnal_umum.html', context)

@login_required
def jurnal_umum_pdf(request):
    """Export Jurnal Umum to PDF - Only user's data"""
    # Filter jurnal hanya untuk akun milik user yang login (diperbaiki)
    jurnal = Jurnal.objects.select_related('transaksi', 'akun').filter(akun__user=request.user).order_by('-transaksi__tanggal', '-transaksi__id')
    
    buffer = export_jurnal_pdf(jurnal)
    response = create_pdf_response('jurnal_umum.pdf')
    response.write(buffer.getvalue())
    
    return response

# --- Buku Besar View ---
@login_required
def buku_besar(request):
    akun_id = request.GET.get('akun_id')
    akun_list = Akun.objects.filter(user=request.user).order_by('kode')
    
    # Filter Jurnal harus sesuai user
    user_jurnal_base = Jurnal.objects.select_related('transaksi', 'akun').filter(akun__user=request.user)

    if akun_id:
        try:
            # Bug Fix: Pastikan akun milik user!
            akun_filter = Akun.objects.get(id=akun_id, user=request.user) 
            jurnal = user_jurnal_base.filter(akun=akun_filter).order_by('transaksi__tanggal')
        except Akun.DoesNotExist:
            messages.error(request, "Akun tidak ditemukan atau Anda tidak memiliki akses.")
            akun_filter = None
            jurnal = user_jurnal_base.none() 
    else:
        # Jika tidak ada filter akun, tampilkan semua jurnal user
        akun_filter = None
        jurnal = user_jurnal_base.order_by('akun__kode', 'transaksi__tanggal')
    
    context = {
        'jurnal': jurnal,
        'akun_list': akun_list,
        'akun_filter': akun_filter,
    }
    
    return render(request, 'buku_besar.html', context)

@login_required
def buku_besar_pdf(request):
    """Export Buku Besar to PDF"""
    akun_id = request.GET.get('akun_id')
    akun_name = "Semua Akun"
    
    # Filter Jurnal harus sesuai user
    user_jurnal_base = Jurnal.objects.select_related('transaksi', 'akun').filter(akun__user=request.user)

    if akun_id:
        try:
            # Bug Fix: Pastikan akun milik user!
            akun_filter = Akun.objects.get(id=akun_id, user=request.user)
            jurnal = user_jurnal_base.filter(akun=akun_filter).order_by('transaksi__tanggal')
            akun_name = f"{akun_filter.kode} - {akun_filter.nama}"
        except Akun.DoesNotExist:
            # Jika akun tidak ditemukan/bukan milik user, kembalikan response error
            return HttpResponseBadRequest("Akun tidak valid untuk PDF.")
    else:
        jurnal = user_jurnal_base.order_by('akun__kode', 'transaksi__tanggal')
    
    buffer = export_buku_besar_pdf(jurnal, akun_name)
    response = create_pdf_response('buku_besar.pdf')
    response.write(buffer.getvalue())
    
    return response

# --- Neraca Saldo View ---
# (Tidak diubah, karena compute_account_totals_for_user sudah memfilter per user)
@login_required
def neraca_saldo(request):
    data = compute_account_totals_for_user(request.user)

    neraca_data = []
    total_debet = 0
    total_kredit = 0

    for entry in data['saldo']:
        akun = entry['akun']
        debit = entry.get('debit', 0) or 0
        kredit = entry.get('kredit', 0) or 0
        
        # Display net amounts: if debit >= kredit show debit-net, else show credit-net
        if debit >= kredit:
            disp_debet = debit - kredit
            disp_kredit = 0
        else:
            disp_debet = 0
            disp_kredit = kredit - debit

        neraca_data.append({
            'akun__kode': akun.kode,
            'akun__nama': akun.nama,
            'total_debet': disp_debet,
            'total_kredit': disp_kredit,
        })

        total_debet += disp_debet
        total_kredit += disp_kredit

    context = {
        'neraca_data': neraca_data,
        'total_debet': total_debet,
        'total_kredit': total_kredit,
    }

    return render(request, 'neraca_saldo.html', context)

@login_required
def neraca_saldo_pdf(request):
    """Export Neraca Saldo to PDF"""
    data = compute_account_totals_for_user(request.user)
    neraca_data = []
    for entry in data['saldo']:
        akun = entry['akun']
        debit = entry.get('debit', 0) or 0
        kredit = entry.get('kredit', 0) or 0
        if debit >= kredit:
            disp_debet = debit - kredit
            disp_kredit = 0
        else:
            disp_debet = 0
            disp_kredit = kredit - debit
        neraca_data.append({
            'akun__kode': akun.kode,
            'akun__nama': akun.nama,
            'total_debet': disp_debet,
            'total_kredit': disp_kredit,
        })

    buffer = export_neraca_saldo_pdf(neraca_data)
    response = create_pdf_response('neraca_saldo.pdf')
    response.write(buffer.getvalue())
    
    return response

# --- Laporan Keuangan View ---
# (Tidak diubah, karena logic utama sudah benar)
@login_required
def laporan_keuangan(request):
    data = compute_account_totals_for_user(request.user)

    laporan = []
    aktiva = []
    kewajiban = []
    modal = []
    pendapatan = []
    beban = []

    for s in data['saldo']:
        akun = s['akun']
        saldo_akhir = s['saldo']
        laporan.append({'akun': akun, 'saldo': saldo_akhir})

        if akun.tipe in ['Aset', 'Aktiva', 'Aktiva Lancar', 'Aktiva Tetap']:
            aktiva.append({'akun': akun, 'saldo': abs(saldo_akhir) if saldo_akhir > 0 else 0})
        elif akun.tipe in ['Kewajiban', 'Kewajiban Lancar', 'Kewajiban Jangka Panjang']:
            kewajiban.append({'akun': akun, 'saldo': abs(saldo_akhir) if saldo_akhir < 0 else 0})
        elif akun.tipe == 'Modal':
            modal.append({'akun': akun, 'saldo': abs(saldo_akhir) if saldo_akhir < 0 else 0})
        elif akun.tipe == 'Pendapatan':
            pendapatan.append({'akun': akun, 'saldo': abs(saldo_akhir) if saldo_akhir < 0 else 0})
        elif akun.tipe == 'Beban':
            beban.append({'akun': akun, 'saldo': abs(saldo_akhir) if saldo_akhir > 0 else 0})

    total_aktiva = data['total_aktiva']
    total_kewajiban = data['total_kewajiban']
    total_modal = data['total_modal']
    total_pendapatan = data['total_pendapatan']
    total_beban = data['total_beban']

    laba_rugi = total_pendapatan - total_beban

    context = {
        'pendapatan': pendapatan,
        'beban': beban,
        'aktiva': aktiva,
        'pasiva': kewajiban,
        'modal': modal,
        'total_pendapatan': total_pendapatan,
        'total_beban': total_beban,
        'total_aktiva': total_aktiva,
        'total_pasiva': total_kewajiban,
        'total_modal': total_modal,
        'laba_rugi': laba_rugi,
    }

    return render(request, 'laporan_keuangan.html', context)

@login_required
def laporan_keuangan_pdf(request):
    """Export Laporan Keuangan to PDF"""
    data = compute_account_totals_for_user(request.user)

    pendapatan = []
    beban = []
    for entry in data['saldo']:
        akun = entry['akun']
        saldo_akhir = entry['saldo']
        if akun.tipe == 'Pendapatan':
            total = abs(saldo_akhir) if saldo_akhir < 0 else 0
            pendapatan.append({'akun__nama': akun.nama, 'total': total})
        elif akun.tipe == 'Beban':
            total = abs(saldo_akhir) if saldo_akhir > 0 else 0
            beban.append({'akun__nama': akun.nama, 'total': total})

    laporan_data = {'pendapatan': pendapatan, 'beban': beban}

    buffer = export_laporan_keuangan_pdf(laporan_data)
    response = create_pdf_response('laporan_keuangan.pdf')
    response.write(buffer.getvalue())
    
    return response

@login_required
def daftar_akun(request):
    """Menampilkan daftar semua akun"""
    akun_list = Akun.objects.filter(user=request.user).order_by('kode')
    context = {
        'akun_list': akun_list,
    }
    return render(request, 'daftar_akun.html', context)

# Ekspor PDF Daftar Akun
@login_required
def daftar_akun_pdf(request):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from io import BytesIO
    akun_list = Akun.objects.filter(user=request.user).order_by('kode')
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Daftar Akun Pengguna") # Lebih aman tanpa username untuk PDF umum
    y -= 30
    p.setFont("Helvetica", 10)
    p.drawString(50, y, "Kode")
    p.drawString(120, y, "Nama")
    p.drawString(350, y, "Tipe")
    y -= 20
    for akun in akun_list:
        p.drawString(50, y, str(akun.kode))
        p.drawString(120, y, akun.nama)
        p.drawString(350, y, akun.tipe)
        y -= 18
        if y < 50:
            p.showPage()
            y = height - 50
    p.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="daftar_akun.pdf"'
    return response

# Ekspor Excel Daftar Akun
@login_required
def daftar_akun_excel(request):
    from openpyxl import Workbook
    from io import BytesIO
    akun_list = Akun.objects.filter(user=request.user).order_by('kode')
    wb = Workbook()
    ws = wb.active
    ws.title = "Daftar Akun"
    ws.append(["Kode", "Nama", "Tipe"])
    for akun in akun_list:
        ws.append([akun.kode, akun.nama, akun.tipe])
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="daftar_akun.xlsx"'
    return response

@login_required
def tambah_akun(request):
    """Menambah akun baru"""
    if request.method == 'POST':
        form = AkunForm(request.POST)
        if form.is_valid():
            akun = form.save(commit=False)
            akun.user = request.user
            akun.save()
            messages.success(request, 'Akun berhasil ditambahkan!')
            return redirect('daftar_akun')
        else:
            messages.error(request, 'Form tidak valid. Mohon periksa kembali input Anda.')
    else:
        form = AkunForm()
    context = {
        'form': form,
        'title': 'Tambah Akun Baru'
    }
    return render(request, 'form_akun.html', context)

@login_required
def edit_akun(request, id):
    """Edit akun yang sudah ada"""
    # Pastikan akun milik user
    akun = get_object_or_404(Akun, id=id, user=request.user)
    
    if request.method == 'POST':
        form = AkunForm(request.POST, instance=akun)
        if form.is_valid():
            form.save()
            messages.success(request, 'Akun berhasil diperbarui!')
            return redirect('daftar_akun')
        else:
            messages.error(request, 'Form tidak valid. Mohon periksa kembali input Anda.')
    else:
        form = AkunForm(instance=akun)
    
    context = {
        'form': form,
        'title': 'Edit Akun',
        'akun': akun
    }
    return render(request, 'form_akun.html', context)

@login_required
@transaction.atomic # Tambahkan atomic untuk menjaga integritas data saat delete
def hapus_akun(request, id):
    """Hapus akun"""
    # Pastikan akun milik user
    akun = get_object_or_404(Akun, id=id, user=request.user)
    
    # Cek apakah akun sudah digunakan dalam transaksi
    jurnal_count = Jurnal.objects.filter(akun=akun).count()
    
    if jurnal_count > 0:
        messages.error(request, f'Akun "{akun.nama}" tidak dapat dihapus karena sudah digunakan dalam {jurnal_count} transaksi.')
        return redirect('daftar_akun')
    
    if request.method == 'POST':
        akun_nama = akun.nama
        akun.delete()
        messages.success(request, f'Akun "{akun_nama}" berhasil dihapus!')
        return redirect('daftar_akun')
    
    context = {
        'akun': akun,
        'jurnal_count': jurnal_count
    }
    return render(request, 'konfirmasi_hapus_akun_clean.html', context)


@login_required
def transaksi_api_list(request):
    """Return JSON list of transaksi (only for current user)."""
    if request.method != 'GET':
        return HttpResponseBadRequest('Method not allowed')

    # Filter Jurnal entries milik user
    jurnal_qs = Jurnal.objects.select_related('transaksi', 'akun').filter(akun__user=request.user).order_by('-transaksi__tanggal', '-transaksi__id')
    
    # Ambil ID transaksi unik
    transaksi_ids = jurnal_qs.values_list('transaksi__id', flat=True).distinct()
    transaksi_qs = Transaksi.objects.filter(id__in=transaksi_ids).order_by('-tanggal', '-id')

    data = []
    for t in transaksi_qs:
        jurnal_entries = jurnal_qs.filter(transaksi=t)
        debet = jurnal_entries.filter(debit__gt=0).first()
        kredit = jurnal_entries.filter(kredit__gt=0).first()
        
        # Perlu cek None sebelum mengakses debet.akun
        debet_data = {'id': debet.akun.id, 'nama': str(debet.akun)} if debet and debet.akun else None
        kredit_data = {'id': kredit.akun.id, 'nama': str(kredit.akun)} if kredit and kredit.akun else None
        
        jumlah = float(debet.debit) if debet else (float(kredit.kredit) if kredit else 0)

        data.append({
            'id': t.id,
            'tanggal': t.tanggal.isoformat(),
            'deskripsi': t.deskripsi,
            'akun_debet': debet_data,
            'akun_kredit': kredit_data,
            'jumlah': jumlah
        })

    return JsonResponse({'results': data})


@login_required
@transaction.atomic # Tambahkan atomic untuk CREATE via API
def transaksi_api_create(request):
    """Create transaksi + jurnal entries via AJAX (expects JSON body or form-encoded POST)."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Method not allowed')

    try:
        ct = (request.content_type or '')
        if ct.startswith('application/json'):
            payload = json.loads(request.body.decode('utf-8'))
        else:
            payload = request.POST

        tanggal = payload.get('tanggal')
        deskripsi = payload.get('deskripsi')
        akun_debet_val = payload.get('akun_debet')
        akun_kredit_val = payload.get('akun_kredit')
        jumlah = payload.get('jumlah')
        
        # Validasi angka dan tanggal
        jumlah = float(jumlah) if jumlah else 0
        parsed_tanggal = parse_date_flexible(tanggal)
    except Exception as e:
        return JsonResponse({'error': 'Invalid input or JSON format', 'detail': str(e)}, status=400)

    if not (parsed_tanggal and deskripsi and akun_debet_val and akun_kredit_val and jumlah > 0):
        return JsonResponse({'error': 'Missing or invalid fields (tanggal, deskripsi, akun, jumlah)'}, status=400)

    # Resolve akun ids: try int id first, fallback to lookup by kode or exact string
    def resolve_akun_local(val): 
        try:
            # Cari berdasarkan ID dan PASTIKAN milik user yang login
            akid = int(val)
            return get_object_or_404(Akun, id=akid, user=request.user)
        except Exception:
            # Coba cari berdasarkan kode atau nama
            ak = Akun.objects.filter(user=request.user).filter(Q(kode__iexact=val) | Q(nama__iexact=val)).first()
            if ak:
                return ak
            # Coba cari format '001 - Nama Akun'
            if ' - ' in str(val):
                parts = str(val).split(' - ')
                maybe_kode = parts[0].strip()
                ak = Akun.objects.filter(user=request.user, kode=maybe_kode).first()
                if ak:
                    return ak
        return None

    akun_debet = resolve_akun_local(akun_debet_val)
    akun_kredit = resolve_akun_local(akun_kredit_val)

    if not akun_debet or not akun_kredit:
        return JsonResponse({'error': 'Akun tidak ditemukan atau tidak dimiliki oleh pengguna'}, status=400)

    if akun_debet.id == akun_kredit.id:
        return JsonResponse({'error': 'Akun debet dan kredit tidak boleh sama'}, status=400)

    # --- Jurnal creation within atomic block ---
    transaksi = Transaksi.objects.create(tanggal=parsed_tanggal, deskripsi=deskripsi, user=request.user)
    Jurnal.objects.create(transaksi=transaksi, akun=akun_debet, debit=jumlah, kredit=0)
    Jurnal.objects.create(transaksi=transaksi, akun=akun_kredit, debit=0, kredit=jumlah)

    data = {
        'id': transaksi.id,
        'tanggal': transaksi.tanggal.isoformat(),
        'deskripsi': transaksi.deskripsi,
        'akun_debet': {'id': akun_debet.id, 'nama': str(akun_debet)},
        'akun_kredit': {'id': akun_kredit.id, 'nama': str(akun_kredit)},
        'jumlah': float(jumlah)
    }

    return JsonResponse({'created': data}, status=201)

# --- Transaksi API Update View ---
@login_required
@transaction.atomic # Tambahkan atomic untuk UPDATE via API
def transaksi_api_update(request, id):
    """Update transaksi and its jurnal entries."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Method not allowed')

    # Pastikan Transaksi milik user
    transaksi = get_object_or_404(Transaksi, id=id, user=request.user)

    try:
        ct = (request.content_type or '')
        if ct.startswith('application/json'):
            payload = json.loads(request.body.decode('utf-8'))
        else:
            payload = request.POST

        tanggal = payload.get('tanggal')
        deskripsi = payload.get('deskripsi')
        akun_debet_val = payload.get('akun_debet')
        akun_kredit_val = payload.get('akun_kredit')
        jumlah = payload.get('jumlah')
        
        jumlah = float(jumlah) if jumlah else 0
        parsed_tanggal = parse_date_flexible(tanggal)
    except Exception as e:
        return JsonResponse({'error': 'Invalid input or JSON format', 'detail': str(e)}, status=400)

    if not (parsed_tanggal and deskripsi and akun_debet_val and akun_kredit_val and jumlah > 0):
        return JsonResponse({'error': 'Missing or invalid fields'}, status=400)

    # Resolve akun values (id/kode/display)
    def resolve_akun_local(val):
        try:
            akid = int(val)
            return get_object_or_404(Akun, id=akid, user=request.user)
        except Exception:
            ak = Akun.objects.filter(user=request.user).filter(Q(kode__iexact=val) | Q(nama__iexact=val)).first()
            if ak:
                return ak
            if ' - ' in str(val):
                parts = str(val).split(' - ')
                maybe_kode = parts[0].strip()
                ak = Akun.objects.filter(user=request.user, kode=maybe_kode).first()
                if ak:
                    return ak
        return None

    akun_debet = resolve_akun_local(akun_debet_val)
    akun_kredit = resolve_akun_local(akun_kredit_val)

    if not akun_debet or not akun_kredit:
        return JsonResponse({'error': 'Akun not found or not owned by user'}, status=400)

    if akun_debet.id == akun_kredit.id:
        return JsonResponse({'error': 'Akun debet dan kredit tidak boleh sama'}, status=400)

    # --- Update Jurnal entries within atomic block ---
    Jurnal.objects.filter(transaksi=transaksi).delete() # Hapus entri lama
    
    transaksi.tanggal = parsed_tanggal
    transaksi.deskripsi = deskripsi
    transaksi.save()

    Jurnal.objects.create(transaksi=transaksi, akun=akun_debet, debit=jumlah, kredit=0)
    Jurnal.objects.create(transaksi=transaksi, akun=akun_kredit, debit=0, kredit=jumlah)

    return JsonResponse({'updated': {'id': transaksi.id}})


@login_required
def transaksi_api_delete(request, id):
    """Delete transaksi and its jurnal entries."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Method not allowed')

    # Pastikan Transaksi milik user
    transaksi = get_object_or_404(Transaksi, id=id, user=request.user)
    transaksi.delete()
    return JsonResponse({'deleted': True})

def logout_view(request):
    """Custom logout view that handles both GET and POST requests"""
    from django.contrib.auth import logout
    from django.contrib import messages
    
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'Anda telah berhasil logout.')
    
    return redirect('login')

def register_view(request):
    """View untuk registrasi user baru"""
    # Redirect ke dashboard jika user sudah login
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            
            # Auto login setelah registrasi
            login(request, user)
            messages.success(request, f'Selamat datang, {user.first_name}! Akun Anda berhasil dibuat dan Anda sudah login.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Registrasi gagal. Mohon periksa kembali input Anda.')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form
    }
    return render(request, 'registration/register.html', context)


@login_required
def profile_view(request):
    """View untuk menampilkan dan mengedit profil pengguna"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profil Anda berhasil diperbarui!')
            return redirect('profile')
        else:
            messages.error(request, 'Gagal memperbarui profil. Mohon periksa form Anda.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile
    }
    return render(request, 'profile.html', context)
