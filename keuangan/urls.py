from django.urls import path
from . import views
from . import views_laporan

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('input/', views.input_transaksi, name='input_transaksi'),
    path('jurnal/', views.jurnal_umum, name='jurnal_umum'),
    path('jurnal/pdf/', views.jurnal_umum_pdf, name='jurnal_umum_pdf'),
    path('jurnal/excel/', views.jurnal_umum_excel, name='jurnal_umum_excel'),
    path('buku-besar/', views_laporan.buku_besar, name='buku_besar'),
    path('buku-besar/pdf/', views_laporan.buku_besar_pdf, name='buku_besar_pdf'),
    path('buku-besar/excel/', views_laporan.buku_besar_excel, name='buku_besar_excel'),
    path('neraca-saldo/', views_laporan.neraca_saldo, name='neraca_saldo'),
    path('neraca-saldo/pdf/', views_laporan.neraca_saldo_pdf, name='neraca_saldo_pdf'),
    path('neraca-saldo/excel/', views_laporan.neraca_saldo_excel, name='neraca_saldo_excel'),
    path('laporan-keuangan/', views_laporan.laporan_keuangan, name='laporan_keuangan'),
    path('laporan-keuangan/pdf/', views_laporan.laporan_keuangan_pdf, name='laporan_keuangan_pdf'),
    path('laporan-keuangan/excel/', views_laporan.laporan_keuangan_excel, name='laporan_keuangan_excel'),
    
    # URL untuk manajemen akun
    path('akun/', views.daftar_akun, name='daftar_akun'),
    path('akun/pdf/', views.daftar_akun_pdf, name='daftar_akun_pdf'),
    path('akun/excel/', views.daftar_akun_excel, name='daftar_akun_excel'),
    path('akun/tambah/', views.tambah_akun, name='tambah_akun'),
    path('akun/edit/<int:id>/', views.edit_akun, name='edit_akun'),
    path('akun/hapus/<int:id>/', views.hapus_akun, name='hapus_akun'),
    # API endpoints for ajax CRUD on transaksi
    path('transaksi/api/list/', views.transaksi_api_list, name='transaksi_api_list'),
    path('transaksi/api/create/', views.transaksi_api_create, name='transaksi_api_create'),
    path('transaksi/api/<int:id>/update/', views.transaksi_api_update, name='transaksi_api_update'),
    path('transaksi/api/<int:id>/delete/', views.transaksi_api_delete, name='transaksi_api_delete'),
    
    # URL untuk profil pengguna
    path('profile/', views.profile_view, name='profile'),
]
