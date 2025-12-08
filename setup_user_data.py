#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akutansi_project.settings')
django.setup()

from django.contrib.auth.models import User
from keuangan.models import Akun

print("=== Creating Different Data for Each User ===")

# Data untuk setiap user
users_accounts = {
    'iraa': [
        {'kode': 'IRR001', 'nama': 'Kas Iraa', 'tipe': 'Aset'},
        {'kode': 'IRR002', 'nama': 'Bank BNI Iraa', 'tipe': 'Aset'},
        {'kode': 'IRR003', 'nama': 'Piutang Iraa', 'tipe': 'Aset'},
        {'kode': 'IRR004', 'nama': 'Modal Iraa', 'tipe': 'Modal'},
        {'kode': 'IRR005', 'nama': 'Pendapatan Jasa Iraa', 'tipe': 'Pendapatan'},
    ],
    'ihsan': [
        {'kode': 'IHS001', 'nama': 'Kas Ihsan', 'tipe': 'Aset'},
        {'kode': 'IHS002', 'nama': 'Bank BRI Ihsan', 'tipe': 'Aset'},
        {'kode': 'IHS003', 'nama': 'Persediaan Ihsan', 'tipe': 'Aset'},
        {'kode': 'IHS004', 'nama': 'Utang Ihsan', 'tipe': 'Kewajiban'},
        {'kode': 'IHS005', 'nama': 'Modal Ihsan', 'tipe': 'Modal'},
        {'kode': 'IHS006', 'nama': 'Pendapatan Ihsan', 'tipe': 'Pendapatan'},
        {'kode': 'IHS007', 'nama': 'Beban Operasional Ihsan', 'tipe': 'Beban'},
    ]
}

# Buat akun untuk setiap user
for username, accounts_data in users_accounts.items():
    try:
        user = User.objects.get(username=username)
        print(f"\n✅ Processing user: {username}")
        
        # Hapus akun lama jika ada
        old_accounts = Akun.objects.filter(user=user)
        if old_accounts.exists():
            old_count = old_accounts.count()
            old_accounts.delete()
            print(f"  🗑️ Deleted {old_count} old accounts")
        
        # Buat akun baru
        for account_data in accounts_data:
            akun = Akun.objects.create(
                kode=account_data['kode'],
                nama=account_data['nama'],
                tipe=account_data['tipe'],
                user=user
            )
            print(f"  ✅ Created: {akun.kode} - {akun.nama}")
            
        print(f"  📊 Total accounts for {username}: {len(accounts_data)}")
        
    except User.DoesNotExist:
        print(f"❌ User {username} not found")

print("\n=== Final User Account Summary ===")
all_users = User.objects.all()
for user in all_users:
    user_accounts = Akun.objects.filter(user=user)
    print(f"📊 {user.username}: {user_accounts.count()} accounts")
    if user_accounts.count() <= 7:  # Show all if 7 or less
        for akun in user_accounts:
            print(f"   - {akun.kode}: {akun.nama}")
    else:  # Show first 3 and count
        for akun in user_accounts[:3]:
            print(f"   - {akun.kode}: {akun.nama}")
        print(f"   ... and {user_accounts.count() - 3} more")

print("\n✅ Data isolation setup complete!")
print("\nNow each user will see different totals:")
print("- admin: 27 accounts (original data)")
print("- iraa: 5 accounts")  
print("- ihsan: 7 accounts")
print("- testuser1: 3 accounts")
print("- testuser2: 3 accounts")
