#!/usr/bin/env python3
"""
Script to add users to the database
"""
import sys
import os
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


def add_user(phone_number: str, name: str = None, language: str = 'es', validity_days: int = 30):
    """Add a new user to the database"""
    
    with get_db_context() as db:
        user_repo = PostgresUserRepository(db)
        
        # Check if user already exists
        existing_user = user_repo.get_by_phone(phone_number)
        if existing_user:
            print(f"❌ User with phone number {phone_number} already exists!")
            print(f"   ID: {existing_user.id}")
            print(f"   Name: {existing_user.name}")
            print(f"   Language: {existing_user.language}")
            print(f"   Validity: {existing_user.validity_days} days")
            print(f"   Created: {existing_user.created_at}")
            print(f"   Valid until: {existing_user.expiration_date()}")
            print(f"   Days remaining: {existing_user.days_remaining()}")
            print(f"   Is valid: {existing_user.is_valid()}")
            return False
        
        # Create new user
        user = User(
            id=None,
            phone_number=phone_number,
            name=name,
            language=language,
            validity_days=validity_days,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        created_user = user_repo.create(user)
        
        print(f"✅ User created successfully!")
        print(f"   ID: {created_user.id}")
        print(f"   Phone: {created_user.phone_number}")
        print(f"   Name: {created_user.name or 'Not set'}")
        print(f"   Language: {created_user.language}")
        print(f"   Validity: {created_user.validity_days} days")
        print(f"   Created: {created_user.created_at}")
        print(f"   Valid until: {created_user.expiration_date()}")
        print(f"   Days remaining: {created_user.days_remaining()}")
        
        return True


def list_users():
    """List all users in the database"""
    
    with get_db_context() as db:
        user_repo = PostgresUserRepository(db)
        users = user_repo.list_all(limit=1000)
        
        if not users:
            print("No users found in the database.")
            return
        
        print(f"\n📋 Total users: {len(users)}\n")
        print(f"{'ID':<5} {'Phone':<20} {'Name':<20} {'Language':<10} {'Valid Days':<12} {'Days Left':<12} {'Status':<10}")
        print("-" * 100)
        
        for user in users:
            status = "✓ Active" if user.is_valid() else "✗ Expired"
            print(f"{user.id:<5} {user.phone_number:<20} {(user.name or 'N/A'):<20} {user.language:<10} {user.validity_days:<12} {user.days_remaining():<12} {status:<10}")


def update_user_validity(phone_number: str, validity_days: int):
    """Update user validity period"""
    
    with get_db_context() as db:
        user_repo = PostgresUserRepository(db)
        
        user = user_repo.get_by_phone(phone_number)
        if not user:
            print(f"❌ User with phone number {phone_number} not found!")
            return False
        
        user.validity_days = validity_days
        updated_user = user_repo.update(user)
        
        print(f"✅ User validity updated successfully!")
        print(f"   Phone: {updated_user.phone_number}")
        print(f"   New validity: {updated_user.validity_days} days")
        print(f"   Valid until: {updated_user.expiration_date()}")
        print(f"   Days remaining: {updated_user.days_remaining()}")
        print(f"   Is valid: {updated_user.is_valid()}")
        
        return True


def deactivate_user(phone_number: str):
    """Deactivate a user"""
    
    with get_db_context() as db:
        user_repo = PostgresUserRepository(db)
        
        user = user_repo.get_by_phone(phone_number)
        if not user:
            print(f"❌ User with phone number {phone_number} not found!")
            return False
        
        user.is_active = False
        updated_user = user_repo.update(user)
        
        print(f"✅ User deactivated successfully!")
        print(f"   Phone: {updated_user.phone_number}")
        print(f"   Status: Inactive")
        
        return True


def main():
    parser = argparse.ArgumentParser(description='Manage users in the database')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add user command
    add_parser = subparsers.add_parser('add', help='Add a new user')
    add_parser.add_argument('phone', help='Phone number (e.g., +1234567890)')
    add_parser.add_argument('--name', help='User name', default=None)
    add_parser.add_argument('--language', help='Language (es, en, pt)', default='es')
    add_parser.add_argument('--validity', type=int, help='Validity period in days', default=30)
    
    # List users command
    list_parser = subparsers.add_parser('list', help='List all users')
    
    # Update validity command
    update_parser = subparsers.add_parser('update', help='Update user validity')
    update_parser.add_argument('phone', help='Phone number')
    update_parser.add_argument('--validity', type=int, required=True, help='New validity period in days')
    
    # Deactivate user command
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate a user')
    deactivate_parser.add_argument('phone', help='Phone number')
    
    args = parser.parse_args()
    
    if args.command == 'add':
        add_user(args.phone, args.name, args.language, args.validity)
    elif args.command == 'list':
        list_users()
    elif args.command == 'update':
        update_user_validity(args.phone, args.validity)
    elif args.command == 'deactivate':
        deactivate_user(args.phone)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
