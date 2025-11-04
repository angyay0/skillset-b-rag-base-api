from flask import Blueprint, send_from_directory
import os

def create_dashboard_blueprint() -> Blueprint:
    """Create and configure dashboard blueprint for serving static files"""
    bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
    
    # Get the dashboard directory path
    dashboard_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        'dashboard'
    )
    
    @bp.route('/')
    def index():
        """Serve the dashboard index page"""
        return send_from_directory(dashboard_dir, 'index.html')
    
    @bp.route('/<path:filename>')
    def serve_file(filename):
        """Serve dashboard static files"""
        return send_from_directory(dashboard_dir, filename)
    
    return bp
