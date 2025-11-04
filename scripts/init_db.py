#!/usr/bin/env python3
"""
Initialize database with tables
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables BEFORE importing database modules
from dotenv import load_dotenv
load_dotenv(override=True)

# Now import database modules (they read DATABASE_URL at import time)
from src.infrastructure.database.connection import init_db

if __name__ == '__main__':
    print("Initializing database...")
    try:
        init_db()
        print("✓ Database initialized successfully!")
        print("\nTables created:")
        print("  - users")
        print("  - conversations")
        print("  - messages")
    except Exception as e:
        print(f"✗ Error initializing database: {str(e)}")
        sys.exit(1)
