from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.http import HttpResponse
from datetime import datetime
import io

def create_pdf_response(filename):
    """Create HTTP response for PDF download"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def get_company_header():
    """Get company header info"""
    return {
        'name': 'SISTEM AKUNTANSI',
        'address': 'Jalan Merpati No. 123, Jakarta',
        'phone': 'Tel: (021) 123-4567',
        'email': 'Email: info@akuntansi.com'
    }

def create_header_style():
    """Create header styles for PDF"""
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.darkblue,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    return title_style, subtitle_style, header_style

def add_company_header(story, title, subtitle=None):
    """Add company header to PDF"""
    title_style, subtitle_style, header_style = create_header_style()
    company = get_company_header()
    
    # Company info
    story.append(Paragraph(company['name'], title_style))
    story.append(Paragraph(company['address'], header_style))
    story.append(Paragraph(f"{company['phone']} | {company['email']}", header_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Report title
    story.append(Paragraph(title, title_style))
    if subtitle:
        story.append(Paragraph(subtitle, subtitle_style))
    story.append(Spacer(1, 0.3*inch))

def create_table_style():
    """Create standard table style"""
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])

def export_jurnal_pdf(jurnal_data):
    """Export jurnal umum to PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    story = []
    
    # Add header
    add_company_header(story, "JURNAL UMUM", f"Per tanggal: {datetime.now().strftime('%d/%m/%Y')}")
    
    # Create table data
    table_data = [['No', 'Tanggal', 'Deskripsi', 'Akun', 'Debet (Rp)', 'Kredit (Rp)']]
    
    no = 1
    total_debet = 0
    total_kredit = 0
    
    for jurnal in jurnal_data:
        table_data.append([
            str(no),
            jurnal.transaksi.tanggal.strftime('%d/%m/%Y'),
            jurnal.transaksi.deskripsi,
            f"{jurnal.akun.kode} - {jurnal.akun.nama}",
            f"{jurnal.debit:,.2f}" if jurnal.debit > 0 else "-",
            f"{jurnal.kredit:,.2f}" if jurnal.kredit > 0 else "-"
        ])
        total_debet += jurnal.debit
        total_kredit += jurnal.kredit
        no += 1
    
    # Add totals
    table_data.append(['', '', '', 'TOTAL', f"{total_debet:,.2f}", f"{total_kredit:,.2f}"])
    
    # Create table
    table = Table(table_data, colWidths=[0.5*inch, 1*inch, 2*inch, 2*inch, 1.2*inch, 1.2*inch])
    table.setStyle(create_table_style())
    
    # Add total row styling
    table.setStyle(TableStyle([
        ('BACKGROUND', (-3, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (-3, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    story.append(table)
    
    # Add footer
    styles = getSampleStyleSheet()
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_RIGHT,
        topPadding=20
    )
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Dicetak pada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def export_buku_besar_pdf(buku_besar_data, akun_name="Semua Akun"):
    """Export buku besar to PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    story = []
    
    # Add header
    add_company_header(story, "BUKU BESAR", f"Akun: {akun_name} | Per tanggal: {datetime.now().strftime('%d/%m/%Y')}")
    
    # Create table data
    table_data = [['No', 'Tanggal', 'Deskripsi', 'Debet (Rp)', 'Kredit (Rp)', 'Saldo (Rp)']]
    
    no = 1
    saldo = 0
    
    for jurnal in buku_besar_data:
        saldo += jurnal.debit - jurnal.kredit
        table_data.append([
            str(no),
            jurnal.transaksi.tanggal.strftime('%d/%m/%Y'),
            jurnal.transaksi.deskripsi,
            f"{jurnal.debit:,.2f}" if jurnal.debit > 0 else "-",
            f"{jurnal.kredit:,.2f}" if jurnal.kredit > 0 else "-",
            f"{saldo:,.2f}"
        ])
        no += 1
    
    # Create table
    table = Table(table_data, colWidths=[0.5*inch, 1*inch, 2.5*inch, 1.2*inch, 1.2*inch, 1.2*inch])
    table.setStyle(create_table_style())
    
    story.append(table)
    
    # Add footer
    styles = getSampleStyleSheet()
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_RIGHT,
        topPadding=20
    )
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Dicetak pada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def export_neraca_saldo_pdf(neraca_data):
    """Export neraca saldo to PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    story = []
    
    # Add header
    add_company_header(story, "NERACA SALDO", f"Per tanggal: {datetime.now().strftime('%d/%m/%Y')}")
    
    # Create table data
    table_data = [['No', 'Kode Akun', 'Nama Akun', 'Debet (Rp)', 'Kredit (Rp)']]
    
    no = 1
    total_debet = 0
    total_kredit = 0
    
    for item in neraca_data:
        debet = item['total_debet'] if item['total_debet'] > item['total_kredit'] else 0
        kredit = item['total_kredit'] if item['total_kredit'] > item['total_debet'] else 0
        
        table_data.append([
            str(no),
            item['akun__kode'],
            item['akun__nama'],
            f"{debet:,.2f}" if debet > 0 else "-",
            f"{kredit:,.2f}" if kredit > 0 else "-"
        ])
        total_debet += debet
        total_kredit += kredit
        no += 1
    
    # Add totals
    table_data.append(['', '', 'TOTAL', f"{total_debet:,.2f}", f"{total_kredit:,.2f}"])
    
    # Create table
    table = Table(table_data, colWidths=[0.5*inch, 1*inch, 3*inch, 1.5*inch, 1.5*inch])
    table.setStyle(create_table_style())
    
    # Add total row styling
    table.setStyle(TableStyle([
        ('BACKGROUND', (-2, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    story.append(table)
    
    # Add footer
    styles = getSampleStyleSheet()
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_RIGHT,
        topPadding=20
    )
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Dicetak pada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def export_laporan_keuangan_pdf(laporan_data):
    """Export laporan keuangan lengkap: Neraca, Laba Rugi, Arus Kas, Analisis"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    story = []
    
    # Add header
    add_company_header(story, "LAPORAN KEUANGAN", f"Per tanggal: {datetime.now().strftime('%d/%m/%Y')}")
    
    styles = getSampleStyleSheet()
    
    # Neraca (Balance Sheet)
    story.append(Paragraph("NERACA", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    bs_left = [['Aktiva', 'Jumlah (Rp)']]
    for item in laporan_data.get('aktiva', []):
        bs_left.append([item['akun__nama'], f"{item['saldo']:,.2f}"])
    bs_left.append(['Total Aktiva', f"{laporan_data.get('total_aktiva', 0):,.2f}"])

    bs_right = [['Kewajiban & Modal', 'Jumlah (Rp)']]
    for item in laporan_data.get('kewajiban', []):
        bs_right.append([item['akun__nama'], f"{item['saldo']:,.2f}"])
    for item in laporan_data.get('modal', []):
        bs_right.append([item['akun__nama'], f"{item['saldo']:,.2f}"])
    bs_right.append(['Total Kewajiban + Modal', f"{laporan_data.get('equation_right', 0):,.2f}"])

    t_left = Table(bs_left, colWidths=[3.5*inch, 1.5*inch])
    t_right = Table(bs_right, colWidths=[3.5*inch, 1.5*inch])
    t_left.setStyle(create_table_style())
    t_right.setStyle(create_table_style())
    story.append(t_left)
    story.append(Spacer(1, 0.1*inch))
    story.append(t_right)
    story.append(Spacer(1, 0.2*inch))

    # Laporan Laba Rugi
    story.append(Paragraph("LAPORAN LABA RUGI", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    pendapatan_data = [['Pendapatan', 'Jumlah (Rp)']]
    total_pendapatan = 0
    
    for item in laporan_data['pendapatan']:
        pendapatan_data.append([item['akun__nama'], f"{item['total']:,.2f}"])
        total_pendapatan += item['total']
    
    pendapatan_data.append(['Total Pendapatan', f"{total_pendapatan:,.2f}"])
    
    pendapatan_table = Table(pendapatan_data, colWidths=[4*inch, 2*inch])
    pendapatan_table.setStyle(create_table_style())
    story.append(pendapatan_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Beban
    beban_data = [['Beban', 'Jumlah (Rp)']]
    total_beban = 0
    
    for item in laporan_data['beban']:
        beban_data.append([item['akun__nama'], f"{item['total']:,.2f}"])
        total_beban += item['total']
    
    beban_data.append(['Total Beban', f"{total_beban:,.2f}"])
    
    beban_table = Table(beban_data, colWidths=[4*inch, 2*inch])
    beban_table.setStyle(create_table_style())
    story.append(beban_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Laba/Rugi
    laba_rugi = total_pendapatan - total_beban
    laba_rugi_data = [['Laba/Rugi Bersih', f"{laba_rugi:,.2f}"]]
    laba_rugi_table = Table(laba_rugi_data, colWidths=[4*inch, 2*inch])
    laba_rugi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.yellow),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(laba_rugi_table)
    story.append(Spacer(1, 0.2*inch))

    # Arus Kas (Cash Flow)
    story.append(Paragraph("LAPORAN ARUS KAS", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    ak_operasional = [["Kas Masuk Operasional", f"{laporan_data.get('kas_masuk_operasional', 0):,.2f}"],
                      ["Kas Keluar Operasional", f"{laporan_data.get('kas_keluar_operasional', 0):,.2f}"],
                      ["Kas Bersih Operasional", f"{laporan_data.get('kas_bersih_operasional', 0):,.2f}"]]
    ak_investasi = [["Kas Masuk Investasi", f"{laporan_data.get('kas_masuk_investasi', 0):,.2f}"],
                    ["Kas Keluar Investasi", f"{laporan_data.get('kas_keluar_investasi', 0):,.2f}"],
                    ["Kas Bersih Investasi", f"{laporan_data.get('kas_bersih_investasi', 0):,.2f}"]]
    ak_pendanaan = [["Kas Masuk Pendanaan", f"{laporan_data.get('kas_masuk_pendanaan', 0):,.2f}"],
                    ["Kas Keluar Pendanaan", f"{laporan_data.get('kas_keluar_pendanaan', 0):,.2f}"],
                    ["Kas Bersih Pendanaan", f"{laporan_data.get('kas_bersih_pendanaan', 0):,.2f}"]]
    ak_total = [["Total Kenaikan/ Penurunan Kas", f"{laporan_data.get('total_kas_bersih', 0):,.2f}"]]

    for section in (ak_operasional, ak_investasi, ak_pendanaan, ak_total):
        t = Table(section, colWidths=[4*inch, 2*inch])
        t.setStyle(create_table_style())
        story.append(t)
        story.append(Spacer(1, 0.1*inch))

    # Analisis (Ratios)
    story.append(Paragraph("ANALISIS", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    analysis = [["Profit Margin (%)", f"{laporan_data.get('profit_margin', 0):,.2f}"],
                ["Current Ratio", f"{laporan_data.get('current_ratio', 0) if laporan_data.get('current_ratio') is not None else '-'}"]]
    t_analysis = Table(analysis, colWidths=[4*inch, 2*inch])
    t_analysis.setStyle(create_table_style())
    story.append(t_analysis)
    
    # Add footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_RIGHT,
        topPadding=20
    )
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Dicetak pada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer
