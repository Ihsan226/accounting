# PDF Export Implementation - Sistem Akuntansi

## Overview
This document describes the implementation of PDF export functionality across all features of the accounting system.

## Features Implemented

### 1. PDF Export Library
- **Library Used**: ReportLab
- **Installation**: `pip install reportlab`
- **Dependencies**: Pillow, charset-normalizer

### 2. PDF Utilities Module (`keuangan/pdf_utils.py`)
Contains reusable functions for PDF generation:
- `create_pdf_response()` - Creates HTTP response for PDF downloads
- `get_company_header()` - Company information for headers
- `create_header_style()` - Consistent styling for PDF headers
- `add_company_header()` - Adds company header to PDFs
- `create_table_style()` - Standard table styling
- `export_jurnal_pdf()` - Jurnal Umum PDF export
- `export_buku_besar_pdf()` - Buku Besar PDF export
- `export_neraca_saldo_pdf()` - Neraca Saldo PDF export
- `export_laporan_keuangan_pdf()` - Laporan Keuangan PDF export

### 3. PDF Export URLs
Added to `keuangan/urls.py`:
- `/jurnal/pdf/` - Export Jurnal Umum to PDF
- `/buku-besar/pdf/` - Export Buku Besar to PDF
- `/neraca-saldo/pdf/` - Export Neraca Saldo to PDF
- `/laporan-keuangan/pdf/` - Export Laporan Keuangan to PDF

### 4. View Functions
#### Main Views (`keuangan/views.py`)
- `jurnal_umum_pdf()` - Export jurnal umum with chronological transaction data

#### Report Views (`keuangan/views_laporan.py`)
- `buku_besar_pdf()` - Export buku besar with account-specific filtering
- `neraca_saldo_pdf()` - Export trial balance with account totals
- `laporan_keuangan_pdf()` - Export financial statements (Income Statement)

### 5. Template Updates
#### Jurnal Umum (`templates/jurnal_umum.html`)
- Added "Export PDF" button next to "Tambah Transaksi"
- Button opens PDF in new tab

#### Buku Besar (`templates/buku_besar.html`)
- Added "Export PDF" button with account filter support
- Maintains selected account filter in PDF export

#### Neraca Saldo (`templates/neraca_saldo.html`)
- Added "Export PDF" button alongside existing Excel and Print options
- Color-coded with danger (red) styling for consistency

#### Laporan Keuangan (`templates/laporan_keuangan.html`)
- Added "Export PDF" button for comprehensive financial reports
- Positioned before Excel and Print options

## PDF Features

### 1. Professional Layout
- Company header with logo space
- Professional typography using Helvetica fonts
- Consistent color scheme (dark blue headers, beige alternating rows)
- Proper margins and spacing

### 2. Data Presentation
- **Jurnal Umum**: Chronological transaction listing with debit/credit columns
- **Buku Besar**: Account-specific transactions with running balances
- **Neraca Saldo**: Trial balance with account codes and balances
- **Laporan Keuangan**: Income statement with revenue and expense categories

### 3. Formatting Features
- Currency formatting with thousand separators
- Date formatting (DD/MM/YYYY)
- Account code and name display
- Total calculations and summaries
- Professional table styling with headers

### 4. Export Options
- Direct download as PDF file
- Descriptive filenames (jurnal_umum.pdf, buku_besar.pdf, etc.)
- Opens in new browser tab
- Maintains data filters (e.g., account selection in Buku Besar)

## Technical Implementation

### 1. Data Processing
- Efficient database queries using Django ORM
- Proper joins and relationships
- Aggregation for totals and summaries
- Date and filter handling

### 2. PDF Generation
- Table-based layout for structured data
- Responsive column widths
- Automatic page breaks
- Header and footer consistency

### 3. Error Handling
- Graceful handling of empty data sets
- Proper HTTP responses
- Database query optimization

## Usage Instructions

### For Users:
1. Navigate to any report page (Jurnal Umum, Buku Besar, Neraca Saldo, Laporan Keuangan)
2. Apply any desired filters
3. Click the "Export PDF" button
4. PDF will open in new browser tab and download automatically

### For Developers:
1. PDF utilities are modular and reusable
2. Add new export functions by following existing patterns
3. Update templates to include export buttons
4. Register new PDF routes in urls.py

## File Structure
```
keuangan/
├── pdf_utils.py          # PDF generation utilities
├── views.py              # Main views with PDF exports
├── views_laporan.py      # Report views with PDF exports
├── urls.py               # URL patterns including PDF routes
└── templates/
    ├── jurnal_umum.html  # Updated with PDF export button
    ├── buku_besar.html   # Updated with PDF export button
    ├── neraca_saldo.html # Updated with PDF export button
    └── laporan_keuangan.html # Updated with PDF export button
```

## Benefits
1. **Professional Reports**: High-quality PDF output suitable for business use
2. **Easy Integration**: Seamlessly integrated into existing workflow
3. **Consistent Branding**: Company header and professional styling
4. **Filter Support**: Maintains user-selected filters in exports
5. **User-Friendly**: One-click export functionality
6. **Scalable**: Easy to extend for additional report types

## Future Enhancements
- Custom date range selection in PDFs
- Multi-page support for large datasets
- Company logo integration
- Additional export formats (Excel, CSV)
- Email integration for automatic report delivery
- Scheduled report generation
