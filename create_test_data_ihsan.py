#!/usr/bin/env python
import os
import sys
import django
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akutansi_project.settings')
django.setup()

from django.contrib.auth.models import User
from keuangan.models import Akun, Transaksi, Jurnal

print("=== Membuat Data Test untuk User ihsan ===")

try:
    # Get user ihsan
    user_ihsan = User.objects.get(username='ihsan')
    print(f"✅ Found user: {user_ihsan.username}")
    
    # Get akun milik ihsan
    ihsan_accounts = Akun.objects.filter(user=user_ihsan)
    print(f"📊 Available accounts for ihsan: {ihsan_accounts.count()}")
    
    if ihsan_accounts.count() == 0:
        print("❌ No accounts found for ihsan. Please run setup_user_data.py first")
        exit()
    
    # Map akun untuk kemudahan
    akun_map = {}
    for akun in ihsan_accounts:
        akun_map[akun.kode] = akun
        print(f"   - {akun.kode}: {akun.nama} ({akun.tipe})")
    
    # Hapus transaksi lama jika ada
    old_transactions = Transaksi.objects.filter(jurnal__akun__user=user_ihsan).distinct()
    if old_transactions.exists():
        old_count = old_transactions.count()
        print(f"\n🗑️ Deleting {old_count} old transactions...")
        for transaksi in old_transactions:
            Jurnal.objects.filter(transaksi=transaksi).delete()
            transaksi.delete()
    
    # Data transaksi test
    test_transactions = [
        {
            'tanggal': date.today() - timedelta(days=10),
            'deskripsi': 'Modal Awal Usaha Ihsan',
            'jurnal': [
                {'akun': 'IHS001', 'debit': 10000000, 'kredit': 0},  # Kas
                {'akun': 'IHS005', 'debit': 0, 'kredit': 10000000},  # Modal
            ]
        },
        {
            'tanggal': date.today() - timedelta(days=9),
            'deskripsi': 'Pembelian Persediaan',
            'jurnal': [
                {'akun': 'IHS003', 'debit': 5000000, 'kredit': 0},   # Persediaan
                {'akun': 'IHS001', 'debit': 0, 'kredit': 5000000},   # Kas
            ]
        },
        {
            'tanggal': date.today() - timedelta(days=8),
            'deskripsi': 'Penjualan Barang',
            'jurnal': [
                {'akun': 'IHS001', 'debit': 7500000, 'kredit': 0},   # Kas
                {'akun': 'IHS006', 'debit': 0, 'kredit': 7500000},   # Pendapatan
            ]
        },
        {
            'tanggal': date.today() - timedelta(days=7),
            'deskripsi': 'Beban Operasional',
            'jurnal': [
                {'akun': 'IHS007', 'debit': 1500000, 'kredit': 0},   # Beban
                {'akun': 'IHS001', 'debit': 0, 'kredit': 1500000},   # Kas
            ]
        },
        {
            'tanggal': date.today() - timedelta(days=5),
            'deskripsi': 'Simpan Uang di Bank',
            'jurnal': [
                {'akun': 'IHS002', 'debit': 5000000, 'kredit': 0},   # Bank
                {'akun': 'IHS001', 'debit': 0, 'kredit': 5000000},   # Kas
            ]
        },
        {
            'tanggal': date.today() - timedelta(days=3),
            'deskripsi': 'Hutang untuk Ekspansi',
            'jurnal': [
                {'akun': 'IHS001', 'debit': 3000000, 'kredit': 0},   # Kas
                {'akun': 'IHS004', 'debit': 0, 'kredit': 3000000},   # Utang
            ]
        },
        {
            'tanggal': date.today() - timedelta(days=1),
            'deskripsi': 'Penjualan Lanjutan',
            'jurnal': [
                {'akun': 'IHS002', 'debit': 4000000, 'kredit': 0},   # Bank (transfer)
                {'akun': 'IHS006', 'debit': 0, 'kredit': 4000000},   # Pendapatan
            ]
        }
    ]
    
    print(f"\n💾 Creating {len(test_transactions)} test transactions...")
    
    created_count = 0
    for trans_data in test_transactions:
        # Buat transaksi dengan user
        transaksi = Transaksi.objects.create(
            tanggal=trans_data['tanggal'],
            deskripsi=trans_data['deskripsi'],
            user=user_ihsan  # Tambahkan user
        )
        
        # Buat jurnal entries
        for jurnal_data in trans_data['jurnal']:
            akun_kode = jurnal_data['akun']
            if akun_kode in akun_map:
                Jurnal.objects.create(
                    transaksi=transaksi,
                    akun=akun_map[akun_kode],
                    debit=jurnal_data['debit'],
                    kredit=jurnal_data['kredit']
                )
        
        created_count += 1
        print(f"   ✅ {trans_data['tanggal']}: {trans_data['deskripsi']}")
    
    print(f"\n✅ Successfully created {created_count} transactions for ihsan")
    
    # Verifikasi data
    print("\n📊 Verification - Account Balances for ihsan:")
    for akun in ihsan_accounts:
        jurnal_entries = Jurnal.objects.filter(akun=akun)
        total_debit = sum(j.debit for j in jurnal_entries)
        total_kredit = sum(j.kredit for j in jurnal_entries)
        saldo = total_debit - total_kredit
        
        print(f"   {akun.kode} ({akun.nama}): ")
        print(f"      Debit: Rp {total_debit:,}")
        print(f"      Kredit: Rp {total_kredit:,}")
        print(f"      Saldo: Rp {saldo:,}")
    
    print("\n🎯 Summary for ihsan:")
    total_transaksi = Transaksi.objects.filter(jurnal__akun__user=user_ihsan).distinct().count()
    total_jurnal = Jurnal.objects.filter(akun__user=user_ihsan).count()
    print(f"   - Total Transaksi: {total_transaksi}")
    print(f"   - Total Jurnal Entries: {total_jurnal}")
    print(f"   - Total Akun: {ihsan_accounts.count()}")

except User.DoesNotExist:
    print("❌ ERROR: User 'ihsan' not found")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

print("\n✅ Test data creation completed!")
print("\nNow ihsan will have rich data to test:")
print("- Neraca Saldo with actual balances")
print("- Jurnal Umum with multiple transactions")
print("- Buku Besar with detailed entries")
print("- Laporan Keuangan with income/expenses")
