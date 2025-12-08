#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akutansi_project.settings')
django.setup()

from keuangan.models import Akun
from django.contrib.auth.models import User

print("=== Test Migration Results ===")

# Check if user field exists in Akun model
try:
    # Get all accounts
    akun_count = Akun.objects.count()
    print(f"Total Akun: {akun_count}")
    
    # Check if user field exists by trying to access it
    if akun_count > 0:
        first_akun = Akun.objects.first()
        print(f"First Akun user: {first_akun.user}")
        print("✅ User field successfully added to Akun model")
    else:
        print("No Akun data found")
    
    # Check users
    user_count = User.objects.count()
    print(f"Total Users: {user_count}")
    
    if user_count > 0:
        users = User.objects.all()
        for user in users:
            user_akun_count = Akun.objects.filter(user=user).count()
            print(f"User '{user.username}' has {user_akun_count} akun")
    
    print("✅ Migration completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
