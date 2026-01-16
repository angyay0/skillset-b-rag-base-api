from typing import List, Optional
from sqlalchemy.orm import Session
from src.domain.entities.agent import Agent
from src.domain.repositories.agent_repository import AgentRepository
from src.infrastructure.database.models import AgentModel


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
            is_active=agent.is_active
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

    def _to_entity(self, db_agent: AgentModel) -> Agent:
        """Convert database model to domain entity"""
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