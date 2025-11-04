from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from src.domain.entities.metric import Metric
from src.domain.repositories.metric_repository import MetricRepository
from src.infrastructure.database.models import MessageModel, MetricModel, UserModel, ConversationModel
from src.infrastructure.ai.vertex_ai_service import VertexAIService


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
        
        # Create the date_trunc expression once to reuse in GROUP BY and ORDER BY
        hour_bucket = func.date_trunc('hour', MessageModel.created_at).label('hour')
        
        results = self.db.query(
            hour_bucket,
            func.avg(MessageModel.response_time_ms).label('avg_ms'),
            func.count(MessageModel.id).label('count')
        )\
            .filter(MessageModel.response_time_ms.isnot(None))\
            .filter(MessageModel.created_at >= start_date)\
            .group_by(hour_bucket)\
            .order_by(hour_bucket)\
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
        
        # Create the date_trunc expression once to reuse in GROUP BY and ORDER BY
        hour_bucket = func.date_trunc('hour', MessageModel.created_at).label('hour')
        
        results = self.db.query(
            hour_bucket,
            func.count(MessageModel.id).label('count')
        )\
            .filter(MessageModel.created_at >= start_date)\
            .group_by(hour_bucket)\
            .order_by(hour_bucket)\
            .all()
        
        return [
            {
                'hour': result.hour.isoformat(),
                'count': result.count
            }
            for result in results
        ]
    
    def get_dashboard_home_metrics(self) -> Dict:
        """Get dashboard home metrics with month-over-month comparison
        
        Returns:
            dict with total_messages, active_users, response_rate, satisfaction
            each with current value, change percentage, and change direction
            Falls back to all-time account averages if current month has no data
        """
        now = datetime.utcnow()
        
        # Current month period
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Last month period
        last_month_end = current_month_start - timedelta(seconds=1)
        last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # --- Get all-time account metrics for fallback ---
        all_time_messages = self.db.query(func.count(MessageModel.id)).scalar() or 0
        all_time_active_users = self.db.query(func.count(func.distinct(ConversationModel.user_id)))\
            .join(MessageModel, MessageModel.conversation_id == ConversationModel.id)\
            .scalar() or 0
        all_time_total = self.db.query(func.count(MessageModel.id)).scalar() or 0
        all_time_with_response = self.db.query(func.count(MessageModel.id))\
            .filter(MessageModel.assistant_response.isnot(None))\
            .filter(MessageModel.assistant_response != '')\
            .scalar() or 0
        all_time_response_rate = (all_time_with_response / all_time_total * 100) if all_time_total > 0 else 0
        all_time_avg_response_time = self.db.query(func.avg(MessageModel.response_time_ms))\
            .filter(MessageModel.response_time_ms.isnot(None))\
            .scalar() or 0
        all_time_satisfaction = self._response_time_to_satisfaction(all_time_avg_response_time)
        
        # --- Total Messages ---
        current_messages = self.db.query(func.count(MessageModel.id))\
            .filter(MessageModel.created_at >= current_month_start)\
            .scalar() or 0
        
        last_month_messages = self.db.query(func.count(MessageModel.id))\
            .filter(MessageModel.created_at >= last_month_start)\
            .filter(MessageModel.created_at < current_month_start)\
            .scalar() or 0
        
        # --- Active Users (users who sent at least one message) ---
        current_active_users = self.db.query(func.count(func.distinct(ConversationModel.user_id)))\
            .join(MessageModel, MessageModel.conversation_id == ConversationModel.id)\
            .filter(MessageModel.created_at >= current_month_start)\
            .scalar() or 0
        
        last_month_active_users = self.db.query(func.count(func.distinct(ConversationModel.user_id)))\
            .join(MessageModel, MessageModel.conversation_id == ConversationModel.id)\
            .filter(MessageModel.created_at >= last_month_start)\
            .filter(MessageModel.created_at < current_month_start)\
            .scalar() or 0
        
        # --- Response Rate (messages with assistant_response / total messages) ---
        current_total = self.db.query(func.count(MessageModel.id))\
            .filter(MessageModel.created_at >= current_month_start)\
            .scalar() or 0
        
        current_with_response = self.db.query(func.count(MessageModel.id))\
            .filter(MessageModel.created_at >= current_month_start)\
            .filter(MessageModel.assistant_response.isnot(None))\
            .filter(MessageModel.assistant_response != '')\
            .scalar() or 0
        
        current_response_rate = (current_with_response / current_total * 100) if current_total > 0 else 0
        
        last_total = self.db.query(func.count(MessageModel.id))\
            .filter(MessageModel.created_at >= last_month_start)\
            .filter(MessageModel.created_at < current_month_start)\
            .scalar() or 0
        
        last_with_response = self.db.query(func.count(MessageModel.id))\
            .filter(MessageModel.created_at >= last_month_start)\
            .filter(MessageModel.created_at < current_month_start)\
            .filter(MessageModel.assistant_response.isnot(None))\
            .filter(MessageModel.assistant_response != '')\
            .scalar() or 0
        
        last_response_rate = (last_with_response / last_total * 100) if last_total > 0 else 0
        
        # --- Satisfaction (based on avg response time - faster = better, scale 1-5) ---
        current_avg_response_time = self.db.query(func.avg(MessageModel.response_time_ms))\
            .filter(MessageModel.created_at >= current_month_start)\
            .filter(MessageModel.response_time_ms.isnot(None))\
            .scalar() or 0
        
        last_avg_response_time = self.db.query(func.avg(MessageModel.response_time_ms))\
            .filter(MessageModel.created_at >= last_month_start)\
            .filter(MessageModel.created_at < current_month_start)\
            .filter(MessageModel.response_time_ms.isnot(None))\
            .scalar() or 0
        
        current_satisfaction = self._response_time_to_satisfaction(current_avg_response_time)
        last_satisfaction = self._response_time_to_satisfaction(last_avg_response_time)
        
        # --- Determine if we should use all-time data (fallback when current month is empty) ---
        use_all_time = current_messages == 0 and all_time_messages > 0
        
        # Use all-time values if current month has no data
        final_messages = all_time_messages if use_all_time else current_messages
        final_active_users = all_time_active_users if use_all_time else current_active_users
        final_response_rate = all_time_response_rate if use_all_time else current_response_rate
        final_satisfaction = all_time_satisfaction if use_all_time else current_satisfaction
        
        # Calculate changes (use 0 change if showing all-time data)
        messages_change = 0.0 if use_all_time else self._calculate_percentage_change(last_month_messages, current_messages)
        users_change = 0.0 if use_all_time else self._calculate_percentage_change(last_month_active_users, current_active_users)
        response_rate_change = 0.0 if use_all_time else round(current_response_rate - last_response_rate, 1)
        satisfaction_change = 0.0 if use_all_time else round(current_satisfaction - last_satisfaction, 1)
        
        period_label = 'all time (no data this month)' if use_all_time else 'from last month'
        
        return {
            'total_messages': {
                'value': final_messages,
                'formatted_value': self._format_number(final_messages),
                'change': messages_change,
                'change_label': f"{'+' if messages_change >= 0 else ''}{messages_change}%",
                'period': period_label
            },
            'active_users': {
                'value': final_active_users,
                'formatted_value': self._format_number(final_active_users),
                'change': users_change,
                'change_label': f"{'+' if users_change >= 0 else ''}{users_change}%",
                'period': period_label
            },
            'response_rate': {
                'value': round(final_response_rate, 1),
                'formatted_value': f"{round(final_response_rate, 1)}%",
                'change': response_rate_change,
                'change_label': f"{'+' if response_rate_change >= 0 else ''}{response_rate_change}%",
                'period': period_label
            },
            'satisfaction': {
                'value': final_satisfaction,
                'formatted_value': f"{final_satisfaction}/5",
                'change': satisfaction_change,
                'change_label': f"{'+' if satisfaction_change >= 0 else ''}{satisfaction_change}",
                'period': period_label
            },
            'period': {
                'current_month_start': current_month_start.isoformat(),
                'last_month_start': last_month_start.isoformat(),
                'last_month_end': last_month_end.isoformat(),
                'using_all_time_data': use_all_time
            },
            'all_time': {
                'total_messages': all_time_messages,
                'active_users': all_time_active_users,
                'response_rate': round(all_time_response_rate, 1),
                'satisfaction': all_time_satisfaction,
                'avg_response_time_ms': int(all_time_avg_response_time) if all_time_avg_response_time else 0
            }
        }
    
    def _calculate_percentage_change(self, old_value: float, new_value: float) -> float:
        """Calculate percentage change between two values"""
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0
        return round(((new_value - old_value) / old_value) * 100, 1)
    
    def _response_time_to_satisfaction(self, avg_response_time_ms: float) -> float:
        """Convert average response time to a satisfaction score (1-5)"""
        if avg_response_time_ms == 0:
            return 5.0
        elif avg_response_time_ms < 2000:  # Under 2 seconds
            return 5.0
        elif avg_response_time_ms < 5000:  # Under 5 seconds
            return 4.5
        elif avg_response_time_ms < 10000:  # Under 10 seconds
            return 4.0
        elif avg_response_time_ms < 15000:  # Under 15 seconds
            return 3.5
        elif avg_response_time_ms < 20000:  # Under 20 seconds
            return 3.0
        elif avg_response_time_ms < 30000:  # Under 30 seconds
            return 2.5
        else:
            return 2.0
    
    def _format_number(self, num: int) -> str:
        """Format number with thousand separators"""
        return f"{num:,}"
    
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
    
    def get_recent_activities(self, limit: int = 50) -> List[Dict]:
        """Get recent activities for dashboard list display
        
        Returns a unified list of recent activities including:
        - New messages/conversations
        - New user registrations
        - System events (errors, warnings, access denied)
        
        Args:
            limit: Maximum number of activities to return
            
        Returns:
            List of activity dicts sorted by timestamp (most recent first)
        """
        activities = []
        
        # Get recent messages with user info
        recent_messages = self.db.query(
            MessageModel.id,
            MessageModel.user_message,
            MessageModel.created_at,
            MessageModel.response_time_ms,
            ConversationModel.channel,
            UserModel.name.label('user_name'),
            UserModel.phone_number
        )\
            .join(ConversationModel, MessageModel.conversation_id == ConversationModel.id)\
            .join(UserModel, ConversationModel.user_id == UserModel.id)\
            .order_by(MessageModel.created_at.desc())\
            .limit(limit)\
            .all()
        
        for msg in recent_messages:
            # Truncate message for preview
            preview = msg.user_message[:80] + '...' if len(msg.user_message) > 80 else msg.user_message
            activities.append({
                'id': f'msg_{msg.id}',
                'type': 'message',
                'icon': 'message',
                'title': f'New message from {msg.user_name or msg.phone_number}',
                'description': preview,
                'channel': msg.channel,
                'timestamp': msg.created_at.isoformat() if msg.created_at else None,
                'metadata': {
                    'response_time_ms': msg.response_time_ms
                }
            })
        
        # Get recent user registrations
        recent_users = self.db.query(UserModel)\
            .order_by(UserModel.created_at.desc())\
            .limit(limit // 2)\
            .all()
        
        for user in recent_users:
            activities.append({
                'id': f'user_{user.id}',
                'type': 'user_registration',
                'icon': 'user-plus',
                'title': f'New user registered',
                'description': f'{user.name or "Unknown"} ({user.phone_number})',
                'channel': None,
                'timestamp': user.created_at.isoformat() if user.created_at else None,
                'metadata': {
                    'subscription_plan': user.subscription_plan,
                    'language': user.language
                }
            })
        
        # Get recent metrics/events (errors, warnings, etc.)
        recent_metrics = self.db.query(MetricModel)\
            .order_by(MetricModel.created_at.desc())\
            .limit(limit // 2)\
            .all()
        
        icon_map = {
            'error': 'alert-circle',
            'warning': 'alert-triangle',
            'info': 'info',
            'access_denied': 'shield-off',
            'expired_user': 'user-x'
        }
        
        for metric in recent_metrics:
            activities.append({
                'id': f'metric_{metric.id}',
                'type': metric.metric_type,
                'icon': icon_map.get(metric.metric_type, 'activity'),
                'title': f'{metric.metric_type.replace("_", " ").title()}',
                'description': metric.message[:100] + '...' if len(metric.message) > 100 else metric.message,
                'channel': metric.channel,
                'timestamp': metric.created_at.isoformat() if metric.created_at else None,
                'metadata': {
                    'severity': metric.severity,
                    'phone_number': metric.phone_number
                }
            })
        
        # Sort all activities by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        
        # Return only the requested limit
        return activities[:limit]
    
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
        from sqlalchemy import select
        user_phones_subq = select(UserModel.phone_number).subquery()
        
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
    
    def _get_frequent_messages(self, limit: int = 100, from_date: Optional[datetime] = None) -> List[Dict]:
        """Get most frequent user messages (internal method for clustering)
        
        Args:
            limit: Maximum number of messages to return
            from_date: Optional start date to filter messages
            
        Returns:
            List of dicts with message text, frequency, unique users, and timestamps
        """
        query = self.db.query(
            func.lower(func.trim(MessageModel.user_message)).label('message_text'),
            func.count(MessageModel.id).label('frequency'),
            func.count(func.distinct(MessageModel.conversation_id)).label('unique_users'),
            func.min(MessageModel.created_at).label('first_asked'),
            func.max(MessageModel.created_at).label('last_asked')
        )\
            .join(ConversationModel, MessageModel.conversation_id == ConversationModel.id)\
            .filter(MessageModel.user_message.isnot(None))\
            .filter(func.length(MessageModel.user_message) > 3)\
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
                'message_text': result.message_text,
                'frequency': result.frequency,
                'unique_users': result.unique_users,
                'first_asked': result.first_asked.isoformat() if result.first_asked else None,
                'last_asked': result.last_asked.isoformat() if result.last_asked else None
            }
            for result in results
        ]
    
    def get_topic_clusters(self, limit: int = 100, from_date: Optional[datetime] = None, num_clusters: int = 5) -> Dict:
        """Get user messages clustered by topic using AI
        
        Args:
            limit: Maximum number of messages to analyze
            from_date: Optional start date to filter messages
            num_clusters: Number of topic clusters to identify
            
        Returns:
            Dict with clusters, each containing topic name, description, messages, and stats
        """
        # Get frequent user messages (not just questions)
        messages_data = self._get_frequent_messages(limit, from_date)
        
        if not messages_data or len(messages_data) == 0:
            return {
                'clusters': [],
                'total_messages_analyzed': 0,
                'total_interactions': 0,
                'analysis_date': datetime.utcnow().isoformat()
            }
        
        # Prepare messages text for AI analysis
        messages_list = []
        for idx, msg in enumerate(messages_data, 1):
            messages_list.append(f"{idx}. {msg['message_text']} (sent {msg['frequency']} times by {msg['unique_users']} users)")
        
        messages_text = "\n".join(messages_list)
        
        # Create AI prompt for clustering
        prompt = f"""Analyze the following user messages and group them into {num_clusters} main topic clusters.

IMPORTANT INSTRUCTIONS:
- Messages may be in Spanish or English - group by SEMANTIC MEANING, not language
- Look for similar intents even if worded differently (e.g., "Vuca-Fani", "vuca fani", "vucafani" are the same)
- Ignore typos, capitalization, and minor variations
- Group messages about the same topic/intent together (questions, statements, requests, etc.)
- Provide topic names and descriptions in Spanish if most messages are in Spanish, otherwise in English

For each cluster, provide:
1. A short topic name (2-4 words) - use the language of the majority of messages
2. A brief description (1 sentence) - explain what users are asking/talking about
3. The message numbers that belong to this cluster

User Messages:
{messages_text}

Respond ONLY with valid JSON in this exact structure (no markdown, no extra text):
{{
    "clusters": [
        {{
            "topic": "Topic Name",
            "description": "Brief description of what users are asking/talking about",
            "message_numbers": [1, 2, 3]
        }}
    ]
}}"""

        try:
            # Use VertexAI to cluster topics
            ai_service = VertexAIService()
            response_text = ai_service.generate_response(
                question=prompt,
                context="Topic clustering analysis",
                language='en',
                use_rag=False,
                max_output_tokens=1000
            )
            
            # Parse AI response
            import json
            import re
            
            # Clean up response text - remove markdown code blocks if present
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```'):
                # Remove markdown code blocks
                cleaned_text = re.sub(r'^```(?:json)?\s*', '', cleaned_text)
                cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
            
            # Extract JSON from response (in case AI adds extra text)
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                ai_result = json.loads(json_match.group())
            else:
                raise ValueError(f"No valid JSON found in AI response. Response was: {response_text[:200]}")
            
            # Build clusters with actual message data
            clusters = []
            total_interactions = 0
            
            for cluster in ai_result.get('clusters', []):
                message_numbers = cluster.get('message_numbers', []) or cluster.get('question_numbers', [])
                cluster_messages = []
                cluster_frequency = 0
                cluster_unique_users = 0
                
                for msg_num in message_numbers:
                    idx = msg_num - 1  # Convert to 0-indexed
                    if 0 <= idx < len(messages_data):
                        msg = messages_data[idx]
                        cluster_messages.append({
                            'text': msg['message_text'],
                            'frequency': msg['frequency'],
                            'unique_users': msg['unique_users']
                        })
                        cluster_frequency += msg['frequency']
                        cluster_unique_users += msg['unique_users']
                
                if cluster_messages:
                    clusters.append({
                        'topic': cluster.get('topic', 'Unknown Topic'),
                        'description': cluster.get('description', ''),
                        'total_messages': len(cluster_messages),
                        'total_frequency': cluster_frequency,
                        'total_unique_users': cluster_unique_users,
                        'questions': cluster_messages[:5]  # Limit to top 5 messages per cluster
                    })
                    total_interactions += cluster_frequency
            
            # Sort clusters by frequency
            clusters.sort(key=lambda x: x['total_frequency'], reverse=True)
            
            return {
                'clusters': clusters,
                'total_questions_analyzed': len(messages_data),
                'total_interactions': total_interactions,
                'analysis_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error clustering topics: {str(e)}")
            # Return a fallback simple clustering based on frequency
            return {
                'clusters': [{
                    'topic': 'Most Frequent Messages',
                    'description': 'Top messages sent by users',
                    'total_messages': min(10, len(messages_data)),
                    'total_frequency': sum(msg['frequency'] for msg in messages_data[:10]),
                    'total_unique_users': sum(msg['unique_users'] for msg in messages_data[:10]),
                    'questions': [
                        {
                            'text': msg['message_text'],
                            'frequency': msg['frequency'],
                            'unique_users': msg['unique_users']
                        }
                        for msg in messages_data[:10]
                    ]
                }],
                'total_questions_analyzed': len(messages_data),
                'total_interactions': sum(msg['frequency'] for msg in messages_data),
                'analysis_date': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    # ==================== DEMOGRAPHICS ANALYTICS ====================
    
    def get_demographics_report(self) -> Dict:
        """Get comprehensive demographics report for dashboard charts
        
        Returns:
            dict with aggregated demographics data for visualization
        """
        users = self.db.query(UserModel).filter(UserModel.demographics.isnot(None)).all()
        
        if not users:
            return {
                'total_users_with_demographics': 0,
                'charts': {},
                'summary': {}
            }
        
        # Initialize aggregators for each demographic field
        demographics_fields = [
            'organization', 'department', 'location', 'country', 
            'gender', 'age_group', 'tenure', 'education_level', 'organizational_level'
        ]
        
        aggregated = {field: {} for field in demographics_fields}
        
        # Aggregate demographics data
        for user in users:
            demographics = user.demographics or {}
            for field in demographics_fields:
                value = demographics.get(field)
                if value:
                    value_str = str(value).strip()
                    if value_str:
                        aggregated[field][value_str] = aggregated[field].get(value_str, 0) + 1
        
        # Build chart data for each field
        charts = {}
        for field, counts in aggregated.items():
            if counts:
                sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                charts[field] = {
                    'labels': [item[0] for item in sorted_items],
                    'values': [item[1] for item in sorted_items],
                    'total': sum(counts.values())
                }
        
        return {
            'total_users_with_demographics': len(users),
            'charts': charts,
            'summary': self._get_demographics_summary(aggregated),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _get_demographics_summary(self, aggregated: Dict) -> Dict:
        """Generate summary statistics from aggregated demographics"""
        summary = {}
        
        for field, counts in aggregated.items():
            if counts:
                total = sum(counts.values())
                top_value = max(counts.items(), key=lambda x: x[1]) if counts else (None, 0)
                summary[field] = {
                    'total_responses': total,
                    'unique_values': len(counts),
                    'top_value': top_value[0],
                    'top_value_count': top_value[1],
                    'top_value_percentage': round((top_value[1] / total) * 100, 1) if total > 0 else 0
                }
        
        return summary
    
    def get_demographics_by_field(self, field: str) -> Dict:
        """Get demographics breakdown for a specific field
        
        Args:
            field: Demographics field name (e.g., 'gender', 'age_group', 'department')
            
        Returns:
            dict with field breakdown data
        """
        valid_fields = [
            'organization', 'department', 'location', 'country',
            'gender', 'age_group', 'tenure', 'education_level', 'organizational_level'
        ]
        
        if field not in valid_fields:
            return {'error': f'Invalid field. Valid fields: {", ".join(valid_fields)}'}
        
        users = self.db.query(UserModel).filter(UserModel.demographics.isnot(None)).all()
        
        counts = {}
        for user in users:
            demographics = user.demographics or {}
            value = demographics.get(field)
            if value:
                value_str = str(value).strip()
                if value_str:
                    counts[value_str] = counts.get(value_str, 0) + 1
        
        if not counts:
            return {
                'field': field,
                'total': 0,
                'breakdown': []
            }
        
        total = sum(counts.values())
        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'field': field,
            'total': total,
            'breakdown': [
                {
                    'value': item[0],
                    'count': item[1],
                    'percentage': round((item[1] / total) * 100, 1)
                }
                for item in sorted_items
            ]
        }
    
    def get_demographics_cross_analysis(self, field1: str, field2: str) -> Dict:
        """Get cross-analysis between two demographics fields
        
        Args:
            field1: First demographics field
            field2: Second demographics field
            
        Returns:
            dict with cross-tabulation data for heatmap/matrix visualization
        """
        valid_fields = [
            'organization', 'department', 'location', 'country',
            'gender', 'age_group', 'tenure', 'education_level', 'organizational_level'
        ]
        
        if field1 not in valid_fields or field2 not in valid_fields:
            return {'error': f'Invalid fields. Valid fields: {", ".join(valid_fields)}'}
        
        users = self.db.query(UserModel).filter(UserModel.demographics.isnot(None)).all()
        
        # Build cross-tabulation
        cross_tab = {}
        field1_values = set()
        field2_values = set()
        
        for user in users:
            demographics = user.demographics or {}
            val1 = demographics.get(field1)
            val2 = demographics.get(field2)
            
            if val1 and val2:
                val1_str = str(val1).strip()
                val2_str = str(val2).strip()
                field1_values.add(val1_str)
                field2_values.add(val2_str)
                
                key = (val1_str, val2_str)
                cross_tab[key] = cross_tab.get(key, 0) + 1
        
        # Build matrix format
        field1_list = sorted(list(field1_values))
        field2_list = sorted(list(field2_values))
        
        matrix = []
        for v1 in field1_list:
            row = {
                field1: v1,
                'values': {v2: cross_tab.get((v1, v2), 0) for v2 in field2_list}
            }
            matrix.append(row)
        
        return {
            'field1': field1,
            'field2': field2,
            'field1_values': field1_list,
            'field2_values': field2_list,
            'matrix': matrix,
            'total_records': sum(cross_tab.values())
        }
