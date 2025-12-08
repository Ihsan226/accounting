# Panduan Pembuatan Website Akuntansi dengan Django

## 1. Instalasi Python & Visual Studio Code
- Download dan install Python dari https://www.python.org/downloads/
- Download dan install Visual Studio Code dari https://code.visualstudio.com/

## 2. Instalasi Ekstensi VS Code
- Buka VS Code, install ekstensi:
  - Python (by Microsoft)
  - Django Snippets (by bibhasdn)

## 3. Membuat Virtual Environment
Buka terminal di VS Code, jalankan:

```
python -m venv venv
.\venv\Scripts\activate
```

## 4. Instalasi Django
```
pip install django
```

## 5. Membuat Project Django
```
django-admin startproject akutansi_project .
```

## 6. Membuat Aplikasi Keuangan
```
python manage.py startapp keuangan
```
Tambahkan `'keuangan'` ke `INSTALLED_APPS` di `akutansi_project/settings.py`.

## 7. Membuat Model di keuangan/models.py
Contoh:
```python
from django.db import models
from django.contrib.auth.models import User

class Akun(models.Model):
    nama = models.CharField(max_length=100)
    kode = models.CharField(max_length=10, unique=True)
    tipe = models.CharField(max_length=20)

class Transaksi(models.Model):
    tanggal = models.DateField()
    deskripsi = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Jurnal(models.Model):
    transaksi = models.ForeignKey(Transaksi, on_delete=models.CASCADE)
    akun = models.ForeignKey(Akun, on_delete=models.CASCADE)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    kredit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
```

## 8. Migrasi Database
```
python manage.py makemigrations
python manage.py migrate
```

## 9. Membuat Login & Autentikasi
- Gunakan `django.contrib.auth` untuk login/logout.
- Buat template login di `templates/registration/login.html`.
- Atur di `settings.py`:
  ```python
  LOGIN_REDIRECT_URL = '/'
  LOGOUT_REDIRECT_URL = '/login/'
  ```
- Pisahkan peran admin dan user dengan `is_staff` atau `groups`.

## 10. Mengatur Template HTML
- Buat folder `templates` di root project.
- Tambahkan path ke `TEMPLATES` di `settings.py`:
  ```python
  'DIRS': [BASE_DIR / 'templates'],
  ```
- Buat file HTML untuk dashboard, input transaksi, laporan, dsb.

## 11. Membuat Form Input Transaksi
Buat `forms.py` di app `keuangan`:
```python
from django import forms
from .models import Transaksi

class TransaksiForm(forms.ModelForm):
    class Meta:
        model = Transaksi
        fields = ['tanggal', 'deskripsi']
```

## 12. Menampilkan Jurnal Umum, Buku Besar, Neraca Saldo, Laporan Keuangan
- Buat fungsi di `keuangan/views.py` untuk masing-masing laporan.
- Atur URL di `keuangan/urls.py` dan include di `akutansi_project/urls.py`.

## 13. Menjalankan Server Lokal
```
python manage.py runserver
```
Akses di http://127.0.0.1:8000/

## 14. (Opsional) Deploy ke PythonAnywhere
- Daftar di https://www.pythonanywhere.com/
- Upload project, atur virtualenv, dan domain sesuai petunjuk PythonAnywhere.

---

Lanjutkan dengan membuat file dan folder sesuai instruksi di atas. Jika ingin otomatisasi, jalankan perintah pada terminal sesuai urutan.
