#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akutansi_project.settings')
django.setup()

from django.contrib.auth.models import User
from keuangan.models import Akun

print("=== Testing User Data Isolation ===")

# Create test users if they don't exist
users_data = [
    {'username': 'testuser1', 'password': 'testpass123', 'email': 'test1@example.com'},
    {'username': 'testuser2', 'password': 'testpass123', 'email': 'test2@example.com'},
]

for user_data in users_data:
    user, created = User.objects.get_or_create(
        username=user_data['username'],
        defaults={
            'email': user_data['email'],
            'is_active': True
        }
    )
    if created:
        user.set_password(user_data['password'])
        user.save()
        print(f"✅ Created user: {user.username}")
        
        # Create some test accounts for this user
        test_accounts = [
            {'kode': f'{user.username[:3].upper()}001', 'nama': f'Kas {user.username}', 'tipe': 'Aset'},
            {'kode': f'{user.username[:3].upper()}002', 'nama': f'Bank {user.username}', 'tipe': 'Aset'},
            {'kode': f'{user.username[:3].upper()}003', 'nama': f'Modal {user.username}', 'tipe': 'Modal'},
        ]
        
        for account_data in test_accounts:
            akun, created = Akun.objects.get_or_create(
                kode=account_data['kode'],
                user=user,
                defaults={
                    'nama': account_data['nama'],
                    'tipe': account_data['tipe']
                }
            )
            if created:
                print(f"  ✅ Created account: {akun.kode} - {akun.nama}")
    else:
        print(f"User {user.username} already exists")

print("\n=== User Account Summary ===")
for user in User.objects.all():
    user_accounts = Akun.objects.filter(user=user)
    print(f"User '{user.username}' has {user_accounts.count()} accounts:")
    for akun in user_accounts[:3]:  # Show first 3
        print(f"  - {akun.kode}: {akun.nama}")
    if user_accounts.count() > 3:
        print(f"  ... and {user_accounts.count() - 3} more")

print("\n=== Test Complete ===")
print("You can now login with:")
print("- Username: testuser1, Password: testpass123")
print("- Username: testuser2, Password: testpass123")
print("- Username: admin, Password: [your admin password]")
