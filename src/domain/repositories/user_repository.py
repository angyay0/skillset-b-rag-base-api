from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.user import User


class UserRepository(ABC):
    """User repository interface"""
    
    @abstractmethod
    def create(self, user: User) -> User:
        """Create a new user"""
        raise NotImplementedError
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        raise NotImplementedError
    
    @abstractmethod
    def get_by_phone(self, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        raise NotImplementedError
    
    @abstractmethod
    def update(self, user: User) -> User:
        """Update user"""
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Delete user"""
        raise NotImplementedError
    
    @abstractmethod
    def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users"""
        raise NotImplementedError
