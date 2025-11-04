from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import Agent

# Plan tier definitions
PLAN_TIERS = {
    'free': {'max_messages_per_month': 100, 'max_agents': 1, 'validity_days': 30, 'level': 0},
    'basic': {'max_messages_per_month': 500, 'max_agents': 3, 'validity_days': 30, 'level': 1},
    'pro': {'max_messages_per_month': 2000, 'max_agents': 10, 'validity_days': 30, 'level': 2},
    'enterprise': {'max_messages_per_month': -1, 'max_agents': -1, 'validity_days': 365, 'level': 3}  # -1 = unlimited
}

VALID_PLANS = list(PLAN_TIERS.keys())


@dataclass
class User:
    """User entity"""
    id: Optional[int]
    phone_number: str
    name: Optional[str]
    language: str
    created_at: datetime
    updated_at: datetime
    validity_days: int = 30
    is_active: bool = True
    agents: List['Agent'] = field(default_factory=list)
    
    # Subscription plan attributes
    subscription_plan: str = 'free'
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    max_messages_per_month: int = 100
    max_agents: int = 1
    
    # Profile attributes (from frontend form)
    email: Optional[str] = None
    password_hash: Optional[str] = None
    company_name: Optional[str] = None
    team_size: Optional[str] = None
    industry: Optional[str] = None
    primary_use_case: Optional[str] = None
    
    # Custom demographics attributes (optional JSON key-value pairs)
    demographics: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.phone_number:
            raise ValueError("Phone number is required")
        if not self.language:
            self.language = 'es'
        if self.subscription_plan not in VALID_PLANS:
            self.subscription_plan = 'free'
    
    def is_valid(self) -> bool:
        """Check if user is within valid service period"""
        if not self.is_active:
            return False
        
        # Use subscription_end_date if available (new system), otherwise fallback to created_at + validity_days
        if self.subscription_end_date:
            expiration_date = self.subscription_end_date
        else:
            expiration_date = self.created_at + timedelta(days=self.validity_days)
        
        current_date = datetime.now(timezone.utc)
        
        # Ensure both datetimes are timezone-aware for comparison
        if expiration_date.tzinfo is None:
            expiration_date = expiration_date.replace(tzinfo=timezone.utc)
        
        return current_date <= expiration_date
    
    def days_remaining(self) -> int:
        """Get number of days remaining in service period"""
        expiration_date = self.created_at + timedelta(days=self.validity_days)
        current_date = datetime.now(timezone.utc)
        
        # Ensure both datetimes are timezone-aware for comparison
        if expiration_date.tzinfo is None:
            expiration_date = expiration_date.replace(tzinfo=timezone.utc)
        
        remaining = (expiration_date - current_date).days
        return max(0, remaining)
    
    def expiration_date(self) -> datetime:
        """Get the expiration date of the service"""
        return self.created_at + timedelta(days=self.validity_days)
    
    def can_upgrade_to(self, plan: str) -> bool:
        """Check if user can upgrade to a specific plan"""
        if plan not in VALID_PLANS:
            return False
        current_level = PLAN_TIERS[self.subscription_plan]['level']
        new_level = PLAN_TIERS[plan]['level']
        return new_level > current_level
    
    def can_downgrade_to(self, plan: str) -> bool:
        """Check if user can downgrade to a specific plan"""
        if plan not in VALID_PLANS:
            return False
        current_level = PLAN_TIERS[self.subscription_plan]['level']
        new_level = PLAN_TIERS[plan]['level']
        return new_level < current_level
    
    def is_subscription_active(self) -> bool:
        """Check if subscription is currently active"""
        if not self.subscription_end_date:
            return True  # No end date means active
        
        current_date = datetime.now(timezone.utc)
        end_date = self.subscription_end_date
        
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        return current_date <= end_date
    
    def get_plan_change_type(self, new_plan: str) -> str:
        """Get the type of plan change: upgrade, downgrade, or same"""
        if new_plan not in VALID_PLANS:
            return 'invalid'
        current_level = PLAN_TIERS[self.subscription_plan]['level']
        new_level = PLAN_TIERS[new_plan]['level']
        if new_level > current_level:
            return 'upgrade'
        elif new_level < current_level:
            return 'downgrade'
        return 'same'

