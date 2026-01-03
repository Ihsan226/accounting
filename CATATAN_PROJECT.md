# CATATAN PROJECT — Sistem Akuntansi (Django)

> Catatan ini dibuat dari pemindaian file inti project (konfigurasi Django, app `keuangan`, template utama, util export, serta dokumen ringkasan yang ada di root). Jika Anda ingin catatan *100% exhaustif* hingga file terkecil (mis. semua CSS/JS panjang di template), bilang saja—nanti saya lanjutkan pemetaan lebih detail.

## 1) Gambaran Umum
Project ini adalah aplikasi **Sistem Akuntansi berbasis Django** (multi-user) dengan fitur utama:
- Autentikasi: login, register, logout
- Manajemen **Akun/Chart of Accounts** per user
- Input **Transaksi** (double-entry) → otomatis membuat entri **Jurnal** debet/kredit
- Laporan: **Jurnal Umum**, **Buku Besar**, **Neraca Saldo**, **Laporan Keuangan**
- Export laporan/daftar akun: **PDF** (ReportLab) dan **Excel** (openpyxl)
- Profil pengguna (`UserProfile`) dengan foto & bio

Karakteristik penting:
- **Data isolation per user**: setiap user hanya bisa melihat data mereka sendiri (akun, transaksi, jurnal, laporan, export).
- Database memakai **SQLite** (`db.sqlite3`).


## 2) Teknologi & Dependensi
- Python + Django
- Database: SQLite
- Frontend: Bootstrap 5 + Bootstrap Icons (CDN)
- PDF: ReportLab (`reportlab`)
- Excel: `openpyxl`

Catatan:
- `requirements.txt` saat ini mencatat paket inti seperti Django/reportlab/pillow, tetapi **belum mencantumkan `openpyxl`**, padahal dipakai di beberapa view export Excel.


## 3) Struktur Folder Penting
- `akutansi_project/`
  - `settings.py` konfigurasi Django
  - `urls.py` routing root (include `keuangan.urls`)
- `keuangan/` (app utama)
  - `models.py` (Akun, Transaksi, Jurnal, UserProfile)
  - `forms.py` (TransaksiForm, AkunForm, CustomUserCreationForm, UserProfileForm, UserUpdateForm)
  - `views.py` (dashboard, transaksi, akun, auth, API transaksi)
  - `views_laporan.py` (laporan + export Excel/PDF untuk laporan)
  - `pdf_utils.py` (helper PDF ReportLab)
  - `context_processors.py` (inject `user_profile` ke template)
  - `migrations/` (riwayat perubahan skema)
- `templates/` (template HTML)
  - `base.html` layout utama + theme logic
  - Halaman akuntansi: `dashboard.html`, `input_transaksi.html`, `jurnal_umum.html`, `buku_besar.html`, `neraca_saldo.html`, `laporan_keuangan.html`
  - Akun: `daftar_akun.html`, `form_akun.html`, `detail_akun.html`, `konfirmasi_hapus_akun*.html`
  - Auth: `templates/registration/login.html`, `templates/registration/register.html`
- `media/` (upload foto profil)
- Script util di root: `setup_user_data.py`, `create_test_users.py`, `create_test_data_ihsan.py`, `create_sample_transactions.py`, dll.


## 4) Konfigurasi Aplikasi (Django)
Sumber: `akutansi_project/settings.py`
- `INSTALLED_APPS` mencakup `keuangan` dan `django.contrib.humanize`.
- Template memakai `DIRS: [BASE_DIR / 'templates']` dan `APP_DIRS=True`.
- Context processor tambahan: `keuangan.context_processors.user_profile_context`.
- Login config:
  - `LOGIN_URL = '/login/'`
  - `LOGIN_REDIRECT_URL = '/'`
  - `LOGOUT_REDIRECT_URL = '/login/'`
- Media:
  - `MEDIA_URL = '/media/'`
  - `MEDIA_ROOT = BASE_DIR/media`

Routing root: `akutansi_project/urls.py`
- `/admin/`
- `/` include semua route `keuangan.urls`
- Static media di mode `DEBUG=True`.


## 5) Model Data (Skema Inti)
Sumber: `keuangan/models.py`

### 5.1 `Akun`
- Field: `user (FK)`, `nama`, `kode`, `tipe`
- Constraint: `unique_together = ('user', 'kode')` → kode akun unik per user.

### 5.2 `Transaksi`
- Field: `tanggal`, `deskripsi`, `user (FK)`

### 5.3 `Jurnal`
- Field: `transaksi (FK)`, `akun (FK)`, `debit`, `kredit`
- Implementasi double-entry: 1 transaksi biasanya menghasilkan 2 baris jurnal (1 debet, 1 kredit).

### 5.4 `UserProfile`
- Field: `user (OneToOne)`, `profile_picture`, `bio`, timestamps


## 6) Routing & Halaman
Sumber: `keuangan/urls.py`

### Halaman utama
- `/` → dashboard
- `/input/` → input transaksi + tabel transaksi inline (AJAX)
- `/jurnal/` (+ `/pdf/`, `/excel/`)
- `/buku-besar/` (+ `/pdf/`, `/excel/`)
- `/neraca-saldo/` (+ `/pdf/`, `/excel/`)
- `/laporan-keuangan/` (+ `/pdf/`, `/excel/`)

### Manajemen akun
- `/akun/` daftar akun
- `/akun/tambah/`, `/akun/edit/<id>/`, `/akun/detail/<id>/`, `/akun/hapus/<id>/`
- Export: `/akun/pdf/`, `/akun/excel/`

### Autentikasi
- `/login/` (CustomLoginView)
- `/register/` (register_view)
- `/logout/` (logout_view)

### Profil
- `/profile/`

