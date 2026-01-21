from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import hashlib
from src.domain.entities.user import User, PLAN_TIERS, VALID_PLANS
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

        # Get plan details for default values
        plan_name = user_data.get('subscription_plan', 'free')
        if plan_name not in VALID_PLANS:
            plan_name = 'free'
        plan_details = PLAN_TIERS[plan_name]
        
        now = datetime.now(timezone.utc)

        # Hash password if provided
        password_hash = None
        if user_data.get('password'):
            password_hash = hashlib.sha256(user_data['password'].encode()).hexdigest()

        # Create user
        user = User(
            id=None,
            phone_number=user_data['phone_number'],
            name=user_data.get('name'),
            language=user_data.get('language', 'es'),
            validity_days=user_data.get('validity_days', plan_details['validity_days']),
            is_active=user_data.get('is_active', True),
            created_at=now,
            updated_at=now,
            agents=agents,
            subscription_plan=plan_name,
            subscription_start_date=now,
            subscription_end_date=now + timedelta(days=plan_details['validity_days']),
            max_messages_per_month=plan_details['max_messages_per_month'],
            max_agents=plan_details['max_agents'],
            email=user_data.get('email'),
            password_hash=password_hash,
            company_name=user_data.get('company_name'),
            team_size=user_data.get('team_size'),
            industry=user_data.get('industry'),
            primary_use_case=user_data.get('primary_use_case')
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

        user.updated_at = datetime.now(timezone.utc)
        return self.user_repo.update(user)

    def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        return self.user_repo.delete(user_id)

    def list_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all users"""
        users = self.user_repo.list_all(limit=limit, offset=offset)
        return [self._to_response_dict(user) for user in users]

    def change_subscription_plan(self, user_id: int, new_plan: str) -> Dict[str, Any]:
        """Change user's subscription plan (upgrade or downgrade)"""
        # Validate plan
        if new_plan not in VALID_PLANS:
            raise ValueError(f"Invalid subscription plan. Valid options: {', '.join(VALID_PLANS)}")
        
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        previous_plan = user.subscription_plan
        change_type = user.get_plan_change_type(new_plan)
        
        if change_type == 'same':
            return {
                'user': self._to_response_dict(user),
                'previous_plan': previous_plan,
                'new_plan': new_plan,
                'change_type': 'none',
                'message': 'User is already on this plan'
            }
        
        # Get new plan details
        plan_details = PLAN_TIERS[new_plan]
        now = datetime.now(timezone.utc)
        
        # Update subscription fields
        user.subscription_plan = new_plan
        user.subscription_start_date = now
        user.subscription_end_date = now + timedelta(days=plan_details['validity_days'])
        user.max_messages_per_month = plan_details['max_messages_per_month']
        user.max_agents = plan_details['max_agents']
        user.validity_days = plan_details['validity_days']
        user.updated_at = now
        
        # Save changes
        updated_user = self.user_repo.update(user)
        
        return {
            'user': self._to_response_dict(updated_user),
            'previous_plan': previous_plan,
            'new_plan': new_plan,
            'change_type': change_type
        }

    def get_plan_details(self, plan_name: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific plan"""
        if plan_name not in VALID_PLANS:
            return None
        return {
            'name': plan_name,
            **PLAN_TIERS[plan_name]
        }

    def get_all_plans(self) -> List[Dict[str, Any]]:
        """Get all available plans with their details"""
        return [
            {'name': name, **details}
            for name, details in PLAN_TIERS.items()
        ]

    def _to_response_dict(self, user: User) -> Dict[str, Any]:
        """Convert user entity to response dictionary"""
        return {
            'id': user.id,
            'phone_number': user.phone_number,
            'name': user.name,
            'email': user.email,
            'company_name': user.company_name,
            'team_size': user.team_size,
            'industry': user.industry,
            'primary_use_case': user.primary_use_case,
            'language': user.language,
            'validity_days': user.validity_days,
            'is_active': user.is_active,
            'subscription_plan': user.subscription_plan,
            'subscription_start_date': user.subscription_start_date.isoformat() if user.subscription_start_date else None,
            'subscription_end_date': user.subscription_end_date.isoformat() if user.subscription_end_date else None,
            'max_messages_per_month': user.max_messages_per_month,
            'max_agents': user.max_agents,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            'agents': [{'id': agent.id, 'name': agent.name} for agent in user.agents] if user.agents else []
        }