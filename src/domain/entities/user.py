from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


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
    
    def __post_init__(self):
        if not self.phone_number:
            raise ValueError("Phone number is required")
        if not self.language:
            self.language = 'es'
    
    def is_valid(self) -> bool:
        """Check if user is within valid service period"""
        if not self.is_active:
            return False
        
        # Calculate expiration date
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
