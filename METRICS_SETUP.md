# Metrics System Setup Guide

## Quick Start

### 1. Run Database Migration

```bash
# Activate virtual environment
source venv/bin/activate

# Apply the migration
alembic upgrade head
```

This will:
- Add `response_time_ms` column to the `messages` table
- Create the `metrics` table with all necessary indexes

### 2. Register Metrics Routes (if using Flask app)

Add to your main Flask application file:

```python
from src.presentation.routes.metrics_routes import create_metrics_blueprint

# Register metrics blueprint
app.register_blueprint(create_metrics_blueprint())
```

### 3. Verify Setup

Check that the migration was successful:

```bash
# Connect to your database and verify tables
psql -d your_database_name

# Check messages table has response_time_ms column
\d messages

# Check metrics table exists
\d metrics
```

## What Was Implemented

### 1. Response Time Tracking
- **Location**: `messages.response_time_ms` column
- **Captured**: Automatically in `ChatService.process_message()`
- **Measured**: Time from AI request start to response received
- **Unit**: Milliseconds

### 2. Metrics Table
Tracks important events:
- **Errors**: Exceptions during message processing
- **Warnings**: Slow responses (>5 seconds)
- **Access Denied**: Unauthorized access attempts
- **Expired Users**: Expired user access attempts

### 3. API Endpoints
All available at `/api/metrics/*`:
- `/dashboard` - Comprehensive summary
- `/response-time` - Response time statistics
- `/response-time/hourly` - Hourly breakdown
- `/errors` - Error summary
- `/errors/recent` - Recent error list
- `/volume` - Message volume by hour
- `/access-denied` - Access denial statistics

### 4. Services Created
- **MetricsService**: Business logic for querying metrics
- **MetricRepository**: Data access layer
- **MetricsController**: HTTP endpoint handlers

## Files Modified/Created

### Modified Files
1. `src/domain/entities/conversation.py` - Added `response_time_ms` to Message entity
2. `src/infrastructure/database/models.py` - Added `response_time_ms` column and MetricModel
3. `src/application/services/chat_service.py` - Added timing and metrics logging
4. `src/infrastructure/repositories/postgres_conversation_repository.py` - Handle response_time_ms
5. `src/config/dependencies.py` - Added metric repository injection

### New Files
1. `src/domain/entities/metric.py` - Metric entity
2. `src/domain/repositories/metric_repository.py` - Metric repository interface
3. `src/infrastructure/database/metric_repository_impl.py` - PostgreSQL implementation
4. `src/application/services/metrics_service.py` - Metrics business logic
5. `src/presentation/controllers/metrics_controller.py` - HTTP controller
6. `src/presentation/routes/metrics_routes.py` - Route definitions
7. `alembic/versions/2025_11_04_2326-de9d8414ebac_add_metrics_and_response_time.py` - Migration
8. `docs/METRICS.md` - Full documentation

## Testing the Implementation

### Test Response Time Tracking

Send a message through your service and check the database:

```sql
SELECT 
    id, 
    user_message, 
    response_time_ms, 
    created_at 
FROM messages 
ORDER BY created_at DESC 
LIMIT 10;
```

### Test Metrics Logging

Try accessing with an invalid phone number and check:

```sql
SELECT * FROM metrics 
WHERE metric_type = 'access_denied' 
ORDER BY created_at DESC 
LIMIT 5;
```

### Test API Endpoints

```bash
# Get dashboard summary
curl http://localhost:5000/api/metrics/dashboard

# Get response time stats
curl http://localhost:5000/api/metrics/response-time?days=7

# Get recent errors
curl http://localhost:5000/api/metrics/errors/recent?limit=10
```

## Dashboard Integration

### Example: Simple Dashboard Query

```python
from src.config.dependencies import get_metrics_service

metrics_service = get_metrics_service()

# Get comprehensive summary
summary = metrics_service.get_dashboard_summary()

print(f"Messages (24h): {summary['messages']['total_24h']}")
print(f"Avg Response Time: {summary['response_time']['avg_ms']}ms")
print(f"Total Errors (7d): {summary['errors']['total']}")
```

### Example: Response Time Chart Data

```python
# Get hourly response times for last 24 hours
hourly_data = metrics_service.get_response_time_by_hour(hours=24)

# Format for chart library
chart_data = {
    'labels': [item['hour'] for item in hourly_data],
    'values': [item['avg_ms'] for item in hourly_data]
}
```

## Monitoring Recommendations

### Key Metrics to Watch

1. **Average Response Time** 
   - Target: < 2000ms
   - Warning: > 3000ms
   - Critical: > 5000ms

2. **P95 Response Time**
   - Target: < 3000ms
   - Warning: > 5000ms
   - Critical: > 8000ms

3. **Error Rate**
   - Target: < 1%
   - Warning: > 2%
   - Critical: > 5%

4. **Access Denied Attempts**
   - Monitor for patterns
   - May indicate security issues

### Alerting Setup

Consider setting up alerts for:
- Response time P95 > 5 seconds
- Error count > 10 in 1 hour
- Access denied attempts > 20 in 1 hour

## Troubleshooting

### Migration Issues

If migration fails:
```bash
# Check current revision
alembic current

# Check migration history
alembic history

# Rollback if needed
alembic downgrade -1
```

### Missing Metrics

If metrics aren't being recorded:
1. Check that `metric_repo` is passed to `ChatService`
2. Verify database connection
3. Check application logs for errors

### Performance Issues

If queries are slow:
1. Verify indexes exist: `\di metrics`
2. Consider archiving old data
3. Add date range filters to queries

## Next Steps

1. **Run the migration**: `alembic upgrade head`
2. **Register routes**: Add metrics blueprint to your Flask app
3. **Test endpoints**: Verify API responses
4. **Build dashboard**: Use the API endpoints to create visualizations
5. **Set up monitoring**: Configure alerts for critical metrics

For detailed API documentation, see `docs/METRICS.md`.
