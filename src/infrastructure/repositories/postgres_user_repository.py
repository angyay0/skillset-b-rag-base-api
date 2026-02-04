from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from src.domain.entities.user import User
from src.domain.entities.agent import Agent
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.database.models import UserModel, AgentModel


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
            is_active=user.is_active,
            subscription_plan=user.subscription_plan,
            subscription_start_date=user.subscription_start_date,
            subscription_end_date=user.subscription_end_date,
            max_messages_per_month=user.max_messages_per_month,
            max_agents=user.max_agents,
            email=user.email,
            password_hash=user.password_hash,
            company_name=user.company_name,
            team_size=user.team_size,
            industry=user.industry,
            primary_use_case=user.primary_use_case
        )
        # Set agents relationship if provided
        if user.agents:
            db_user.agents = [self.db.query(AgentModel).get(agent.id) for agent in user.agents if agent.id]
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return self._to_entity(db_user)
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        db_user = self.db.query(UserModel).options(joinedload(UserModel.agents)).filter(UserModel.id == user_id).first()
        return self._to_entity(db_user) if db_user else None

    def get_by_phone(self, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        db_user = self.db.query(UserModel).options(joinedload(UserModel.agents)).filter(UserModel.phone_number == phone_number).first()
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
        db_user.subscription_plan = user.subscription_plan
        db_user.subscription_start_date = user.subscription_start_date
        db_user.subscription_end_date = user.subscription_end_date
        db_user.max_messages_per_month = user.max_messages_per_month
        db_user.max_agents = user.max_agents
        db_user.email = user.email
        db_user.password_hash = user.password_hash
        db_user.company_name = user.company_name
        db_user.team_size = user.team_size
        db_user.industry = user.industry
        db_user.primary_use_case = user.primary_use_case
        # Update agents relationship
        if user.agents:
            db_user.agents = [self.db.query(AgentModel).get(agent.id) for agent in user.agents if agent.id]

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
    
    def add_agent_to_user(self, user_id: int, agent_id: int) -> bool:
        """Add an agent to a user (creates entry in user_agents table)"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return False
        
        db_agent = self.db.query(AgentModel).filter(AgentModel.id == agent_id).first()
        if not db_agent:
            return False
        
        # Check if relationship already exists
        if db_agent not in db_user.agents:
            db_user.agents.append(db_agent)
            self.db.commit()
        
        return True
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users"""
        db_users = self.db.query(UserModel).options(joinedload(UserModel.agents)).offset(offset).limit(limit).all()
        return [self._to_entity(db_user) for db_user in db_users]
    
    def _to_entity(self, db_user: UserModel) -> User:
        """Convert database model to entity"""
        agents = [self._to_agent_entity(db_agent) for db_agent in db_user.agents] if db_user.agents else []
        return User(
            id=db_user.id,
            phone_number=db_user.phone_number,
            name=db_user.name,
            language=db_user.language,
            validity_days=db_user.validity_days,
            is_active=db_user.is_active,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
            agents=agents,
            subscription_plan=db_user.subscription_plan,
            subscription_start_date=db_user.subscription_start_date,
            subscription_end_date=db_user.subscription_end_date,
            max_messages_per_month=db_user.max_messages_per_month,
            max_agents=db_user.max_agents,
            email=db_user.email,
            password_hash=db_user.password_hash,
            company_name=db_user.company_name,
            team_size=db_user.team_size,
            industry=db_user.industry,
            primary_use_case=db_user.primary_use_case
        )

    def _to_agent_entity(self, db_agent: AgentModel) -> Agent:
        """Convert AgentModel to Agent entity"""
        return Agent(
            id=db_agent.id,
            name=db_agent.name,
            type=db_agent.type,
            description=db_agent.description,
            configuration=db_agent.configuration,
            is_active=db_agent.is_active,
            created_at=db_agent.created_at,
            updated_at=db_agent.updated_at
        )
