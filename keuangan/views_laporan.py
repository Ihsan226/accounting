from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Jurnal, Akun
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from .pdf_utils import (
    export_buku_besar_pdf, 
    export_neraca_saldo_pdf, 
    export_laporan_keuangan_pdf,
    create_pdf_response
)


# Shared helper to compute balances and totals by account type for a user
def compute_account_totals_for_user(user):
    akun_list = Akun.objects.filter(user=user)
    saldo = []
    total_debit = 0
    total_kredit = 0

    # Totals by account type
    total_aktiva = 0
    total_kewajiban = 0
    total_modal = 0
    total_pendapatan = 0
    total_beban = 0

    # Define account type groups and their normal balances
    asset_types = ['Aset', 'Aktiva', 'Aktiva Lancar', 'Aktiva Tetap', 'Aktiva Lainnya']
    liability_types = ['Kewajiban', 'Kewajiban Lancar', 'Kewajiban Jangka Panjang']

    for akun in akun_list:
        debit_sum = Jurnal.objects.filter(akun=akun).aggregate(total_debit=Coalesce(Sum('debit'), Value(0, output_field=DecimalField())))['total_debit']
        kredit_sum = Jurnal.objects.filter(akun=akun).aggregate(total_kredit=Coalesce(Sum('kredit'), Value(0, output_field=DecimalField())))['total_kredit']
        saldo_akhir = debit_sum - kredit_sum

        saldo.append({
            'akun': akun,
            'debit': debit_sum,
            'kredit': kredit_sum,
            'saldo': saldo_akhir,
        })

        total_debit += debit_sum
        total_kredit += kredit_sum

        # Determine normal side by account type
        if akun.tipe in asset_types or akun.tipe == 'Beban':
            normal = 'debit'
        else:
            # treat Kewajiban, Modal, Pendapatan as credit-normal
            normal = 'credit'

        # Route balances to correct totals respecting normal balance
        # If account has a debit-normal balance (debit_sum - kredit_sum >= 0)
        if normal == 'debit':
            if saldo_akhir >= 0:
                # debit balance -> goes to left side (aktiva or beban)
                if akun.tipe in asset_types:
                    total_aktiva += saldo_akhir
                elif akun.tipe == 'Beban':
                    total_beban += saldo_akhir
                else:
                    # default to aktiva if unknown
                    total_aktiva += saldo_akhir
            else:
                # credit balance on a debit-normal account -> count on right side
                if akun.tipe in asset_types:
                    total_kewajiban += abs(saldo_akhir)
                elif akun.tipe == 'Beban':
                    total_pendapatan += abs(saldo_akhir)
                else:
                    total_kewajiban += abs(saldo_akhir)
        else:
            # credit-normal accounts
            if saldo_akhir <= 0:
                val = abs(saldo_akhir)
                if akun.tipe in liability_types:
                    total_kewajiban += val
                elif akun.tipe == 'Modal':
                    total_modal += val
                elif akun.tipe == 'Pendapatan':
                    total_pendapatan += val
                else:
                    total_kewajiban += val
            else:
                # unexpected debit balance on credit-normal account -> treat as aktiva
                total_aktiva += saldo_akhir

    return {
        'saldo': saldo,
        'total_debit': total_debit,
        'total_kredit': total_kredit,
        'total_aktiva': total_aktiva,
        'total_kewajiban': total_kewajiban,
        'total_modal': total_modal,
        'total_pendapatan': total_pendapatan,
        'total_beban': total_beban,
    }

@login_required
def buku_besar(request):
    # Filter akun berdasarkan user yang login
    akun_list = Akun.objects.filter(user=request.user)
    data = []
    grand_total_debit = 0
    grand_total_kredit = 0
    
    for akun in akun_list:
        # Filter jurnal hanya untuk akun milik user yang login
        jurnal = Jurnal.objects.filter(akun=akun)
        total_debit = jurnal.aggregate(total_debit=Coalesce(Sum('debit'), Value(0, output_field=DecimalField())))['total_debit']
        total_kredit = jurnal.aggregate(total_kredit=Coalesce(Sum('kredit'), Value(0, output_field=DecimalField())))['total_kredit']

        data.append({
            'akun': akun,
            'jurnal': jurnal,
            'total_debit': total_debit,
            'total_kredit': total_kredit,
        })
        
        grand_total_debit += total_debit
        grand_total_kredit += total_kredit
    
    context = {
        'data': data,
        'all_akun': akun_list,
        'grand_total_debit': grand_total_debit,
        'grand_total_kredit': grand_total_kredit,
    }
    
    return render(request, 'buku_besar.html', context)

@login_required
def neraca_saldo(request):
    # Use the shared helper so presentation logic is consistent across reports
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

    # Compose context using canonical totals from the helper
    context = {
        'saldo': data['saldo'],
        'neraca_data': neraca_data,
        'total_debit': data.get('total_debit', 0),
        'total_kredit': data.get('total_kredit', 0),
        'total_aktiva': data.get('total_aktiva', 0),
        'total_kewajiban': data.get('total_kewajiban', 0),
        'total_modal': data.get('total_modal', 0),
        'total_pendapatan': data.get('total_pendapatan', 0),
        'total_beban': data.get('total_beban', 0),
        'laba_rugi': (data.get('total_pendapatan', 0) - data.get('total_beban', 0)),
        'rhs_total': (data.get('total_kewajiban', 0) + data.get('total_modal', 0) + (data.get('total_pendapatan', 0) - data.get('total_beban', 0)))
    }

    return render(request, 'neraca_saldo.html', context)

