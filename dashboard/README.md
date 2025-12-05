# Blinky Metrics Dashboard

A real-time dashboard for monitoring Blinky's metrics and performance.

## Features

### Summary Cards
- **Total Messages (24h)**: Total number of messages in the last 24 hours
- **Avg Response Time**: Average response time in milliseconds
- **Total Errors (7d)**: Total errors in the last 7 days
- **Access Denied**: Unique phone numbers with access denied

### Interactive Charts
1. **Peak Interaction Hours**: Bar chart showing interactions and unique users by hour
2. **Message Volume (24h)**: Line chart of message volume over the last 24 hours
3. **Response Time by Hour**: Line chart showing average response times
4. **Errors by Type**: Doughnut chart of error distribution by type
5. **Errors by Severity**: Bar chart of errors by severity level
6. **Response Time Distribution**: Bar chart showing min, p50, avg, p95, p99, and max response times

### Data Tables
- **User Statistics**: Top 10 users by message count with warning counts
- **Unregistered Phone Numbers**: Phone numbers attempting access without registration
- **Recent Errors**: Latest 20 errors with full details

## Setup

### 1. Configure API Endpoint

Edit `dashboard.js` and update the API base URL if needed:

```javascript
const API_BASE_URL = 'http://localhost:5000/api/metrics';
```

### 2. Serve the Dashboard

You can serve the dashboard using any static file server. Here are a few options:

#### Option A: Python HTTP Server
```bash
cd dashboard
python3 -m http.server 8080
```

Then open: http://localhost:8080

#### Option B: Node.js HTTP Server
```bash
npm install -g http-server
cd dashboard
http-server -p 8080
```

Then open: http://localhost:8080

#### Option C: Flask Integration

Add this to your Flask app to serve the dashboard:

```python
from flask import send_from_directory

@app.route('/dashboard')
def dashboard():
    return send_from_directory('dashboard', 'index.html')

@app.route('/dashboard/<path:path>')
def dashboard_files(path):
    return send_from_directory('dashboard', path)
```

### 3. Enable CORS (if needed)

If your API and dashboard are on different ports, you'll need to enable CORS in your Flask app:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
```

Or install flask-cors:
```bash
pip install flask-cors
```

## API Endpoints Used

The dashboard consumes the following endpoints:

- `GET /api/metrics/dashboard` - Dashboard summary
- `GET /api/metrics/peak-hours` - Peak interaction hours
- `GET /api/metrics/volume?hours=24` - Message volume
- `GET /api/metrics/response-time/hourly?hours=24` - Response time by hour
- `GET /api/metrics/errors?days=7` - Error summary
- `GET /api/metrics/user-stats` - User statistics
- `GET /api/metrics/unregistered-phones` - Unregistered phone numbers
- `GET /api/metrics/errors/recent?limit=20` - Recent errors

## Features

- **Auto-refresh**: Dashboard automatically refreshes every 60 seconds
- **Manual refresh**: Click the refresh button to update immediately
- **Responsive design**: Works on desktop, tablet, and mobile devices
- **Real-time updates**: All data is fetched from live API endpoints

## Browser Compatibility

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Troubleshooting

### Dashboard shows "Loading..." indefinitely
- Check that your Flask API is running
- Verify the API_BASE_URL in dashboard.js is correct
- Check browser console for CORS or network errors

### CORS errors
- Install and configure flask-cors in your Flask app
- Or serve the dashboard from the same domain as your API

### Charts not displaying
- Ensure Chart.js CDN is accessible
- Check browser console for JavaScript errors
