# User Validation System - Changes Summary

## Overview

The application has been updated to include a comprehensive user validation and access control system. Users must now be registered in the database before they can use the service, and each user has a configurable validity period.

## Key Changes

### 1. User Entity Updates

**File**: `src/domain/entities/user.py`

**New Fields:**
- `validity_days: int = 30` - Number of days user has access from creation date

**New Methods:**
- `is_valid() -> bool` - Check if user is within valid service period
- `days_remaining() -> int` - Get number of days remaining
- `expiration_date() -> datetime` - Get the expiration date

**Example:**
```python
user = user_repo.get_by_phone("+1234567890")
if user.is_valid():
    print(f"User has {user.days_remaining()} days remaining")
else:
    print(f"User expired on {user.expiration_date()}")
```

### 2. Database Model Updates

**File**: `src/infrastructure/database/models.py`

**New Column:**
```python
validity_days = Column(Integer, default=30, nullable=False)
```

**Migration Required:**
```bash
# Create migration
alembic revision --autogenerate -m "add_validity_days_to_users"

# Apply migration
alembic upgrade head
```

### 3. Repository Updates

**File**: `src/infrastructure/repositories/postgres_user_repository.py`

**Changes:**
- `create()` - Now includes `validity_days` parameter
- `update()` - Can update `validity_days`
- `_to_entity()` - Maps `validity_days` from database

### 4. Chat Service Updates

**File**: `src/application/services/chat_service.py`

**Major Changes:**

#### Before (Auto-create users)
```python
user = self.user_repo.get_by_phone(phone_number)
if not user:
    user = self._create_user(phone_number, language)
```

#### After (Validate users)
```python
user = self.user_repo.get_by_phone(phone_number)
if not user:
    return self._get_no_access_message(language)

if not user.is_valid():
    return self._get_expired_message(language, user)
```

**New Methods:**
- `_get_no_access_message(language)` - Message for unregistered users
- `_get_expired_message(language, user)` - Message for expired users

### 5. User Management Script

**File**: `scripts/add_user.py`

**Commands:**

```bash
# Add user
python scripts/add_user.py add +1234567890 --name "John" --validity 30

# List users
python scripts/add_user.py list

# Update validity
python scripts/add_user.py update +1234567890 --validity 60

# Deactivate user
python scripts/add_user.py deactivate +1234567890
```

## User Messages

### Spanish (Default)

**No Access:**
> Lo sentimos, no tienes acceso a este servicio. Por favor, contacta a tu administrador para obtener acceso.

**Expired:**
> Tu período de servicio ha expirado. Tu acceso venció el 15/12/2024. Por favor, contacta a tu administrador para renovar tu suscripción.

### English

**No Access:**
> Sorry, you do not have access to this service. Please contact your administrator to get access.

**Expired:**
> Your service period has expired. Your access expired on 12/15/2024. Please contact your administrator to renew your subscription.

### Portuguese

**No Access:**
> Desculpe, você não tem acesso a este serviço. Entre em contato com seu administrador para obter acesso.

**Expired:**
> Seu período de serviço expirou. Seu acesso expirou em 15/12/2024. Entre em contato com seu administrador para renovar sua assinatura.

## Migration Steps

### For New Installations

1. Run migrations:
   ```bash
   alembic upgrade head
   ```

2. Add users:
   ```bash
   python scripts/add_user.py add +1234567890 --name "User" --validity 30
   ```

### For Existing Installations

1. **Backup database** (important!)
   ```bash
   pg_dump blinky_db > backup_$(date +%Y%m%d).sql
   ```

2. **Create and apply migration:**
   ```bash
   alembic revision --autogenerate -m "add_validity_days_to_users"
   alembic upgrade head
   ```

3. **Update existing users:**
   ```sql
   -- Set default validity for all existing users
   UPDATE users SET validity_days = 30 WHERE validity_days IS NULL;
   ```

4. **Test the system:**
   ```bash
   # List users to verify
   python scripts/add_user.py list
   
   # Test with a known user
   # Send a message and verify it works
   ```

