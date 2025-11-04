"""
Example: How to integrate metrics routes into your Flask application

Add this code to your main Flask app file (e.g., app.py or app_new.py)
"""

from flask import Flask
from flask_cors import CORS
from src.presentation.routes.metrics_routes import create_metrics_blueprint

# Create Flask app
app = Flask(__name__)
CORS(app)

# ... your existing routes and configuration ...

# Register metrics blueprint
metrics_bp = create_metrics_blueprint()
app.register_blueprint(metrics_bp)

# Now your metrics endpoints are available at:
# - GET /api/metrics/dashboard
# - GET /api/metrics/response-time
# - GET /api/metrics/response-time/hourly
# - GET /api/metrics/errors
# - GET /api/metrics/errors/recent
# - GET /api/metrics/volume
# - GET /api/metrics/access-denied

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
