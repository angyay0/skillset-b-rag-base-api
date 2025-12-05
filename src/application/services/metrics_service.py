from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from src.domain.entities.metric import Metric
from src.domain.repositories.metric_repository import MetricRepository
from src.infrastructure.database.models import MessageModel, MetricModel, UserModel, ConversationModel


class MetricsService:
    """Service for querying and analyzing metrics for dashboard display"""
    
    def __init__(self, metric_repo: MetricRepository, db_session: Session):
        self.metric_repo = metric_repo
        self.db = db_session
    
    def get_response_time_stats(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """Get response time statistics
        
        Returns:
            dict with avg, min, max, p50, p95, p99 response times in milliseconds
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Query messages with response times
        query = self.db.query(MessageModel.response_time_ms)\
            .filter(MessageModel.response_time_ms.isnot(None))\
            .filter(MessageModel.created_at >= start_date)\
            .filter(MessageModel.created_at <= end_date)
        
        response_times = [rt[0] for rt in query.all()]
        
        if not response_times:
            return {
                'count': 0,
                'avg_ms': 0,
                'min_ms': 0,
                'max_ms': 0,
                'p50_ms': 0,
                'p95_ms': 0,
                'p99_ms': 0
            }
        
        response_times.sort()
        count = len(response_times)
        
        return {
            'count': count,
            'avg_ms': int(sum(response_times) / count),
            'min_ms': response_times[0],
            'max_ms': response_times[-1],
            'p50_ms': response_times[int(count * 0.50)],
            'p95_ms': response_times[int(count * 0.95)],
            'p99_ms': response_times[int(count * 0.99)]
        }
    
    def get_response_time_by_hour(self, hours: int = 24) -> List[Dict]:
        """Get average response time grouped by hour
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of dicts with hour and avg_response_time_ms
        """
        start_date = datetime.utcnow() - timedelta(hours=hours)
        
        results = self.db.query(
            func.date_trunc('hour', MessageModel.created_at).label('hour'),
            func.avg(MessageModel.response_time_ms).label('avg_ms'),
            func.count(MessageModel.id).label('count')
        )\
            .filter(MessageModel.response_time_ms.isnot(None))\
            .filter(MessageModel.created_at >= start_date)\
            .group_by(func.date_trunc('hour', MessageModel.created_at))\
            .order_by(func.date_trunc('hour', MessageModel.created_at))\
            .all()
        
        return [
            {
                'hour': result.hour.isoformat(),
                'avg_ms': int(result.avg_ms) if result.avg_ms else 0,
                'count': result.count
            }
            for result in results
        ]
    
    def get_error_summary(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """Get error summary statistics
        
        Returns:
            dict with error counts by type and severity
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Count by type
        by_type = self.metric_repo.get_error_count_by_type(start_date, end_date)
        
        # Count by severity
        by_severity_results = self.db.query(
            MetricModel.severity,
            func.count(MetricModel.id).label('count')
        )\
            .filter(MetricModel.created_at >= start_date)\
            .filter(MetricModel.created_at <= end_date)\
            .group_by(MetricModel.severity)\
            .all()
        
        by_severity = {result.severity: result.count for result in by_severity_results}
        
        return {
            'by_type': by_type,
            'by_severity': by_severity,
            'total': sum(by_type.values())
        }
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict]:
        """Get recent errors with details
        
        Returns:
            List of error dictionaries
        """
        metrics = self.metric_repo.get_recent_errors(limit)
        
        return [
            {
                'id': m.id,
                'type': m.metric_type,
                'severity': m.severity,
                'message': m.message,
                'phone_number': m.phone_number,
                'channel': m.channel,
                'error_details': m.error_details,
                'created_at': m.created_at.isoformat() if m.created_at else None
            }
            for m in metrics
        ]
    
    def get_access_denied_stats(self, days: int = 7) -> Dict:
        """Get statistics on access denied attempts
        
        Returns:
            dict with count and list of phone numbers
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        metrics = self.db.query(MetricModel)\
            .filter(MetricModel.metric_type == 'access_denied')\
            .filter(MetricModel.created_at >= start_date)\
            .all()
        
        phone_numbers = {}
        for m in metrics:
            if m.phone_number:
                phone_numbers[m.phone_number] = phone_numbers.get(m.phone_number, 0) + 1
        
        return {
            'total_attempts': len(metrics),
            'unique_numbers': len(phone_numbers),
            'top_numbers': sorted(phone_numbers.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    
    def get_message_volume(self, hours: int = 24) -> List[Dict]:
        """Get message volume grouped by hour
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of dicts with hour and message count
        """
        start_date = datetime.utcnow() - timedelta(hours=hours)
        
        results = self.db.query(
            func.date_trunc('hour', MessageModel.created_at).label('hour'),
            func.count(MessageModel.id).label('count')
        )\
            .filter(MessageModel.created_at >= start_date)\
            .group_by(func.date_trunc('hour', MessageModel.created_at))\
            .order_by(func.date_trunc('hour', MessageModel.created_at))\
            .all()
        
        return [
            {
                'hour': result.hour.isoformat(),
                'count': result.count
            }
            for result in results
        ]
    
    def get_dashboard_summary(self) -> Dict:
        """Get comprehensive dashboard summary
        
        Returns:
            dict with all key metrics for dashboard display
        """
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Response time stats (last 24h)
        response_stats_24h = self.get_response_time_stats(last_24h, now)
        
        # Error summary (last 7 days)
        error_summary = self.get_error_summary(last_7d, now)
        
        # Message volume (last 24h)
        message_count_24h = self.db.query(func.count(MessageModel.id))\
            .filter(MessageModel.created_at >= last_24h)\
            .scalar()
        
        # Access denied stats (last 7 days)
        access_denied = self.get_access_denied_stats(7)
        
        # Slow responses (>5s in last 24h)
        slow_responses = self.db.query(func.count(MessageModel.id))\
            .filter(MessageModel.created_at >= last_24h)\
            .filter(MessageModel.response_time_ms > 5000)\
            .scalar()
        
        return {
            'period': {
                'start': last_24h.isoformat(),
                'end': now.isoformat()
            },
            'messages': {
                'total_24h': message_count_24h,
                'slow_responses_24h': slow_responses
            },
            'response_time': response_stats_24h,
            'errors': error_summary,
            'access_denied': access_denied
        }
    
    def get_conversation_stats(self) -> List[Dict]:
        """Get conversation stats with user names
        
        Returns:
            List of dicts with user name, phone number, total messages, and warnings
        """
        # Query based on first SQL query in metrics-query.sql
        results = self.db.query(
            UserModel.name,
            UserModel.phone_number,
            func.count(MessageModel.id).label('total_messages'),
            func.count(MetricModel.id).label('warnings')
        )\
            .join(ConversationModel, ConversationModel.user_id == UserModel.id)\
            .join(MessageModel, MessageModel.conversation_id == ConversationModel.id)\
            .outerjoin(MetricModel, MetricModel.conversation_id == ConversationModel.id)\
            .group_by(UserModel.id, UserModel.name, UserModel.phone_number)\
            .all()
        
        return [
            {
                'name': result.name,
                'phone_number': result.phone_number,
                'total_messages': result.total_messages,
                'warnings': result.warnings
            }
            for result in results
        ]
    
    def get_all_metrics_with_users(self) -> List[Dict]:
        """Get all metrics with user names
        
        Returns:
            List of dicts with user name, metric type, severity, and description
        """
        # Query based on second SQL query in metrics-query.sql
        results = self.db.query(
            UserModel.name,
            MetricModel.metric_type,
            MetricModel.severity,
            MetricModel.message.label('description')
        )\
            .join(UserModel, UserModel.id == MetricModel.user_id)\
            .all()
        
        return [
            {
                'name': result.name,
                'metric_type': result.metric_type,
                'severity': result.severity,
                'description': result.description
            }
            for result in results
        ]
    
    def get_unregistered_phone_numbers(self) -> List[Dict]:
        """Get phone numbers with no associated user
        
        Returns:
            List of dicts with phone number, attempt count, and timestamps
        """
        # Query based on third SQL query in metrics-query.sql
        # Subquery to get all user phone numbers
        user_phones_subq = self.db.query(UserModel.phone_number).subquery()
        
        results = self.db.query(
            MetricModel.phone_number,
            func.count(MetricModel.id).label('attempt_count'),
            func.max(MetricModel.created_at).label('last_attempt'),
            func.min(MetricModel.created_at).label('first_attempt'),
            MetricModel.channel
        )\
            .filter(
                and_(
                    MetricModel.phone_number.isnot(None),
                    ~MetricModel.phone_number.in_(user_phones_subq)
                )
            )\
            .group_by(MetricModel.phone_number, MetricModel.channel)\
            .order_by(func.count(MetricModel.id).desc())\
            .all()
        
        return [
            {
                'phone_number': result.phone_number,
                'attempt_count': result.attempt_count,
                'last_attempt': result.last_attempt.isoformat() if result.last_attempt else None,
                'first_attempt': result.first_attempt.isoformat() if result.first_attempt else None,
                'channel': result.channel
            }
            for result in results
        ]
    
    def get_all_users_with_stats(self) -> List[Dict]:
        """Get all users with their message and warning counts
        
        Returns:
            List of dicts with user name, phone number, total messages, and total warnings
        """
        # Query based on fourth SQL query in metrics-query.sql
        # Subquery for message counts
        msg_counts_subq = self.db.query(
            ConversationModel.user_id,
            func.count(MessageModel.id).label('mcnt')
        )\
            .join(MessageModel, MessageModel.conversation_id == ConversationModel.id)\
            .group_by(ConversationModel.user_id)\
            .subquery()
        
        # Subquery for warning counts
        warning_counts_subq = self.db.query(
            MetricModel.user_id,
            func.count(MetricModel.id).label('total')
        )\
            .filter(MetricModel.user_id.isnot(None))\
            .group_by(MetricModel.user_id)\
            .subquery()
        
        results = self.db.query(
            UserModel.name,
            UserModel.phone_number,
            func.coalesce(msg_counts_subq.c.mcnt, 0).label('total_messages'),
            func.coalesce(warning_counts_subq.c.total, 0).label('total_warnings')
        )\
            .outerjoin(msg_counts_subq, msg_counts_subq.c.user_id == UserModel.id)\
            .outerjoin(warning_counts_subq, warning_counts_subq.c.user_id == UserModel.id)\
            .order_by(UserModel.name)\
            .all()
        
        return [
            {
                'name': result.name,
                'phone_number': result.phone_number,
                'total_messages': result.total_messages,
                'total_warnings': result.total_warnings
            }
            for result in results
        ]
    
    def get_peak_interaction_hours(self, from_date: Optional[datetime] = None) -> List[Dict]:
        """Get peak interaction hours throughout the day
        
        Args:
            from_date: Optional start date to filter messages
            
        Returns:
            List of dicts with hour of day, interaction count, and unique users
        """
        # Query based on fifth SQL query in metrics-query.sql
        query = self.db.query(
            func.extract('hour', MessageModel.created_at).label('hour_of_day'),
            func.count(MessageModel.id).label('interaction_count'),
            func.count(func.distinct(MessageModel.conversation_id)).label('unique_users')
        )\
            .join(ConversationModel, MessageModel.conversation_id == ConversationModel.id)
        
        # Apply date filter if provided
        if from_date:
            query = query.filter(MessageModel.created_at >= from_date)
        
        results = query\
            .group_by(func.extract('hour', MessageModel.created_at))\
            .order_by(func.count(MessageModel.id).desc())\
            .all()
        
        return [
            {
                'hour_of_day': int(result.hour_of_day) if result.hour_of_day is not None else 0,
                'interaction_count': result.interaction_count,
                'unique_users': result.unique_users
            }
            for result in results
        ]
    
    def get_frequent_questions(self, limit: int = 50, from_date: Optional[datetime] = None) -> List[Dict]:
        """Get most frequent questions or message patterns
        
        Args:
            limit: Maximum number of questions to return
            from_date: Optional start date to filter messages
            
        Returns:
            List of dicts with question text, frequency, unique users, and timestamps
        """
        # Query based on the frequent questions SQL query in metrics-query.sql
        query = self.db.query(
            func.lower(func.trim(MessageModel.user_message)).label('question_text'),
            func.count(MessageModel.id).label('frequency'),
            func.count(func.distinct(MessageModel.conversation_id)).label('unique_users'),
            func.min(MessageModel.created_at).label('first_asked'),
            func.max(MessageModel.created_at).label('last_asked')
        )\
            .join(ConversationModel, MessageModel.conversation_id == ConversationModel.id)\
            .filter(MessageModel.user_message.isnot(None))\
            .filter(func.length(MessageModel.user_message) > 5)\
            .filter(func.length(MessageModel.user_message) < 500)
        
        # Apply date filter if provided
        if from_date:
            query = query.filter(MessageModel.created_at >= from_date)
        
        results = query\
            .group_by(func.lower(func.trim(MessageModel.user_message)))\
            .having(func.count(MessageModel.id) > 1)\
            .order_by(func.count(MessageModel.id).desc(), func.count(func.distinct(MessageModel.conversation_id)).desc())\
            .limit(limit)\
            .all()
        
        return [
            {
                'question_text': result.question_text,
                'frequency': result.frequency,
                'unique_users': result.unique_users,
                'first_asked': result.first_asked.isoformat() if result.first_asked else None,
                'last_asked': result.last_asked.isoformat() if result.last_asked else None
            }
            for result in results
        ]