### API transaksi (dipakai oleh halaman input transaksi)
- `/transaksi/api/list/`
- `/transaksi/api/create/`
- `/transaksi/api/<id>/update/`
- `/transaksi/api/<id>/delete/`


## 7) Alur Bisnis Utama

### 7.1 Input transaksi (double-entry)
Sumber: `keuangan/views.py` + `keuangan/forms.py`
- User mengisi: tanggal, deskripsi, akun debet, akun kredit, jumlah.
- Validasi penting: **akun debet != akun kredit**.
- Sistem membuat:
  1) `Transaksi(user=request.user)`
  2) `Jurnal` debet untuk akun debet
  3) `Jurnal` kredit untuk akun kredit

### 7.2 Laporan
Sumber: `keuangan/views.py` dan `keuangan/views_laporan.py`
- Basis data laporan: `Jurnal` yang terkait akun milik user.
- Neraca saldo & laporan keuangan memakai helper `compute_account_totals_for_user(user)` untuk konsistensi.
- Kategori akun ditentukan dari `Akun.tipe` (ada beberapa variasi string seperti `Aset/Aktiva/Aktiva Lancar/...`).


## 8) Isolasi Data Per User (Multi-tenant)
Dokumen: `DATABASE_ISOLATION_COMPLETE.md`, `DATA_ISOLATION_FINAL.md`, `DASHBOARD_FIX_SUMMARY.md`

Prinsip yang dipakai:
- Semua query `Akun` difilter: `Akun.objects.filter(user=request.user)`.
- Semua query `Jurnal` difilter: `Jurnal.objects.filter(akun__user=request.user)`.
- `Transaksi` dipilih berdasarkan jurnal yang memakai akun user.

Hasil yang ditargetkan:
- User A tidak bisa melihat akun/transaksi/jurnal user B.
- Export PDF/Excel hanya memuat data milik user yang login.


## 9) Export PDF & Excel

### 9.1 PDF (ReportLab)
Sumber: `keuangan/pdf_utils.py` + pemanggil di views
- PDF dibuat dengan Table (ReportLab Platypus) + header.
- Export tersedia untuk jurnal, buku besar, neraca saldo, laporan keuangan, dan daftar akun.

### 9.2 Excel (openpyxl)
Sumber: `keuangan/views.py` dan `keuangan/views_laporan.py`
- Jurnal Umum → export dengan styling header dan total.
- Buku Besar / Neraca Saldo / Laporan Keuangan → export per user, beberapa sheet untuk laporan keuangan.
- Daftar akun memiliki fallback CSV bila openpyxl gagal.


## 10) Template & UI
- `templates/base.html` berisi layout utama + navbar/sidebar + sistem tema otomatis (light/dark berdasarkan jam dan localStorage).
- `dashboard.html` menampilkan kartu statistik (total transaksi/debet/kredit/akun), ringkasan, dan tombol aksi cepat.
- `input_transaksi.html` punya:
  - Form transaksi (toggle)
  - Tabel transaksi inline yang diisi lewat JavaScript (memakai endpoint API transaksi)
  - Toolbar filter (search + date range)


## 11) Script Util / Seeder Data
File di root yang membantu menyiapkan demo/testing:
- `create_test_users.py`: membuat `testuser1/testuser2` + akun contoh.
- `setup_user_data.py`: mengisi akun spesifik untuk user `iraa` & `ihsan` (menghapus akun lama lalu recreate).
- `create_test_data_ihsan.py`: membuat transaksi+jurnal untuk user `ihsan` agar laporan terlihat realistis.
- `create_sample_transactions.py`: membuat transaksi sample (cenderung untuk admin) dan menghapus semua data transaksi/jurnal global.
- `start_server.bat`: menjalankan server memakai python dari virtualenv `env/`.

Catatan kehati-hatian:
- `create_sample_transactions.py` melakukan `Jurnal.objects.all().delete()` dan `Transaksi.objects.all().delete()` (global), jadi jangan dijalankan kalau ingin mempertahankan data.


## 12) Cara Menjalankan (Windows)
Opsi 1: pakai batch
1) Jalankan `start_server.bat`
2) Buka `http://127.0.0.1:8000/`

Opsi 2: manual (virtualenv)
1) Aktifkan env (jika perlu): `env\Scripts\activate`
2) Jalankan: `env\Scripts\python.exe manage.py migrate`
3) Jalankan: `env\Scripts\python.exe manage.py runserver`


## 13) Catatan Teknis / Risiko
- `DEBUG=True` dan `SECRET_KEY` tersimpan di repo → aman untuk lokal, **jangan untuk production**.
- `ALLOWED_HOSTS=[]` → perlu diatur saat deploy.
- `requirements.txt` tidak mencantumkan `openpyxl`, padahal fitur export Excel memerlukannya.
- String `Akun.tipe` bervariasi (`Aset`, `Aktiva`, dll). Pastikan konsisten saat menambah akun baru agar laporan mengelompokkan dengan benar.


## 14) Referensi Dokumen Internal
- `DATABASE_ISOLATION_COMPLETE.md` / `DATA_ISOLATION_FINAL.md`: ringkasan isolasi data
- `PDF_EXPORT_IMPLEMENTATION.md`: ringkasan fitur export PDF
- `LOGOUT_FIX_SUMMARY.md`: perbaikan logout GET/POST
- `PERBAIKAN_SUMMARY.md`: ringkasan export daftar akun + isolasi data
- `TAMPILAN_HAPUS_REDESIGN.md`: redesign UI konfirmasi hapus akun


---

Jika Anda mau, saya bisa lanjutkan dengan membuat **peta alur request → view → template** per halaman (dengan diagram sederhana) atau membuat **checklist deployment** (production settings, security, requirements lengkap).
