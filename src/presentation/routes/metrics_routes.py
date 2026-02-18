from flask import Blueprint, jsonify
from src.infrastructure.database.connection import get_db_context
from src.infrastructure.database.metric_repository_impl import MetricRepositoryImpl
from src.infrastructure.repositories.postgres_report_request_repository import PostgresReportRequestRepository
from src.application.services.metrics_service import MetricsService
from src.application.services.report_request_service import ReportRequestService
from src.presentation.controllers.metrics_controller import MetricsController
from src.presentation.controllers.report_request_controller import ReportRequestController


def create_metrics_blueprint() -> Blueprint:
    """Create and configure metrics blueprint"""
    bp = Blueprint('metrics', __name__, url_prefix='/api/metrics')
    
    # Helper function to create controller with proper session management
    def with_metrics_controller(handler_method):
        """Decorator to provide controller with proper DB session management"""
        def wrapper(*args, **kwargs):
            with get_db_context() as db:
                metric_repo = MetricRepositoryImpl(db)
                metrics_service = MetricsService(metric_repo, db)
                controller = MetricsController(metrics_service)
                return getattr(controller, handler_method)(*args, **kwargs)
        wrapper.__name__ = handler_method
        return wrapper
    
    # Helper function for report request controller
    def with_report_request_controller(handler_method):
        """Decorator to provide report request controller with proper DB session management"""
        def wrapper(*args, **kwargs):
            with get_db_context() as db:
                report_request_repo = PostgresReportRequestRepository(db)
                report_request_service = ReportRequestService(report_request_repo)
                controller = ReportRequestController(report_request_service)
                return getattr(controller, handler_method)(*args, **kwargs)
        wrapper.__name__ = handler_method
        return wrapper
    
    # Register routes with session management
    bp.route('/dashboard-home', methods=['GET'])(with_metrics_controller('get_dashboard_home_metrics'))
    bp.route('/dashboard', methods=['GET'])(with_metrics_controller('get_dashboard_summary'))
    bp.route('/response-time', methods=['GET'])(with_metrics_controller('get_response_time_stats'))
    bp.route('/response-time/hourly', methods=['GET'])(with_metrics_controller('get_response_time_by_hour'))
    bp.route('/errors', methods=['GET'])(with_metrics_controller('get_error_summary'))
    bp.route('/errors/recent', methods=['GET'])(with_metrics_controller('get_recent_errors'))
    bp.route('/volume', methods=['GET'])(with_metrics_controller('get_message_volume'))
    bp.route('/access-denied', methods=['GET'])(with_metrics_controller('get_access_denied_stats'))
    
    # New dashboard routes based on metrics-query.sql
    bp.route('/conversation-stats', methods=['GET'])(with_metrics_controller('get_conversation_stats'))
    bp.route('/all-metrics', methods=['GET'])(with_metrics_controller('get_all_metrics_with_users'))
    bp.route('/unregistered-phones', methods=['GET'])(with_metrics_controller('get_unregistered_phone_numbers'))
    bp.route('/user-stats', methods=['GET'])(with_metrics_controller('get_all_users_with_stats'))
    bp.route('/peak-hours', methods=['GET'])(with_metrics_controller('get_peak_interaction_hours'))
    bp.route('/frequent-questions', methods=['GET'])(with_metrics_controller('get_frequent_questions'))
    bp.route('/topic-clusters', methods=['GET'])(with_metrics_controller('get_topic_clusters'))
    
    # Report request endpoints
    bp.route('/reports/request', methods=['POST'])(with_report_request_controller('create_report_request'))
    bp.route('/reports/request/<request_id>', methods=['GET'])(with_report_request_controller('get_report_request'))
    bp.route('/reports/requests', methods=['GET'])(with_report_request_controller('get_all_report_requests'))
    
    return bp
