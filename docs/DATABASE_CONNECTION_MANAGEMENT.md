# Database Connection Management Guide

## Problem: Connections Staying Open

The application was keeping database connections open because:
1. Sessions were created but never closed
2. Connection pool was too large
3. No connection recycling
4. Alembic migrations didn't dispose of engines

## Solutions Implemented

### 1. Reduced Connection Pool Size
```python
# Before
pool_size=10, max_overflow=20  # Up to 30 connections!

# After
pool_size=5, max_overflow=10  # Up to 15 connections
pool_recycle=3600  # Recycle after 1 hour
pool_timeout=30  # Timeout for getting connection
```

### 2. Alembic Uses NullPool
Alembic now uses `NullPool` which closes connections immediately after use:
```python
poolclass=pool.NullPool  # No connection pooling during migrations
connectable.dispose()  # Explicitly close all connections
```

### 3. Proper Session Management

**❌ BAD - Session Never Closed:**
```python
def get_chat_service():
    db = get_db()  # Session created
    # ... use db ...
    return service  # Session NEVER closed!
```

**✅ GOOD - Use Context Manager:**
```python
from src.infrastructure.database.connection import get_db_context

with get_db_context() as db:
    user_repo = PostgresUserRepository(db)
    # ... use repos ...
    # Session automatically closed when exiting 'with' block
```

## How to Use Properly

### Option 1: Context Manager (Recommended)
```python
from src.infrastructure.database.connection import get_db_context

def process_request():
    with get_db_context() as db:
        user_repo = PostgresUserRepository(db)
        user = user_repo.get_by_phone("+1234567890")
        # Session automatically closed here
```

### Option 2: Manual Session Management
```python
from src.infrastructure.database.connection import get_db

def process_request():
    db = get_db()
    try:
        user_repo = PostgresUserRepository(db)
        user = user_repo.get_by_phone("+1234567890")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()  # MUST close manually!
```

### Option 3: Flask Request Scope
For Flask applications, use teardown:
```python
from flask import g
from src.infrastructure.database.connection import get_db

@app.before_request
def before_request():
    g.db = get_db()

@app.teardown_request
def teardown_request(exception=None):
    db = g.pop('db', None)
    if db is not None:
        if exception:
            db.rollback()
        db.close()
```

## Checking Open Connections

### PostgreSQL Query
```sql
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query,
    state_change
FROM pg_stat_activity
WHERE datname = 'your_database_name'
ORDER BY state_change DESC;
```

### Count Active Connections
```sql
SELECT count(*) 
FROM pg_stat_activity 
WHERE datname = 'your_database_name';
```

## Migration Best Practices

### Run Migrations
```bash
# Set DATABASE_URL in .env file instead of exporting
# This ensures consistent connection string

# Run migration
alembic upgrade head

# Connections are now automatically closed after migration
```

### Check Migration Status
```bash
# Current version
alembic current

# History
alembic history

# Pending migrations
alembic heads
```

## Troubleshooting

### Too Many Connections Error
If you see "too many connections" error:

1. **Check current connections:**
   ```sql
   SELECT count(*) FROM pg_stat_activity;
   ```

2. **Kill idle connections:**
   ```sql
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE state = 'idle'
   AND state_change < NOW() - INTERVAL '5 minutes';
   ```

3. **Reduce pool size** in `connection.py`:
   ```python
   pool_size=3,  # Even smaller
   max_overflow=5
   ```

### Connections Not Closing
1. Check that you're using context managers or closing sessions
2. Verify no long-running transactions
3. Check for exception handling that skips `db.close()`

### Alembic Hanging
If Alembic hangs during migration:
1. Check for locks: `SELECT * FROM pg_locks;`
2. Kill blocking queries
3. Use `pool.NullPool` (already implemented)
4. Ensure `connectable.dispose()` is called (already implemented)

## Configuration Recommendations

### Development
```python
# .env
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/db
SQL_ECHO=true  # See all SQL queries
```

### Production
```python
# .env
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db
SQL_ECHO=false
```

### Connection Pool Settings

**Small Application (< 10 concurrent users):**
```python
pool_size=3
max_overflow=5
```

**Medium Application (10-50 concurrent users):**
```python
pool_size=5
max_overflow=10
```

**Large Application (> 50 concurrent users):**
```python
pool_size=10
max_overflow=20
```

## Summary

✅ **What was fixed:**
- Reduced connection pool from 30 to 15 max connections
- Added connection recycling (1 hour)
- Alembic now uses NullPool and disposes engines
- Added proper session management warnings
- Imported MetricModel in Alembic env.py

✅ **What you should do:**
- Always use `get_db_context()` context manager
- If using `get_db()`, always close the session
- Monitor connection count in production
- Adjust pool size based on your needs
