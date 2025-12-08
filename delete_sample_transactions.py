#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akutansi_project.settings')
django.setup()

from keuangan.models import Transaksi, Jurnal

def delete_sample_transactions():
    """
    Safely delete sample transactions while preserving:
    - All account data (Chart of Accounts)
    - All code fixes (views, templates, forms)
    - All system improvements
    """
    
    print("Current database state:")
    print(f"- Transactions: {Transaksi.objects.count()}")
    print(f"- Journal entries: {Jurnal.objects.count()}")
    
    # Get all transactions
    transactions = Transaksi.objects.all()
    
    if transactions.exists():
        print(f"\nFound {transactions.count()} transactions to delete:")
        for trans in transactions:
            print(f"  - {trans.tanggal} | {getattr(trans, 'nomor_transaksi', 'N/A')} | {trans.deskripsi}")
        
        # Delete all journal entries first (due to foreign key constraints)
        journal_count = Jurnal.objects.count()
        Jurnal.objects.all().delete()
        print(f"\n✅ Deleted {journal_count} journal entries")
        
        # Delete all transactions
        transaction_count = transactions.count()
        Transaksi.objects.all().delete()
        print(f"✅ Deleted {transaction_count} transactions")
        
        print(f"\nDatabase cleaned! Current state:")
        print(f"- Transactions: {Transaksi.objects.count()}")
        print(f"- Journal entries: {Jurnal.objects.count()}")
        
    else:
        print("\nNo transactions found to delete.")
    
    # Verify accounts are still intact
    from keuangan.models import Akun
    account_count = Akun.objects.count()
    print(f"- Chart of Accounts: {account_count} accounts (preserved)")
    
    if account_count > 0:
        print("\n✅ All system improvements and account data preserved!")
        print("✅ Sample transactions removed successfully!")
    else:
        print("\n⚠️  Warning: No accounts found. You may need to re-run add_accounts.py")

if __name__ == "__main__":
    delete_sample_transactions()
