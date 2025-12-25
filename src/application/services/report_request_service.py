from datetime import datetime
from typing import Dict, Any
from src.domain.entities.report_request import ReportRequest
from src.domain.repositories.report_request_repository import ReportRequestRepository


class ReportRequestService:
    """Service for managing report requests"""
    
    def __init__(self, report_request_repo: ReportRequestRepository):
        self.report_request_repo = report_request_repo
    
    def create_report_request(self, request_data: Dict[str, Any]) -> ReportRequest:
        """Create a new report request with validation"""
        
        # Validaciones básicas
        self._validate_request_data(request_data)
        
        # Calcular period_days a partir del date_range si existe
        period_days = request_data.get('period_days')
        if not period_days and 'date_range' in request_data:
            period_days = self._calculate_period_days(request_data['date_range'])
        
        # Crear entidad
        report_request = ReportRequest(
            id=None,
            agent_id=request_data['agent_id'],
            metrics=request_data['metrics'],
            period_days=period_days,
            format=request_data['format'],
            requested_for=request_data.get('requested_for'),
            requested_by=request_data['requested_by'],
            status='pending',
            created_at=datetime.utcnow()
        )
        
        # Guardar en base de datos
        return self.report_request_repo.create(report_request)
    
    def get_request_by_id(self, request_id: str) -> Dict[str, Any]:
        """Get report request by ID"""
        from uuid import UUID
        try:
            uuid_id = UUID(request_id)
            request = self.report_request_repo.get_by_id(uuid_id)
            return self._to_response_dict(request) if request else None
        except ValueError:
            raise ValueError(f"Invalid request ID format: {request_id}")

    def get_all_requests(self) -> list:
        """Get all report requests"""
        requests = self.report_request_repo.get_all()
        return [self._to_response_dict(request) for request in requests]
    
    def _validate_request_data(self, request_data: Dict[str, Any]) -> None:
        """Validate basic request data"""
        if not request_data.get('agent_id'):
            raise ValueError("agent_id is required")
        
        metrics = request_data.get('metrics', [])
        if not isinstance(metrics, list) or len(metrics) == 0:
            raise ValueError("metrics must be a non-empty list")
        
        if 'date_range' in request_data:
            self._validate_date_range(request_data['date_range'])
        
        format_value = request_data.get('format')
        if not format_value or not isinstance(format_value, str):
            raise ValueError("format is required and must be a string")
        
        if not request_data.get('requested_by'):
            raise ValueError("requested_by is required")
    
    def _validate_date_range(self, date_range: Dict[str, str]) -> None:
        """Validate date range format"""
        if not isinstance(date_range, dict):
            raise ValueError("date_range must be a dictionary")
        
        from_date = date_range.get('from')
        to_date = date_range.get('to')
        
        if not from_date or not to_date:
            raise ValueError("date_range must include 'from' and 'to' dates")
        
        try:
            from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            
            if from_dt > to_dt:
                raise ValueError("date_range 'from' must be less than or equal to 'to'")
        except ValueError as e:
            if "fromisoformat" in str(e):
                raise ValueError("Invalid date format. Use ISO format: YYYY-MM-DD")
            raise
    
    def _calculate_period_days(self, date_range: Dict[str, str]) -> int:
        """Calculate period days from date range"""
        from_date = datetime.fromisoformat(date_range['from'].replace('Z', '+00:00'))
        to_date = datetime.fromisoformat(date_range['to'].replace('Z', '+00:00'))
        
        delta = to_date - from_date
        return max(1, delta.days + 1)  # +1 to include both dates
    
    def _to_response_dict(self, request: ReportRequest) -> Dict[str, Any]:
        """Convert entity to response dictionary"""
        return {
            'id': str(request.id) if request.id else None,
            'agent_id': request.agent_id,
            'metrics': request.metrics,
            'period_days': request.period_days,
            'format': request.format,
            'requested_for': request.requested_for,
            'requested_by': request.requested_by,
            'status': request.status,
            'created_at': request.created_at.isoformat() if request.created_at else None
        }
