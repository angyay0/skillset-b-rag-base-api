from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from src.domain.entities.agent import Agent
from src.domain.entities.user import User
from src.domain.repositories.agent_repository import AgentRepository
from src.infrastructure.database.models import AgentModel, UserModel


class PostgresAgentRepository(AgentRepository):
    """PostgreSQL implementation of AgentRepository"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, agent: Agent) -> Agent:
        """Create a new agent"""
        db_agent = AgentModel(
            name=agent.name,
            type=agent.type,
            description=agent.description,
            configuration=agent.configuration,
            is_active=agent.is_active,
            auto_respond=agent.auto_respond,
            learning_mode=agent.learning_mode,
            response_temperature=str(agent.response_temperature),
            max_response_tokens=agent.max_response_tokens,
            system_prompt=agent.system_prompt
        )

        self.db.add(db_agent)
        self.db.commit()
        self.db.refresh(db_agent)

        return self._to_entity(db_agent)

    def get_by_id(self, agent_id: int) -> Optional[Agent]:
        """Get agent by ID"""
        db_agent = self.db.query(AgentModel).filter(
            AgentModel.id == agent_id
        ).first()

        return self._to_entity(db_agent) if db_agent else None

    def get_by_name(self, name: str) -> Optional[Agent]:
        """Get agent by name"""
        db_agent = self.db.query(AgentModel).filter(
            AgentModel.name == name
        ).first()

        return self._to_entity(db_agent) if db_agent else None

    def get_by_type(self, agent_type: str, limit: int = 100) -> List[Agent]:
        """Get agents by type"""
        db_agents = self.db.query(AgentModel).filter(
            AgentModel.type == agent_type
        ).order_by(AgentModel.created_at.desc()).limit(limit).all()

        return [self._to_entity(agent) for agent in db_agents]

    def get_all(self, limit: int = 100) -> List[Agent]:
        """Get all agents"""
        db_agents = self.db.query(AgentModel).order_by(
            AgentModel.created_at.desc()
        ).limit(limit).all()

        return [self._to_entity(agent) for agent in db_agents]

    def get_active(self, limit: int = 100) -> List[Agent]:
        """Get active agents"""
        db_agents = self.db.query(AgentModel).filter(
            AgentModel.is_active == True
        ).order_by(AgentModel.created_at.desc()).limit(limit).all()

        return [self._to_entity(agent) for agent in db_agents]

    def update(self, agent: Agent) -> bool:
        """Update an agent"""
        updated = self.db.query(AgentModel).filter(
            AgentModel.id == agent.id
        ).update({
            'name': agent.name,
            'type': agent.type,
            'description': agent.description,
            'configuration': agent.configuration,
            'is_active': agent.is_active,
            'auto_respond': agent.auto_respond,
            'learning_mode': agent.learning_mode,
            'response_temperature': str(agent.response_temperature),
            'max_response_tokens': agent.max_response_tokens,
            'system_prompt': agent.system_prompt,
            'updated_at': agent.updated_at
        })

        self.db.commit()
        return updated > 0

    def delete(self, agent_id: int) -> bool:
        """Delete an agent"""
        deleted = self.db.query(AgentModel).filter(
            AgentModel.id == agent_id
        ).delete()

        self.db.commit()
        return deleted > 0

    def get_users_by_agent(self, agent_id: int) -> List[dict]:
        """Get all users assigned to an agent"""
        db_agent = self.db.query(AgentModel).options(
            joinedload(AgentModel.users)
        ).filter(AgentModel.id == agent_id).first()
        
        if not db_agent:
            return []
        
        return [self._user_to_dict(user) for user in db_agent.users]

    def add_user_to_agent(self, agent_id: int, user_id: int) -> bool:
        """Add a user to an agent"""
        db_agent = self.db.query(AgentModel).filter(AgentModel.id == agent_id).first()
        if not db_agent:
            return False
        
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return False
        
        if db_user not in db_agent.users:
            db_agent.users.append(db_user)
            self.db.commit()
        
        return True

    def add_users_to_agent(self, agent_id: int, users_data: List[dict]) -> dict:
        """Add multiple users to an agent with optional language/validity updates"""
        db_agent = self.db.query(AgentModel).filter(AgentModel.id == agent_id).first()
        if not db_agent:
            return {'success': False, 'added': [], 'failed': [u.get('user_id') for u in users_data]}
        
        added = []
        failed = []
        
        for user_data in users_data:
            user_id = user_data.get('user_id')
            db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            
            if db_user:
                # Update language if provided
                if 'language' in user_data and user_data['language']:
                    db_user.language = user_data['language']
                
                # Update validity_days if provided
                if 'validity_days' in user_data and user_data['validity_days'] is not None:
                    db_user.validity_days = user_data['validity_days']
                
                # Add to agent if not already assigned
                if db_user not in db_agent.users:
                    db_agent.users.append(db_user)
                
                added.append(user_id)
            else:
                failed.append(user_id)
        
        self.db.commit()
        return {'success': True, 'added': added, 'failed': failed}

    def update_agent_users(self, agent_id: int, users_data: List[dict]) -> dict:
        """Update language/validity for users assigned to an agent"""
        db_agent = self.db.query(AgentModel).options(
            joinedload(AgentModel.users)
        ).filter(AgentModel.id == agent_id).first()
        
        if not db_agent:
            return {'success': False, 'updated': [], 'failed': [u.get('user_id') for u in users_data]}
        
        updated = []
        failed = []
        
        for user_data in users_data:
            user_id = user_data.get('user_id')
            db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            
            if db_user and db_user in db_agent.users:
                # Update language if provided
                if 'language' in user_data and user_data['language']:
                    db_user.language = user_data['language']
                
                # Update validity_days if provided
                if 'validity_days' in user_data and user_data['validity_days'] is not None:
                    db_user.validity_days = user_data['validity_days']
                
                updated.append(user_id)
            else:
                failed.append(user_id)
        
        self.db.commit()
        return {'success': True, 'updated': updated, 'failed': failed}

    def remove_user_from_agent(self, agent_id: int, user_id: int) -> bool:
        """Remove a user from an agent"""
        db_agent = self.db.query(AgentModel).options(
            joinedload(AgentModel.users)
        ).filter(AgentModel.id == agent_id).first()
        
        if not db_agent:
            return False
        
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return False
        
        if db_user in db_agent.users:
            db_agent.users.remove(db_user)
            self.db.commit()
            return True
        
        return False

    def remove_users_from_agent(self, agent_id: int, user_ids: List[int]) -> dict:
        """Remove multiple users from an agent"""
        db_agent = self.db.query(AgentModel).options(
            joinedload(AgentModel.users)
        ).filter(AgentModel.id == agent_id).first()
        
        if not db_agent:
            return {'success': False, 'removed': [], 'failed': user_ids}
        
        removed = []
        failed = []
        
        for user_id in user_ids:
            db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            if db_user and db_user in db_agent.users:
                db_agent.users.remove(db_user)
                removed.append(user_id)
            else:
                failed.append(user_id)
        
        self.db.commit()
        return {'success': True, 'removed': removed, 'failed': failed}

    def _to_entity(self, db_agent: AgentModel) -> Agent:
        """Convert database model to domain entity"""
        return Agent(
            id=db_agent.id,
            name=db_agent.name,
            type=db_agent.type,
            description=db_agent.description,
            configuration=db_agent.configuration,
            is_active=db_agent.is_active,
            auto_respond=db_agent.auto_respond,
            learning_mode=db_agent.learning_mode,
            response_temperature=float(db_agent.response_temperature) if db_agent.response_temperature else 0.7,
            max_response_tokens=db_agent.max_response_tokens,
            system_prompt=db_agent.system_prompt,
            created_at=db_agent.created_at,
            updated_at=db_agent.updated_at
        )

    def _user_to_dict(self, db_user: UserModel) -> dict:
        """Convert user model to dictionary"""
        return {
            'id': db_user.id,
            'phone_number': db_user.phone_number,
            'name': db_user.name,
            'language': db_user.language,
            'is_active': db_user.is_active,
            'created_at': db_user.created_at.isoformat() if db_user.created_at else None
        }