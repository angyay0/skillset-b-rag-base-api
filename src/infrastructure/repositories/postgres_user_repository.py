from typing import Optional, List
from sqlalchemy.orm import Session
from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.database.models import UserModel


class PostgresUserRepository(UserRepository):
    """PostgreSQL implementation of UserRepository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user: User) -> User:
        """Create a new user"""
        db_user = UserModel(
            phone_number=user.phone_number,
            name=user.name,
            language=user.language,
            validity_days=user.validity_days,
            is_active=user.is_active
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return self._to_entity(db_user)
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_entity(db_user) if db_user else None
    
    def get_by_phone(self, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        db_user = self.db.query(UserModel).filter(UserModel.phone_number == phone_number).first()
        return self._to_entity(db_user) if db_user else None
    
    def update(self, user: User) -> User:
        """Update user"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if not db_user:
            raise ValueError(f"User with id {user.id} not found")
        
        db_user.phone_number = user.phone_number
        db_user.name = user.name
        db_user.language = user.language
        db_user.validity_days = user.validity_days
        db_user.is_active = user.is_active
        
        self.db.commit()
        self.db.refresh(db_user)
        return self._to_entity(db_user)
    
    def delete(self, user_id: int) -> bool:
        """Delete user"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        return True
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users"""
        db_users = self.db.query(UserModel).offset(offset).limit(limit).all()
        return [self._to_entity(db_user) for db_user in db_users]
    
    @staticmethod
    def _to_entity(db_user: UserModel) -> User:
        """Convert database model to entity"""
        return User(
            id=db_user.id,
            phone_number=db_user.phone_number,
            name=db_user.name,
            language=db_user.language,
            validity_days=db_user.validity_days,
            is_active=db_user.is_active,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )
