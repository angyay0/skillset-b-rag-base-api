from flask import Blueprint, jsonify
from src.config.dependencies import get_whatsapp_controller, get_voice_controller

# Create blueprints
whatsapp_bp = Blueprint('whatsapp', __name__)
voice_bp = Blueprint('voice', __name__)
health_bp = Blueprint('health', __name__)


# WhatsApp routes
@whatsapp_bp.route('/webhook', methods=['GET', 'POST'])
def webhook_meta():
    """WhatsApp Business API webhook (Meta)"""
    controller = get_whatsapp_controller()
    return controller.webhook_meta()


@whatsapp_bp.route('/whatsapp/twilio', methods=['POST'])
def webhook_twilio():
    """WhatsApp webhook via Twilio"""
    controller = get_whatsapp_controller()
    return controller.webhook_twilio()


# Voice routes
@voice_bp.route('/voice/incoming', methods=['POST'])
def voice_incoming():
    """Handle incoming voice calls"""
    controller = get_voice_controller()
    return controller.incoming()


@voice_bp.route('/voice/process', methods=['POST'])
def voice_process():
    """Process speech input"""
    controller = get_voice_controller()
    return controller.process()


@voice_bp.route('/voice/status', methods=['POST'])
def voice_status():
    """Handle call status callbacks"""
    controller = get_voice_controller()
    return controller.status()


# Health check route
@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "blinky-base-api"}), 200


def register_routes(app):
    """Register all blueprints with the app"""
    # Import here to avoid circular imports
    from src.presentation.routes.metrics_routes import create_metrics_blueprint
    from src.presentation.routes.dashboard_routes import create_dashboard_blueprint
    
    app.register_blueprint(whatsapp_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(health_bp)
    
    # Register metrics and dashboard blueprints
    metrics_bp = create_metrics_blueprint()
    dashboard_bp = create_dashboard_blueprint()
    app.register_blueprint(metrics_bp)
    app.register_blueprint(dashboard_bp)
