from typing import List, Optional, Dict, Any
from datetime import datetime
from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository


class UserService:
    """Service for managing users"""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user with validation"""

        # Validations
        if not user_data.get('phone_number'):
            raise ValueError("phone_number is required")

        # Check if user exists
        existing = self.user_repo.get_by_phone(user_data['phone_number'])
        if existing:
            raise ValueError(f"User with phone number {user_data['phone_number']} already exists")

        # Get agents if provided
        agents = []
        if 'agent_ids' in user_data:
            from src.infrastructure.repositories.postgres_agent_repository import PostgresAgentRepository
            from src.infrastructure.database.connection import get_db_context
            with get_db_context() as db:
                agent_repo = PostgresAgentRepository(db)
                for agent_id in user_data['agent_ids']:
                    agent = agent_repo.get_by_id(agent_id)
                    if agent:
                        agents.append(agent)

        # Create user
        user = User(
            id=None,
            phone_number=user_data['phone_number'],
            name=user_data.get('name'),
            language=user_data.get('language', 'es'),
            validity_days=user_data.get('validity_days', 30),
            is_active=user_data.get('is_active', True),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            agents=agents
        )

        return self.user_repo.create(user)

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        user = self.user_repo.get_by_id(user_id)
        return self._to_response_dict(user) if user else None

    def get_user_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get user by phone number"""
        user = self.user_repo.get_by_phone(phone_number)
        return self._to_response_dict(user) if user else None

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
        """Update user"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None

        # Update fields
        for key, value in user_data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        user.updated_at = datetime.utcnow()
        return self.user_repo.update(user)

    def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        return self.user_repo.delete(user_id)

    def list_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all users"""
        users = self.user_repo.list_all(limit=limit, offset=offset)
        return [self._to_response_dict(user) for user in users]

    def _to_response_dict(self, user: User) -> Dict[str, Any]:
        """Convert user entity to response dictionary"""
        return {
            'id': user.id,
            'phone_number': user.phone_number,
            'name': user.name,
            'language': user.language,
            'validity_days': user.validity_days,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            'agents': [{'id': agent.id, 'name': agent.name} for agent in user.agents] if user.agents else []
        }