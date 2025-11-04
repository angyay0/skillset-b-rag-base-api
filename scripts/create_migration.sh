#!/bin/bash

# Create migration for validity_days column

echo "Creating database migration for validity_days..."
alembic revision --autogenerate -m "add_validity_days_to_users"

echo "✓ Migration created!"
echo ""
echo "To apply the migration, run:"
echo "  alembic upgrade head"