## Behavior Changes

### Before

1. User sends message
2. System checks if user exists
3. If not, creates new user automatically
4. Processes message
5. Returns AI response

### After

1. User sends message
2. System checks if user exists
3. **If not, returns "no access" message** ❌
4. System checks if user is valid
5. **If expired, returns "expired" message** ❌
6. If valid, processes message ✅
7. Returns AI response

## Impact on Existing Users

### Automatic Users (Created Before Update)

- Will have `validity_days = 30` (default)
- Validity calculated from `created_at` date
- May already be expired if created >30 days ago
- **Action Required**: Review and extend validity as needed

### New Users (After Update)

- Must be manually added by administrator
- Cannot self-register through messaging
- Have configurable validity period
- Clear expiration dates

## Testing Checklist

- [ ] Database migration applied successfully
- [ ] Existing users have `validity_days` set
- [ ] New users can be added via script
- [ ] Valid users can send messages
- [ ] Expired users receive expiration message
- [ ] Unregistered users receive no-access message
- [ ] User list command works
- [ ] Update validity command works
- [ ] Deactivate user command works
- [ ] Messages are in correct language

## Monitoring

### Check Expiring Users

```bash
# List all users with their expiration status
python scripts/add_user.py list
```

### SQL Queries

```sql
-- Users expiring in next 7 days
SELECT 
    phone_number, 
    name, 
    created_at,
    created_at + (validity_days || ' days')::interval as expires_at,
    EXTRACT(DAY FROM (created_at + (validity_days || ' days')::interval - NOW())) as days_remaining
FROM users
WHERE created_at + (validity_days || ' days')::interval <= NOW() + interval '7 days'
  AND is_active = true
ORDER BY expires_at;

-- Expired users
SELECT 
    phone_number, 
    name, 
    created_at,
    created_at + (validity_days || ' days')::interval as expired_at
FROM users
WHERE created_at + (validity_days || ' days')::interval < NOW()
  AND is_active = true
ORDER BY expired_at DESC;

-- Active users count
SELECT 
    COUNT(*) as total_users,
    SUM(CASE WHEN created_at + (validity_days || ' days')::interval >= NOW() THEN 1 ELSE 0 END) as valid_users,
    SUM(CASE WHEN created_at + (validity_days || ' days')::interval < NOW() THEN 1 ELSE 0 END) as expired_users
FROM users
WHERE is_active = true;
```

## Security Considerations

1. **Phone Number Verification**: Ensure phone numbers are legitimate
2. **Access Logs**: Log all denied access attempts
3. **Admin Access**: Restrict user management script access
4. **Rate Limiting**: Prevent abuse from expired accounts
5. **Audit Trail**: Track user validity changes

## Future Enhancements

### Planned
- [ ] Email/SMS notifications before expiration
- [ ] Automatic renewal for paying customers
- [ ] Grace period after expiration
- [ ] Usage analytics per user
- [ ] Bulk user import from CSV

### Possible
- [ ] Tiered access levels (basic, premium, enterprise)
- [ ] Family/group accounts
- [ ] Referral system
- [ ] Payment integration
- [ ] Self-service portal for users

## Rollback Plan

If issues occur, you can rollback:

1. **Revert code changes:**
   ```bash
   git revert <commit-hash>
   ```

2. **Rollback database:**
   ```bash
   alembic downgrade -1
   ```

3. **Restore from backup:**
   ```bash
   psql blinky_db < backup_YYYYMMDD.sql
   ```

## Support

For issues or questions:
- See [USER_MANAGEMENT.md](USER_MANAGEMENT.md) for detailed user management guide
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system architecture
- Review [README.md](README.md) for setup instructions

## Documentation Files

- **USER_MANAGEMENT.md** - Complete user management guide
- **USER_VALIDATION_CHANGES.md** - This file (changes summary)
- **ARCHITECTURE.md** - System architecture
- **README.md** - General documentation
- **MIGRATION_GUIDE.md** - Migration from old version
