from flask import Blueprint
from src.config.dependencies import get_metrics_service
from src.presentation.controllers.metrics_controller import MetricsController


def create_metrics_blueprint() -> Blueprint:
    """Create and configure metrics blueprint"""
    bp = Blueprint('metrics', __name__, url_prefix='/api/metrics')
    
    # Initialize controller
    metrics_service = get_metrics_service()
    controller = MetricsController(metrics_service)
    
    # Register routes
    bp.route('/dashboard', methods=['GET'])(controller.get_dashboard_summary)
    bp.route('/response-time', methods=['GET'])(controller.get_response_time_stats)
    bp.route('/response-time/hourly', methods=['GET'])(controller.get_response_time_by_hour)
    bp.route('/errors', methods=['GET'])(controller.get_error_summary)
    bp.route('/errors/recent', methods=['GET'])(controller.get_recent_errors)
    bp.route('/volume', methods=['GET'])(controller.get_message_volume)
    bp.route('/access-denied', methods=['GET'])(controller.get_access_denied_stats)
    
    # New dashboard routes based on metrics-query.sql
    bp.route('/conversation-stats', methods=['GET'])(controller.get_conversation_stats)
    bp.route('/all-metrics', methods=['GET'])(controller.get_all_metrics_with_users)
    bp.route('/unregistered-phones', methods=['GET'])(controller.get_unregistered_phone_numbers)
    bp.route('/user-stats', methods=['GET'])(controller.get_all_users_with_stats)
    bp.route('/peak-hours', methods=['GET'])(controller.get_peak_interaction_hours)
    
    return bp
