from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Metric:
    """Metric entity for tracking errors and important events"""
    id: Optional[int]
    metric_type: str  # 'error', 'warning', 'info', 'access_denied', 'expired_user', 'ai_error'
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None
    phone_number: Optional[str] = None
    channel: Optional[str] = None
    error_details: Optional[dict] = None
    created_at: Optional[datetime] = None
