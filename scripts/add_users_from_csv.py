#!/usr/bin/env python3
"""
Script to add users from a CSV file (name,phone format without header)
"""
import sys
import os
import csv
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from src.infrastructure.database.connection import get_db_context
from src.infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from src.domain.entities.user import User

# Load environment variables
load_dotenv()


def add_users_from_csv(csv_file_path: str, language: str = 'es', validity_days: int = 30, skip_existing: bool = True):
    """
    Add users from a CSV file with format: name,phone (no header)
    
    Args:
        csv_file_path: Path to the CSV file
        language: Default language for users (es, en, pt)
        validity_days: Validity period in days
        skip_existing: If True, skip existing users; if False, report error
    """
    
    if not os.path.exists(csv_file_path):
        print(f"❌ File not found: {csv_file_path}")
        return
    
    stats = {
        'total': 0,
        'created': 0,
        'skipped': 0,
        'errors': 0
    }
    
    with get_db_context() as db:
        user_repo = PostgresUserRepository(db)
        
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            
            for row_num, row in enumerate(csv_reader, start=1):
                stats['total'] += 1
                
                # Validate row has exactly 2 columns
                if len(row) != 2:
                    print(f"⚠️  Row {row_num}: Invalid format (expected 2 columns, got {len(row)}) - Skipping")
                    stats['errors'] += 1
                    continue
                
                name, phone = row[0].strip(), row[1].strip()
                
                # Validate phone number is not empty
                if not phone:
                    print(f"⚠️  Row {row_num}: Empty phone number for '{name}' - Skipping")
                    stats['errors'] += 1
                    continue
                
                # Add + prefix if not present
                #if not phone.startswith('+'):
                #    phone = '+' + phone
                
                try:
                    # Check if user already exists
                    existing_user = user_repo.get_by_phone(phone)
                    if existing_user:
                        if skip_existing:
                            print(f"⏭️  Row {row_num}: User '{name}' ({phone}) already exists - Skipping")
                            stats['skipped'] += 1
                            continue
                        else:
                            print(f"❌ Row {row_num}: User '{name}' ({phone}) already exists!")
                            stats['errors'] += 1
                            continue
                    
                    # Create new user
                    user = User(
                        id=None,
                        phone_number=phone,
                        name=name if name else None,
                        language=language,
                        validity_days=validity_days,
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    created_user = user_repo.create(user)
                    print(f"✅ Row {row_num}: Created user '{created_user.name}' ({created_user.phone_number})")
                    stats['created'] += 1
                    
                except Exception as e:
                    print(f"❌ Row {row_num}: Error creating user '{name}' ({phone}): {str(e)}")
                    stats['errors'] += 1
    
    # Print summary
    print("\n" + "="*60)
    print("📊 IMPORT SUMMARY")
    print("="*60)
    print(f"Total rows processed: {stats['total']}")
    print(f"✅ Successfully created: {stats['created']}")
    print(f"⏭️  Skipped (already exist): {stats['skipped']}")
    print(f"❌ Errors: {stats['errors']}")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Add users from CSV file (format: name,phone without header)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import users with default settings (30 days validity, Spanish language)
  python add_users_from_csv.py usuarios.csv
  
  # Import with custom validity period
  python add_users_from_csv.py usuarios.csv --validity 60
  
  # Import with English language
  python add_users_from_csv.py usuarios.csv --language en
  
  # Fail on existing users instead of skipping
  python add_users_from_csv.py usuarios.csv --no-skip-existing
        """
    )
    
    parser.add_argument('csv_file', help='Path to CSV file (format: name,phone)')
    parser.add_argument('--language', help='Language for users (es, en, pt)', default='es')
    parser.add_argument('--validity', type=int, help='Validity period in days', default=30)
    parser.add_argument('--no-skip-existing', action='store_true', 
                       help='Report error for existing users instead of skipping')
    
    args = parser.parse_args()
    
    add_users_from_csv(
        args.csv_file,
        language=args.language,
        validity_days=args.validity,
        skip_existing=not args.no_skip_existing
    )


if __name__ == '__main__':
    main()
