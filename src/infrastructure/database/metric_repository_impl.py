from typing import List
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.domain.entities.metric import Metric
from src.domain.repositories.metric_repository import MetricRepository
from src.infrastructure.database.models import MetricModel


class MetricRepositoryImpl(MetricRepository):
    """SQLAlchemy implementation of MetricRepository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, metric: Metric) -> Metric:
        """Create a new metric"""
        db_metric = MetricModel(
            metric_type=metric.metric_type,
            severity=metric.severity,
            message=metric.message,
            user_id=metric.user_id,
            conversation_id=metric.conversation_id,
            phone_number=metric.phone_number,
            channel=metric.channel,
            error_details=metric.error_details
        )
        self.session.add(db_metric)
        self.session.commit()
        self.session.refresh(db_metric)
        
        return self._to_entity(db_metric)
    
    def get_by_type(self, metric_type: str, limit: int = 100) -> List[Metric]:
        """Get metrics by type"""
        db_metrics = self.session.query(MetricModel)\
            .filter(MetricModel.metric_type == metric_type)\
            .order_by(MetricModel.created_at.desc())\
            .limit(limit)\
            .all()
        
        return [self._to_entity(m) for m in db_metrics]
    
    def get_by_severity(self, severity: str, limit: int = 100) -> List[Metric]:
        """Get metrics by severity"""
        db_metrics = self.session.query(MetricModel)\
            .filter(MetricModel.severity == severity)\
            .order_by(MetricModel.created_at.desc())\
            .limit(limit)\
            .all()
        
        return [self._to_entity(m) for m in db_metrics]
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 1000) -> List[Metric]:
        """Get metrics within a date range"""
        db_metrics = self.session.query(MetricModel)\
            .filter(MetricModel.created_at >= start_date)\
            .filter(MetricModel.created_at <= end_date)\
            .order_by(MetricModel.created_at.desc())\
            .limit(limit)\
            .all()
        
        return [self._to_entity(m) for m in db_metrics]
    
    def get_error_count_by_type(self, start_date: datetime, end_date: datetime) -> dict:
        """Get count of errors grouped by type"""
        results = self.session.query(
            MetricModel.metric_type,
            func.count(MetricModel.id).label('count')
        )\
            .filter(MetricModel.created_at >= start_date)\
            .filter(MetricModel.created_at <= end_date)\
            .group_by(MetricModel.metric_type)\
            .all()
        
        return {result.metric_type: result.count for result in results}
    
    def get_recent_errors(self, limit: int = 50) -> List[Metric]:
        """Get recent errors and warnings"""
        db_metrics = self.session.query(MetricModel)\
            .filter(MetricModel.metric_type.in_(['error', 'warning', 'ai_error']))\
            .order_by(MetricModel.created_at.desc())\
            .limit(limit)\
            .all()
        
        return [self._to_entity(m) for m in db_metrics]
    
    def _to_entity(self, db_metric: MetricModel) -> Metric:
        """Convert database model to entity"""
        return Metric(
            id=db_metric.id,
            metric_type=db_metric.metric_type,
            severity=db_metric.severity,
            message=db_metric.message,
            user_id=db_metric.user_id,
            conversation_id=db_metric.conversation_id,
            phone_number=db_metric.phone_number,
            channel=db_metric.channel,
            error_details=db_metric.error_details,
            created_at=db_metric.created_at
        )
