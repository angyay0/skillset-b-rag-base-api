from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from src.domain.entities.metric import Metric


class MetricRepository(ABC):
    """Abstract repository for metrics"""
    
    @abstractmethod
    def create(self, metric: Metric) -> Metric:
        """Create a new metric"""
        pass
    
    @abstractmethod
    def get_by_type(self, metric_type: str, limit: int = 100) -> List[Metric]:
        """Get metrics by type"""
        pass
    
    @abstractmethod
    def get_by_severity(self, severity: str, limit: int = 100) -> List[Metric]:
        """Get metrics by severity"""
        pass
    
    @abstractmethod
    def get_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 1000) -> List[Metric]:
        """Get metrics within a date range"""
        pass
    
    @abstractmethod
    def get_error_count_by_type(self, start_date: datetime, end_date: datetime) -> dict:
        """Get count of errors grouped by type"""
        pass
    
    @abstractmethod
    def get_recent_errors(self, limit: int = 50) -> List[Metric]:
        """Get recent errors and warnings"""
        pass
