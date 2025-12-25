from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.domain.entities.report_request import ReportRequest
from src.domain.repositories.report_request_repository import ReportRequestRepository
from src.infrastructure.database.models import ReportRequestModel


class PostgresReportRequestRepository(ReportRequestRepository):
    """PostgreSQL implementation of ReportRequestRepository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, report_request: ReportRequest) -> ReportRequest:
        """Create a new report request"""
        db_request = ReportRequestModel(
            agent_id=report_request.agent_id,
            metrics=report_request.metrics,
            period_days=report_request.period_days,
            format=report_request.format,
            requested_for=report_request.requested_for,
            requested_by=report_request.requested_by,
            status=report_request.status
        )
        
        self.db.add(db_request)
        self.db.commit()
        self.db.refresh(db_request)
        
        return self._to_entity(db_request)
    
    def get_by_id(self, request_id: UUID) -> Optional[ReportRequest]:
        """Get report request by ID"""
        db_request = self.db.query(ReportRequestModel).filter(
            ReportRequestModel.id == request_id
        ).first()
        
        return self._to_entity(db_request) if db_request else None
    
    def get_by_agent(self, agent_id: str, limit: int = 100) -> List[ReportRequest]:
        """Get report requests by agent ID"""
        db_requests = self.db.query(ReportRequestModel).filter(
            ReportRequestModel.agent_id == agent_id
        ).order_by(ReportRequestModel.created_at.desc()).limit(limit).all()
        
        return [self._to_entity(req) for req in db_requests]
    
    def get_by_status(self, status: str, limit: int = 100) -> List[ReportRequest]:
        """Get report requests by status"""
        db_requests = self.db.query(ReportRequestModel).filter(
            ReportRequestModel.status == status
        ).order_by(ReportRequestModel.created_at.desc()).limit(limit).all()

        return [self._to_entity(req) for req in db_requests]

    def get_all(self, limit: int = 100) -> List[ReportRequest]:
        """Get all report requests"""
        db_requests = self.db.query(ReportRequestModel).order_by(
            ReportRequestModel.created_at.desc()
        ).limit(limit).all()

        return [self._to_entity(req) for req in db_requests]

    def update_status(self, request_id: UUID, status: str) -> bool:
        """Update report request status"""
        updated = self.db.query(ReportRequestModel).filter(
            ReportRequestModel.id == request_id
        ).update({'status': status})
        
        self.db.commit()
        return updated > 0
    
    def _to_entity(self, db_request: ReportRequestModel) -> ReportRequest:
        """Convert database model to domain entity"""
        return ReportRequest(
            id=db_request.id,
            agent_id=db_request.agent_id,
            metrics=db_request.metrics,
            period_days=db_request.period_days,
            format=db_request.format,
            requested_for=db_request.requested_for,
            requested_by=db_request.requested_by,
            status=db_request.status,
            created_at=db_request.created_at
        )
