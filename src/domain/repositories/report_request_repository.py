from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from src.domain.entities.report_request import ReportRequest


class ReportRequestRepository(ABC):
    """Abstract repository for report requests"""
    
    @abstractmethod
    def create(self, report_request: ReportRequest) -> ReportRequest:
        """Create a new report request"""
        pass
    
    @abstractmethod
    def get_by_id(self, request_id: UUID) -> Optional[ReportRequest]:
        """Get report request by ID"""
        pass
    
    @abstractmethod
    def get_by_agent(self, agent_id: int, limit: int = 100) -> List[ReportRequest]:
        """Get report requests by agent ID"""
        pass
    
    @abstractmethod
    def get_by_status(self, status: str, limit: int = 100) -> List[ReportRequest]:
        """Get report requests by status"""
        pass

    @abstractmethod
    def get_all(self, limit: int = 100) -> List[ReportRequest]:
        """Get all report requests"""
        pass

    @abstractmethod
    def update_status(self, request_id: UUID, status: str) -> bool:
        """Update report request status"""
        pass
