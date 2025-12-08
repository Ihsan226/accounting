#!/usr/bin/env python
import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akutansi_project.settings')
django.setup()

from django.contrib.auth.models import User
from keuangan.models import Akun, Transaksi, Jurnal

def create_sample_transactions():
    # Get or create a user
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'is_superuser': True,
            'is_staff': True
        }
    )
    if created:
        user.set_password('admin')
        user.save()
        print(f"Created admin user")

    # Get accounts
    kas = Akun.objects.get(kode='1001')  # Kas
    bank = Akun.objects.get(kode='1002')  # Bank BCA
    piutang = Akun.objects.get(kode='1101')  # Piutang Dagang
    modal = Akun.objects.get(kode='3001')  # Modal Saham
    pendapatan = Akun.objects.get(kode='4001')  # Pendapatan Penjualan
    beban_gaji = Akun.objects.get(kode='5001')  # Beban Gaji
    beban_sewa = Akun.objects.get(kode='5004')  # Beban Sewa

    # Clear existing transactions
    Jurnal.objects.all().delete()
    Transaksi.objects.all().delete()

    sample_transactions = [
        # Initial Capital Investment
        {
            'tanggal': date.today() - timedelta(days=30),
            'nomor_transaksi': 'TRX-001',
            'deskripsi': 'Setoran modal awal dari pemilik',
            'debet_akun': kas,
            'kredit_akun': modal,
            'jumlah': Decimal('50000000.00')
        },
        # Transfer to Bank
        {
            'tanggal': date.today() - timedelta(days=29),
            'nomor_transaksi': 'TRX-002',
            'deskripsi': 'Transfer dana ke bank untuk keamanan',
            'debet_akun': bank,
            'kredit_akun': kas,
            'jumlah': Decimal('40000000.00')
        },
        # Sales Revenue
        {
            'tanggal': date.today() - timedelta(days=25),
            'nomor_transaksi': 'TRX-003',
            'deskripsi': 'Penjualan barang secara tunai',
            'debet_akun': kas,
            'kredit_akun': pendapatan,
            'jumlah': Decimal('15000000.00')
        },
        # Credit Sales
        {
            'tanggal': date.today() - timedelta(days=20),
            'nomor_transaksi': 'TRX-004',
            'deskripsi': 'Penjualan barang secara kredit',
            'debet_akun': piutang,
            'kredit_akun': pendapatan,
            'jumlah': Decimal('8000000.00')
        },
        # Salary Expense
        {
            'tanggal': date.today() - timedelta(days=15),
            'nomor_transaksi': 'TRX-005',
            'deskripsi': 'Pembayaran gaji karyawan bulan ini',
            'debet_akun': beban_gaji,
            'kredit_akun': bank,
            'jumlah': Decimal('12000000.00')
        },
        # Rent Expense
        {
            'tanggal': date.today() - timedelta(days=10),
            'nomor_transaksi': 'TRX-006',
            'deskripsi': 'Pembayaran sewa kantor bulan ini',
            'debet_akun': beban_sewa,
            'kredit_akun': bank,
            'jumlah': Decimal('5000000.00')
        },
        # Collection from Customer
        {
            'tanggal': date.today() - timedelta(days=5),
            'nomor_transaksi': 'TRX-007',
            'deskripsi': 'Penerimaan pembayaran dari pelanggan',
            'debet_akun': kas,
            'kredit_akun': piutang,
            'jumlah': Decimal('5000000.00')
        },
    ]

    created_count = 0
    for trans_data in sample_transactions:
        # Create transaction
        transaksi = Transaksi.objects.create(
            tanggal=trans_data['tanggal'],
            deskripsi=trans_data['deskripsi'],
            user=user
        )
        
        # Add nomor_transaksi if field exists
        if hasattr(transaksi, 'nomor_transaksi'):
            transaksi.nomor_transaksi = trans_data['nomor_transaksi']
            transaksi.save()

        # Create debit entry
        Jurnal.objects.create(
            transaksi=transaksi,
            akun=trans_data['debet_akun'],
            debit=trans_data['jumlah'],
            kredit=Decimal('0.00')
        )

        # Create credit entry
        Jurnal.objects.create(
            transaksi=transaksi,
            akun=trans_data['kredit_akun'],
            debit=Decimal('0.00'),
            kredit=trans_data['jumlah']
        )

        created_count += 1
        print(f"Created transaction: {trans_data['nomor_transaksi']} - {trans_data['deskripsi']}")

    print(f"\nCompleted! Created {created_count} sample transactions.")
    print(f"Total transactions: {Transaksi.objects.count()}")
    print(f"Total journal entries: {Jurnal.objects.count()}")

if __name__ == "__main__":
    create_sample_transactions()