@login_required
def laporan_keuangan(request):
    # Delegate to the canonical helper so totals/signs are consistent with neraca
    data = compute_account_totals_for_user(request.user)

    pendapatan = []
    beban = []
    laporan = []
    aktiva = []
    kewajiban = []
    modal = []

    for entry in data['saldo']:
        akun = entry['akun']
        saldo_akhir = entry['saldo']
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

    total_aktiva = data.get('total_aktiva', 0)
    total_kewajiban = data.get('total_kewajiban', 0)
    total_modal = data.get('total_modal', 0)
    total_pendapatan = data.get('total_pendapatan', 0)
    total_beban = data.get('total_beban', 0)

    # Net income (laba/rugi bersih)
    net_income = total_pendapatan - total_beban

    # Add Retained Earnings / Current Year Earnings into Modal display section
    if net_income != 0:
        modal.append({'akun': Akun(nama='Laba Tahun Berjalan', tipe='Modal'), 'saldo': abs(net_income) if net_income < 0 else net_income})

    # Modal akhir (untuk tampilan): Modal Awal + Laba Bersih
    total_modal_display = total_modal + net_income

    # Accounting equation right side uses Modal Akhir
    equation_right = total_kewajiban + total_modal_display

    # Simple cash flow reconstruction (placeholder logic)
    kas_masuk_operasional = total_pendapatan
    kas_keluar_operasional = total_beban
    kas_bersih_operasional = kas_masuk_operasional - kas_keluar_operasional
    kas_masuk_investasi = 0
    kas_keluar_investasi = 0
    kas_bersih_investasi = kas_masuk_investasi - kas_keluar_investasi
    kas_masuk_pendanaan = total_modal  # treat modal additions as financing inflow
    kas_keluar_pendanaan = 0
    kas_bersih_pendanaan = kas_masuk_pendanaan - kas_keluar_pendanaan
    total_kas_bersih = kas_bersih_operasional + kas_bersih_investasi + kas_bersih_pendanaan
    kas_awal = 0
    kas_akhir = total_aktiva  # Assuming all aktiva currently represented in kas for this simplified model

    # Ratios
    profit_margin = (net_income / total_pendapatan * 100) if total_pendapatan else 0
    current_ratio = (total_aktiva / total_kewajiban) if total_kewajiban else None

    context = {
        'laporan': laporan,
        'aktiva': aktiva,
        'kewajiban': kewajiban,
        'modal': modal,
        'pendapatan': pendapatan,
        'beban': beban,
        'total_aktiva': total_aktiva,
        'total_kewajiban': total_kewajiban,
        'total_modal': total_modal,
        'total_modal_display': total_modal_display,
        'total_pendapatan': total_pendapatan,
        'total_beban': total_beban,
        'net_income': net_income,
        'equation_right': equation_right,
        'kas_masuk_operasional': kas_masuk_operasional,
        'kas_keluar_operasional': kas_keluar_operasional,
        'kas_bersih_operasional': kas_bersih_operasional,
        'kas_masuk_investasi': kas_masuk_investasi,
        'kas_keluar_investasi': kas_keluar_investasi,
        'kas_bersih_investasi': kas_bersih_investasi,
        'kas_masuk_pendanaan': kas_masuk_pendanaan,
        'kas_keluar_pendanaan': kas_keluar_pendanaan,
        'kas_bersih_pendanaan': kas_bersih_pendanaan,
        'total_kas_bersih': total_kas_bersih,
        'kas_awal': kas_awal,
        'kas_akhir': kas_akhir,
        'profit_margin': profit_margin,
        'current_ratio': current_ratio,
    }

    return render(request, 'laporan_keuangan.html', context)

@login_required
def buku_besar_pdf(request):
    """Export Buku Besar to PDF - Only user's data"""
    akun_id = request.GET.get('akun_id')
    akun_name = "Semua Akun"
    
    if akun_id:
        # Filter akun berdasarkan user dan ID
        akun_filter = Akun.objects.get(id=akun_id, user=request.user)
        jurnal = Jurnal.objects.select_related('transaksi', 'akun').filter(akun=akun_filter).order_by('transaksi__tanggal')
        akun_name = f"{akun_filter.kode} - {akun_filter.nama}"
    else:
        # Filter semua jurnal hanya untuk akun milik user yang login
        user_akun_ids = Akun.objects.filter(user=request.user).values_list('id', flat=True)
        jurnal = Jurnal.objects.select_related('transaksi', 'akun').filter(akun__in=user_akun_ids).order_by('akun__kode', 'transaksi__tanggal')
    
    buffer = export_buku_besar_pdf(jurnal, akun_name)
    response = create_pdf_response('buku_besar.pdf')
    response.write(buffer.getvalue())
    
    return response

@login_required
def neraca_saldo_pdf(request):
    """Export Neraca Saldo to PDF - Only user's data"""
    # Build neraca data using shared helper so saldo-normal logic matches other reports
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


@login_required
def laporan_keuangan_pdf(request):
    """Export Laporan Keuangan to PDF - Only user's data"""
    data = compute_account_totals_for_user(request.user)

    pendapatan = []
    beban = []

    # Build data in the shape expected by export_laporan_keuangan_pdf
    for entry in data['saldo']:
        akun = entry['akun']
        saldo_akhir = entry['saldo']
        if akun.tipe == 'Pendapatan':
            total = abs(saldo_akhir) if saldo_akhir < 0 else 0
            pendapatan.append({'akun__nama': akun.nama, 'total': total})
        elif akun.tipe == 'Beban':
            total = abs(saldo_akhir) if saldo_akhir > 0 else 0
            beban.append({'akun__nama': akun.nama, 'total': total})

    laporan_data = {
        'pendapatan': pendapatan,
        'beban': beban,
    }

    buffer = export_laporan_keuangan_pdf(laporan_data)
    response = create_pdf_response('laporan_keuangan.pdf')
    response.write(buffer.getvalue())

    return response
