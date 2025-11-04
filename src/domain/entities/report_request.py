from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from .agent import Agent


@dataclass
class ReportRequest:
    """Report request entity for tracking custom metric report requests"""
    id: Optional[UUID]
    agent_id: Optional[int]
    metrics: List[str]
    period_days: int
    format: str
    requested_for: Optional[str]
    requested_by: str
    status: str = "pending"
    created_at: Optional[datetime] = None
    agent: Optional[Agent] = None
