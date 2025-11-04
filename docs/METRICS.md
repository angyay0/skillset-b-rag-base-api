# Metrics and Dashboard System

This document describes the metrics tracking system implemented for monitoring chat service performance and errors.

## Overview

The metrics system captures:
1. **Response Time**: Time taken to generate AI responses (stored in `messages.response_time_ms`)
2. **Errors and Events**: Important events like errors, access denials, expired users (stored in `metrics` table)

## Database Schema

### Messages Table
- Added `response_time_ms` (INTEGER): Time in milliseconds to generate the AI response

### Metrics Table
New table for tracking errors and important events:
- `id`: Primary key
- `metric_type`: Type of metric (error, warning, info, access_denied, expired_user, ai_error)
- `severity`: Severity level (low, medium, high, critical)
- `message`: Description of the event
- `user_id`: Associated user (nullable)
- `conversation_id`: Associated conversation (nullable)
- `phone_number`: Phone number (for cases where user doesn't exist)
- `channel`: Communication channel (whatsapp, voice, etc.)
- `error_details`: JSON field with additional details (stack traces, error codes, etc.)
- `created_at`: Timestamp

## Running the Migration

To apply the database changes:

```bash
# Activate virtual environment
source venv/bin/activate

# Run migration
alembic upgrade head
```

## API Endpoints

All metrics endpoints are under `/api/metrics`:

### Dashboard Summary
```
GET /api/metrics/dashboard
```
Returns comprehensive metrics including:
- Message volume (last 24h)
- Response time statistics
- Error summary (last 7 days)
- Access denied attempts
- Slow responses count

**Response Example:**
```json
{
  "period": {
    "start": "2025-11-04T00:00:00",
    "end": "2025-11-05T00:00:00"
  },
  "messages": {
    "total_24h": 1250,
    "slow_responses_24h": 15
  },
  "response_time": {
    "count": 1250,
    "avg_ms": 1850,
    "min_ms": 450,
    "max_ms": 8200,
    "p50_ms": 1600,
    "p95_ms": 3500,
    "p99_ms": 5200
  },
  "errors": {
    "by_type": {
      "error": 5,
      "warning": 12,
      "access_denied": 8
    },
    "by_severity": {
      "high": 5,
      "medium": 20
    },
    "total": 25
  },
  "access_denied": {
    "total_attempts": 8,
    "unique_numbers": 5,
    "top_numbers": [["+1234567890", 3], ["+0987654321", 2]]
  }
}
```

### Response Time Statistics
```
GET /api/metrics/response-time?days=7
```
Query parameters:
- `days` (optional, default: 7): Number of days to look back

Returns statistics on response times including average, min, max, and percentiles.

### Response Time by Hour
```
GET /api/metrics/response-time/hourly?hours=24
```
Query parameters:
- `hours` (optional, default: 24): Number of hours to look back

Returns hourly breakdown of average response times.

**Response Example:**
```json
[
  {
    "hour": "2025-11-04T20:00:00",
    "avg_ms": 1850,
    "count": 45
  },
  {
    "hour": "2025-11-04T21:00:00",
    "avg_ms": 2100,
    "count": 52
  }
]
```

### Error Summary
```
GET /api/metrics/errors?days=7
```
Query parameters:
- `days` (optional, default: 7): Number of days to look back

Returns error counts grouped by type and severity.

### Recent Errors
```
GET /api/metrics/errors/recent?limit=50
```
Query parameters:
- `limit` (optional, default: 50): Maximum number of errors to return

Returns list of recent errors with full details.

**Response Example:**
```json
[
  {
    "id": 123,
    "type": "error",
    "severity": "high",
    "message": "Error processing message: Connection timeout",
    "phone_number": "+1234567890",
    "channel": "whatsapp",
    "error_details": {
      "error": "Connection timeout",
      "traceback": "...",
      "message_text": "Hello, I need help with..."
    },
    "created_at": "2025-11-04T22:15:30"
  }
]
```

### Message Volume
```
GET /api/metrics/volume?hours=24
```
Query parameters:
- `hours` (optional, default: 24): Number of hours to look back

Returns message count grouped by hour.

### Access Denied Statistics
```
GET /api/metrics/access-denied?days=7
```
Query parameters:
- `days` (optional, default: 7): Number of days to look back

Returns statistics on access denied attempts.

## Metric Types

### Automatically Tracked Events

1. **access_denied** (severity: medium)
   - Triggered when: User without access tries to use the service
   - Includes: phone_number, channel

2. **expired_user** (severity: medium)
   - Triggered when: User with expired access tries to use the service
   - Includes: user_id, phone_number, channel

3. **warning** (severity: medium)
   - Triggered when: AI response takes > 5 seconds
   - Includes: user_id, conversation_id, phone_number, channel, response_time_ms

4. **error** (severity: high)
   - Triggered when: Exception occurs during message processing
   - Includes: Full error details, stack trace, user context

## Using Metrics in Your Dashboard

### Example: Building a Dashboard

```python
from src.config.dependencies import get_metrics_service

# Get metrics service
metrics_service = get_metrics_service()

# Get dashboard summary
summary = metrics_service.get_dashboard_summary()

# Get response time trends
hourly_response_times = metrics_service.get_response_time_by_hour(hours=24)

# Get recent errors
recent_errors = metrics_service.get_recent_errors(limit=20)
```

### Key Metrics to Monitor

1. **Average Response Time**: Should stay under 3 seconds
2. **P95 Response Time**: Should stay under 5 seconds
3. **Error Rate**: Monitor for spikes
4. **Access Denied Attempts**: May indicate unauthorized access attempts
5. **Message Volume**: Track usage patterns

## Performance Considerations

- All metrics queries are indexed for performance
- Response time data is stored directly in the messages table for fast access
- Metrics table uses indexes on: metric_type, severity, user_id, conversation_id, phone_number, created_at
- Consider archiving old metrics data after 90 days

## Future Enhancements

Potential additions:
- User satisfaction metrics
- Channel-specific performance tracking
- Geographic distribution of requests
- Peak usage time analysis
- Cost tracking per message
