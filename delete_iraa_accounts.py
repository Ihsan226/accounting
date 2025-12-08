#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akutansi_project.settings')
django.setup()

from django.contrib.auth.models import User
from keuangan.models import Akun, Jurnal, Transaksi

print("=== Menghapus Semua Akun User Iraa ===")

try:
    # Get user iraa
    user_iraa = User.objects.get(username='iraa')
    print(f"✅ Found user: {user_iraa.username}")
    
    # Get all accounts belonging to iraa
    iraa_accounts = Akun.objects.filter(user=user_iraa)
    account_count = iraa_accounts.count()
    
    print(f"📊 Current accounts for iraa: {account_count}")
    
    if account_count > 0:
        print("\n🗑️ Accounts to be deleted:")
        for akun in iraa_accounts:
            print(f"   - {akun.kode}: {akun.nama}")
        
        # Check if any accounts are used in transactions
        used_accounts = []
        for akun in iraa_accounts:
            jurnal_count = Jurnal.objects.filter(akun=akun).count()
            if jurnal_count > 0:
                used_accounts.append((akun, jurnal_count))
        
        if used_accounts:
            print("\n⚠️ WARNING: Some accounts are used in transactions:")
            for akun, count in used_accounts:
                print(f"   - {akun.kode}: used in {count} journal entries")
            
            # Delete related journal entries first
            print("\n🗑️ Deleting related journal entries...")
            for akun, count in used_accounts:
                jurnal_entries = Jurnal.objects.filter(akun=akun)
                
                # Get unique transactions that will be affected
                affected_transactions = Transaksi.objects.filter(
                    jurnal__akun=akun
                ).distinct()
                
                print(f"   - Deleting {count} journal entries for {akun.kode}")
                jurnal_entries.delete()
                
                # Check if transactions have no more journal entries, delete them too
                for transaksi in affected_transactions:
                    remaining_jurnal = Jurnal.objects.filter(transaksi=transaksi).count()
                    if remaining_jurnal == 0:
                        print(f"   - Deleting empty transaction: {transaksi.deskripsi}")
                        transaksi.delete()
        
        # Now delete all accounts
        print(f"\n🗑️ Deleting {account_count} accounts...")
        deleted_count = iraa_accounts.delete()[0]
        print(f"✅ Successfully deleted {deleted_count} records")
        
    else:
        print("ℹ️ User iraa already has 0 accounts")
    
    # Verify deletion
    final_count = Akun.objects.filter(user=user_iraa).count()
    print(f"\n📊 Final account count for iraa: {final_count}")
    
    if final_count == 0:
        print("✅ SUCCESS: User iraa now has 0 accounts!")
    else:
        print(f"❌ ERROR: Still has {final_count} accounts remaining")

except User.DoesNotExist:
    print("❌ ERROR: User 'iraa' not found")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

print("\n=== Final User Account Summary ===")
all_users = User.objects.all()
for user in all_users:
    user_accounts = Akun.objects.filter(user=user)
    print(f"📊 {user.username}: {user_accounts.count()} accounts")

print("\n✅ Operation completed!")
print("\nNow iraa will see 'Total Akun: 0' in dashboard")
