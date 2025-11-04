# Migration Guide: From Monolithic to Clean Architecture

## Overview

The application has been refactored from a single `app.py` file to a clean architecture structure with proper separation of concerns and PostgreSQL database integration.

## What Changed

### Before (app.py)
- Single file with all logic
- In-memory conversation storage
- No database persistence
- Tightly coupled components
- Difficult to test and maintain

### After (app_new.py + src/)
- Clean architecture with 4 layers
- PostgreSQL database for persistence
- Repository pattern for data access
- Dependency injection
- Testable and maintainable

## File Mapping

| Old Location | New Location | Purpose |
|-------------|--------------|---------|
| `app.py` (all) | `app_new.py` | Application entry point |
| `app.py` (routes) | `src/presentation/routes.py` | Route definitions |
| `app.py` (WhatsApp logic) | `src/presentation/controllers/whatsapp_controller.py` | WhatsApp handlers |
| `app.py` (Voice logic) | `src/presentation/controllers/voice_controller.py` | Voice call handlers |
| `app.py` (AI logic) | `src/infrastructure/ai/vertex_ai_service.py` | AI service |
| `app.py` (conversations dict) | `src/infrastructure/database/models.py` | Database models |
| N/A | `src/domain/entities/` | Business entities |
| N/A | `src/domain/repositories/` | Repository interfaces |
| N/A | `src/application/services/` | Business logic |

## Database Schema

### New Tables

**users**
- Stores user information (phone number, language, preferences)
- Replaces in-memory user tracking

**conversations**
- Tracks conversations by user and channel
- Replaces `conversations` dictionary

**messages**
- Stores all messages and responses
- Provides conversation history
- Replaces in-memory message storage

## Migration Steps

### 1. Install New Dependencies

```bash
pip install -r requirements.txt
```

New packages:
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL driver
- `alembic` - Database migrations

### 2. Set Up Database

```bash
# Create database
createdb blinky_db

# Update .env with DATABASE_URL
DATABASE_URL=postgresql://user:password@localhost:5432/blinky_db

# Run migrations
alembic upgrade head
```

### 3. Update Environment Variables

Add to `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/blinky_db
SQL_ECHO=false
```

### 4. Test the New Application

```bash
# Run the new app
python app_new.py

# Test endpoints
curl http://localhost:5003/health
```

### 5. Deploy

Update your deployment to use `app_new.py`:

```bash
# Dockerfile already updated
docker build -t blinky-base-api .

# Cloud Run
gcloud run deploy blinky-base-api --source .
```

## Breaking Changes

### None for External APIs
- All endpoints remain the same
- WhatsApp and Voice webhooks work identically
- No changes needed to Twilio/Meta configuration

### Internal Changes
- Conversation data now persists in database
- Users are automatically created on first message
- Message history is stored permanently

## Benefits

### Data Persistence
- Conversations survive server restarts
- Full message history available
- User preferences stored

### Scalability
- Multiple instances can share database
- Horizontal scaling possible
- No data loss on deployment

### Maintainability
- Clear separation of concerns
- Easy to add new features
- Testable components

### Observability
- Database queries for analytics
- User engagement tracking
- Conversation metrics

## Rollback Plan

If needed, you can rollback to the old version:

1. Keep `app.py` as backup
2. Change Dockerfile CMD back to `app:app`
3. Redeploy

Note: You'll lose database-stored conversations.

## Testing Checklist

- [ ] Database connection works
- [ ] WhatsApp messages are received and stored
- [ ] Voice calls work correctly
- [ ] Conversation history is retrieved
- [ ] Users are created automatically
- [ ] Health check endpoint responds
- [ ] All environment variables are set

## Support

For issues or questions:
1. Check `ARCHITECTURE.md` for design details
2. Review `README.md` for setup instructions
3. Check database logs for connection issues
4. Verify all environment variables are set

## Next Steps

1. **Add monitoring**: Implement logging and metrics
2. **Add tests**: Write unit and integration tests
3. **Add admin API**: Create endpoints for user management
4. **Add analytics**: Track usage and engagement
5. **Optimize queries**: Add indexes and caching
