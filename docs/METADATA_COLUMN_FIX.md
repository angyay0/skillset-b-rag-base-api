# Metadata Column Fix

## Problem
SQLAlchemy raised an error: `Attribute name 'metadata' is reserved when using the Declarative API.`

This occurred because the `MessageModel` had a column named `metadata`, which conflicts with SQLAlchemy's built-in `metadata` attribute used for table definitions.

## Solution
Renamed the column from `metadata` to `message_metadata` to avoid the conflict.

## Files Changed

### 1. `src/infrastructure/database/models.py`
**Line 49**: Changed column name
```python
# Before
metadata = Column(JSON, nullable=True)

# After
message_metadata = Column(JSON, nullable=True)
```

### 2. `src/infrastructure/repositories/postgres_conversation_repository.py`
**Lines 89 and 121**: Updated references to use the new column name

**In `create()` method:**
```python
# Before
metadata=message.metadata

# After
message_metadata=message.metadata
```

**In `_to_entity()` method:**
```python
# Before
metadata=db_message.metadata

# After
metadata=db_message.message_metadata
```

## Verification
The fix has been verified - models now import successfully without errors:
```bash
✓ Models imported successfully - metadata conflict resolved!
```

## Next Steps

### 1. Configure Database Connection
Before running migrations, set up your database connection in `.env`:

```bash
# For local PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/blinky_db

# For Cloud SQL (production)
DATABASE_URL=postgresql://user:password@/blinky_db?host=/cloudsql/project:region:instance
```

### 2. Create Initial Migration
```bash
# Activate virtual environment
source venv/bin/activate

# Create migration
alembic revision --autogenerate -m "Initial schema with message_metadata"
```

### 3. Apply Migration
```bash
alembic upgrade head
```

## Database Schema
The `messages` table will now have the column `message_metadata` instead of `metadata`:

```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    language VARCHAR(10) NOT NULL,
    message_metadata JSON,  -- Changed from 'metadata'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Impact
- **Domain Layer**: No changes needed - the `Message` entity still uses `metadata` attribute
- **Repository Layer**: Updated to map between entity's `metadata` and model's `message_metadata`
- **Application Layer**: No changes needed - continues using `metadata` in business logic

This maintains clean separation between domain and infrastructure layers.
