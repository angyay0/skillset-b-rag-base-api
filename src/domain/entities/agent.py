from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


@dataclass
class Agent:
    """Agent entity for managing AI agents"""
    id: Optional[int]
    name: str
    type: str
    description: Optional[str]
    configuration: Optional[Dict[str, Any]]
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    users: List['User'] = field(default_factory=list)