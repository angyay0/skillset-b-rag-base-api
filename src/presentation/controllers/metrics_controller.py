from flask import jsonify, request
from datetime import datetime, timedelta
from src.application.services.metrics_service import MetricsService


class MetricsController:
    """Controller for metrics and dashboard endpoints"""
    
    def __init__(self, metrics_service: MetricsService):
        self.metrics_service = metrics_service
    
    def get_dashboard_home_metrics(self):
        """Get dashboard home metrics with month-over-month comparison
        
        GET /api/metrics/dashboard-home
        
        Returns:
            JSON with total_messages, active_users, response_rate, satisfaction
            each with current value, change percentage, and change label
        """
        try:
            metrics = self.metrics_service.get_dashboard_home_metrics()
            return jsonify(metrics), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_dashboard_summary(self):
        """Get comprehensive dashboard summary
        
        GET /api/metrics/dashboard
        """
        try:
            summary = self.metrics_service.get_dashboard_summary()
            return jsonify(summary), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_response_time_stats(self):
        """Get response time statistics
        
        GET /api/metrics/response-time?days=7
        """
        try:
            days = int(request.args.get('days', 7))
            start_date = datetime.utcnow() - timedelta(days=days)
            end_date = datetime.utcnow()
            
            stats = self.metrics_service.get_response_time_stats(start_date, end_date)
            return jsonify(stats), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_response_time_by_hour(self):
        """Get response time grouped by hour
        
        GET /api/metrics/response-time/hourly?hours=24
        """
        try:
            hours = int(request.args.get('hours', 24))
            data = self.metrics_service.get_response_time_by_hour(hours)
            return jsonify(data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_error_summary(self):
        """Get error summary
        
        GET /api/metrics/errors?days=7
        """
        try:
            days = int(request.args.get('days', 7))
            start_date = datetime.utcnow() - timedelta(days=days)
            end_date = datetime.utcnow()
            
            summary = self.metrics_service.get_error_summary(start_date, end_date)
            return jsonify(summary), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_recent_errors(self):
        """Get recent errors
        
        GET /api/metrics/errors/recent?limit=50
        """
        try:
            limit = int(request.args.get('limit', 50))
            errors = self.metrics_service.get_recent_errors(limit)
            return jsonify(errors), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_message_volume(self):
        """Get message volume by hour
        
        GET /api/metrics/volume?hours=24
        """
        try:
            hours = int(request.args.get('hours', 24))
            data = self.metrics_service.get_message_volume(hours)
            return jsonify(data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_access_denied_stats(self):
        """Get access denied statistics
        
        GET /api/metrics/access-denied?days=7
        """
        try:
            days = int(request.args.get('days', 7))
            stats = self.metrics_service.get_access_denied_stats(days)
            return jsonify(stats), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_conversation_stats(self):
        """Get conversation stats with user names
        
        GET /api/metrics/conversation-stats
        """
        try:
            stats = self.metrics_service.get_conversation_stats()
            return jsonify(stats), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_all_metrics_with_users(self):
        """Get all metrics with user names
        
        GET /api/metrics/all-metrics
        """
        try:
            metrics = self.metrics_service.get_all_metrics_with_users()
            return jsonify(metrics), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_unregistered_phone_numbers(self):
        """Get phone numbers with no associated user
        
        GET /api/metrics/unregistered-phones
        """
        try:
            phones = self.metrics_service.get_unregistered_phone_numbers()
            return jsonify(phones), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_all_users_with_stats(self):
        """Get all users with their message and warning counts
        
        GET /api/metrics/user-stats
        """
        try:
            users = self.metrics_service.get_all_users_with_stats()
            return jsonify(users), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_peak_interaction_hours(self):
        """Get peak interaction hours throughout the day
        
        GET /api/metrics/peak-hours?from_date=2025-01-01
        """
        try:
            from_date = None
            if request.args.get('from_date'):
                from_date = datetime.fromisoformat(request.args.get('from_date'))
            
            hours = self.metrics_service.get_peak_interaction_hours(from_date)
            return jsonify(hours), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_frequent_questions(self):
        """Get most frequent questions or message patterns
        
        GET /api/metrics/frequent-questions?limit=50&from_date=2025-01-01
        """
        try:
            limit = int(request.args.get('limit', 50))
            from_date = None
            if request.args.get('from_date'):
                from_date = datetime.fromisoformat(request.args.get('from_date'))
            
            questions = self.metrics_service.get_frequent_questions(limit, from_date)
            return jsonify(questions), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_topic_clusters(self):
        """Get user messages clustered by topic using AI
        
        GET /api/metrics/topic-clusters?limit=100&from_date=2025-01-01&num_clusters=5
        """
        try:
            limit = int(request.args.get('limit', 100))
            num_clusters = int(request.args.get('num_clusters', 5))
            from_date = None
            if request.args.get('from_date'):
                from_date = datetime.fromisoformat(request.args.get('from_date'))
            
            clusters = self.metrics_service.get_topic_clusters(limit, from_date, num_clusters)
            return jsonify(clusters), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_recent_activities(self):
        """Get recent activities for dashboard list
        
        GET /api/metrics/recent-activities?limit=50
        
        Returns:
            JSON list of recent activities including messages, user registrations,
            and system events sorted by timestamp (most recent first)
        """
        try:
            limit = int(request.args.get('limit', 50))
            activities = self.metrics_service.get_recent_activities(limit)
            return jsonify({
                'activities': activities,
                'count': len(activities)
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_demographics_report(self):
        """Get comprehensive demographics report for dashboard charts
        
        GET /api/metrics/demographics
        
        Returns:
            JSON with aggregated demographics data for all fields
        """
        try:
            report = self.metrics_service.get_demographics_report()
            return jsonify(report), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_demographics_by_field(self, field: str):
        """Get demographics breakdown for a specific field
        
        GET /api/metrics/demographics/<field>
        
        Args:
            field: Demographics field (gender, age_group, department, etc.)
        
        Returns:
            JSON with breakdown data for the specified field
        """
        try:
            data = self.metrics_service.get_demographics_by_field(field)
            if 'error' in data:
                return jsonify(data), 400
            return jsonify(data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_demographics_cross_analysis(self):
        """Get cross-analysis between two demographics fields
        
        GET /api/metrics/demographics/cross-analysis?field1=gender&field2=department
        
        Returns:
            JSON with cross-tabulation data for heatmap visualization
        """
        try:
            field1 = request.args.get('field1')
            field2 = request.args.get('field2')
            
            if not field1 or not field2:
                return jsonify({'error': 'Both field1 and field2 are required'}), 400
            
            data = self.metrics_service.get_demographics_cross_analysis(field1, field2)
            if 'error' in data:
                return jsonify(data), 400
            return jsonify(data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
