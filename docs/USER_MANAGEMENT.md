# User Management Guide

## Overview

The Blinky Base API now includes user validation and access control. Users must be registered in the database before they can use the service, and each user has a validity period (default: 30 days).

## User Validity System

### How It Works

1. **User Registration**: Users must be added to the database by an administrator
2. **Validity Period**: Each user has a validity period (default: 30 days from creation)
3. **Access Control**: Only valid users can interact with the chatbot
4. **Automatic Validation**: Every message checks if the user is valid

### User States

- **Valid**: User is active and within validity period
- **Expired**: User's validity period has ended
- **Inactive**: User has been manually deactivated
- **Not Registered**: Phone number not in database

## User Management Script

### Add a New User

```bash
# Basic usage (30 days validity)
python scripts/add_user.py add +1234567890

# With name and custom validity
python scripts/add_user.py add +1234567890 --name "John Doe" --validity 60

# With language preference
python scripts/add_user.py add +1234567890 --name "María García" --language es --validity 90
```

**Parameters:**
- `phone`: Phone number with country code (required)
- `--name`: User's name (optional)
- `--language`: Language preference - es, en, pt (default: es)
- `--validity`: Validity period in days (default: 30)

### List All Users

```bash
python scripts/add_user.py list
```

**Output:**
```
📋 Total users: 3

ID    Phone                Name                 Language   Valid Days   Days Left    Status    
----------------------------------------------------------------------------------------------------
1     +1234567890          John Doe             es         30           25           ✓ Active  
2     +9876543210          María García         es         60           55           ✓ Active  
3     +5555555555          Test User            en         30           -5           ✗ Expired 
```

### Update User Validity

```bash
# Extend validity to 60 days
python scripts/add_user.py update +1234567890 --validity 60

# Extend to 90 days
python scripts/add_user.py update +1234567890 --validity 90
```

**Note:** The validity period is calculated from the user's creation date, not from the update date.

### Deactivate a User

```bash
python scripts/add_user.py deactivate +1234567890
```

This immediately blocks access regardless of validity period.

## User Messages

### No Access (User Not Registered)

**Spanish:**
> Lo sentimos, no tienes acceso a este servicio. Por favor, contacta a tu administrador para obtener acceso.

**English:**
> Sorry, you do not have access to this service. Please contact your administrator to get access.

**Portuguese:**
> Desculpe, você não tem acesso a este serviço. Entre em contato com seu administrador para obter acesso.

### Expired Access

**Spanish:**
> Tu período de servicio ha expirado. Tu acceso venció el 15/12/2024. Por favor, contacta a tu administrador para renovar tu suscripción.

**English:**
> Your service period has expired. Your access expired on 12/15/2024. Please contact your administrator to renew your subscription.

**Portuguese:**
> Seu período de serviço expirou. Seu acesso expirou em 15/12/2024. Entre em contato com seu administrador para renovar sua assinatura.

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    language VARCHAR(10) DEFAULT 'es',
    validity_days INTEGER DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Key Fields

- **validity_days**: Number of days the user has access from creation date
- **is_active**: Manual override to disable access
- **created_at**: Used to calculate expiration date

## User Entity Methods

### `is_valid() -> bool`

Checks if user is within valid service period:
- Returns `False` if `is_active` is `False`
- Returns `False` if current date > (created_at + validity_days)
- Returns `True` otherwise

```python
user = user_repo.get_by_phone("+1234567890")
if user.is_valid():
    # Process message
else:
    # Return expired message
```

### `days_remaining() -> int`

Returns number of days remaining in service period:
- Returns 0 if expired
- Returns positive number if still valid

```python
days_left = user.days_remaining()
print(f"User has {days_left} days remaining")
```

### `expiration_date() -> datetime`

Returns the exact expiration date:

```python
expiry = user.expiration_date()
print(f"User access expires on {expiry.strftime('%Y-%m-%d')}")
```

## Integration with Chat Service

### Message Processing Flow

1. **Receive Message**: WhatsApp or Voice message arrives
2. **Check User Exists**: Look up user by phone number
   - If not found → Return "no access" message
3. **Check Validity**: Call `user.is_valid()`
   - If expired → Return "expired" message
4. **Process Message**: Generate AI response and save
5. **Return Response**: Send response to user

### Code Example

```python
def process_message(self, phone_number: str, message_text: str, channel: str):
    # Get user
    user = self.user_repo.get_by_phone(phone_number)
    if not user:
        return self._get_no_access_message(language)
    
    # Check validity
    if not user.is_valid():
        return self._get_expired_message(language, user)
    
    # Process message normally
    # ...
```

## Best Practices

### For Administrators

1. **Regular Monitoring**: Check user list regularly for expiring accounts
2. **Proactive Renewal**: Extend validity before expiration
3. **Clear Communication**: Inform users about expiration dates
4. **Consistent Validity**: Use standard periods (30, 60, 90 days)

### For Developers

1. **Always Check Validity**: Never skip user validation
2. **Clear Error Messages**: Provide helpful messages in user's language
3. **Log Access Attempts**: Track denied access for monitoring
4. **Handle Edge Cases**: Account for timezone differences

## Migration from Old System

### Before (Automatic User Creation)

```python
# Old behavior
user = self.user_repo.get_by_phone(phone_number)
if not user:
    user = self._create_user(phone_number, language)  # Auto-create
```

### After (Validation Required)

```python
# New behavior
user = self.user_repo.get_by_phone(phone_number)
if not user:
    return self._get_no_access_message(language)  # Deny access

if not user.is_valid():
    return self._get_expired_message(language, user)  # Check validity
```

## Automation Ideas

### Expiration Notifications

Create a cron job to notify users before expiration:

```bash
# Check users expiring in 7 days
python scripts/check_expiring_users.py --days 7
```

### Auto-Renewal

Implement automatic renewal for paying customers:

```python
def renew_user(phone_number: str, additional_days: int):
    user = user_repo.get_by_phone(phone_number)
    user.validity_days += additional_days
    user_repo.update(user)
```

### Bulk Import

Import users from CSV:

```bash
# CSV format: phone,name,language,validity_days
python scripts/bulk_import_users.py users.csv
```

## Troubleshooting

### User Can't Access Service

1. Check if user exists: `python scripts/add_user.py list`
2. Check validity: Look at "Days Left" column
3. Check if active: Ensure not deactivated
4. Check phone number format: Must match exactly

### User Shows as Expired But Should Be Valid

1. Check `created_at` date in database
2. Verify `validity_days` value
3. Check server timezone settings
4. Recalculate: expiration = created_at + validity_days

### Migration Issues

If you have existing users without `validity_days`:

```sql
-- Update all existing users to 30 days validity
UPDATE users SET validity_days = 30 WHERE validity_days IS NULL;
```

## Security Considerations

1. **Phone Number Verification**: Ensure phone numbers are verified
2. **Access Logs**: Log all access attempts and denials
3. **Rate Limiting**: Prevent abuse from expired accounts
4. **Admin Access**: Restrict user management to authorized admins

## Future Enhancements

- [ ] Email notifications for expiring accounts
- [ ] Payment integration for automatic renewal
- [ ] Grace period after expiration
- [ ] Usage analytics per user
- [ ] Tiered access levels
- [ ] Family/group accounts
- [ ] Referral system
