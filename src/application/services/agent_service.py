from datetime import datetime
from typing import Dict, Any, List, Optional
from src.domain.entities.agent import Agent
from src.domain.repositories.agent_repository import AgentRepository


class AgentService:
    """Service for managing agents"""

    def __init__(self, agent_repo: AgentRepository):
        self.agent_repo = agent_repo

    def create_agent(self, agent_data: Dict[str, Any]) -> Agent:
        """Create a new agent with validation"""

        # Validations
        self._validate_agent_data(agent_data)

        # Check if name already exists
        existing = self.agent_repo.get_by_name(agent_data['name'])
        if existing:
            raise ValueError(f"Agent with name '{agent_data['name']}' already exists")

        # Create entity
        agent = Agent(
            id=None,
            name=agent_data['name'],
            type=agent_data['type'],
            description=agent_data.get('description'),
            configuration=agent_data.get('configuration'),
            is_active=agent_data.get('is_active', True),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Save to database
        return self.agent_repo.create(agent)

    def get_agent_by_id(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        agent = self.agent_repo.get_by_id(agent_id)
        return self._to_response_dict(agent) if agent else None

    def get_agent_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get agent by name"""
        agent = self.agent_repo.get_by_name(name)
        return self._to_response_dict(agent) if agent else None

    def get_agents_by_type(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get agents by type"""
        agents = self.agent_repo.get_by_type(agent_type)
        return [self._to_response_dict(agent) for agent in agents]

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents"""
        agents = self.agent_repo.get_all()
        return [self._to_response_dict(agent) for agent in agents]

    def get_active_agents(self) -> List[Dict[str, Any]]:
        """Get active agents"""
        agents = self.agent_repo.get_active()
        return [self._to_response_dict(agent) for agent in agents]

    def update_agent(self, agent_id: int, agent_data: Dict[str, Any]) -> bool:
        """Update an agent"""

        # Get existing agent
        existing = self.agent_repo.get_by_id(agent_id)
        if not existing:
            raise ValueError(f"Agent with ID {agent_id} not found")

        # Check name uniqueness if name is being changed
        if 'name' in agent_data and agent_data['name'] != existing.name:
            name_check = self.agent_repo.get_by_name(agent_data['name'])
            if name_check:
                raise ValueError(f"Agent with name '{agent_data['name']}' already exists")

        # Update entity
        updated_agent = Agent(
            id=agent_id,
            name=agent_data.get('name', existing.name),
            type=agent_data.get('type', existing.type),
            description=agent_data.get('description', existing.description),
            configuration=agent_data.get('configuration', existing.configuration),
            is_active=agent_data.get('is_active', existing.is_active),
            created_at=existing.created_at,
            updated_at=datetime.utcnow()
        )

        return self.agent_repo.update(updated_agent)

    def delete_agent(self, agent_id: int) -> bool:
        """Delete an agent"""
        existing = self.agent_repo.get_by_id(agent_id)
        if not existing:
            raise ValueError(f"Agent with ID {agent_id} not found")

        return self.agent_repo.delete(agent_id)

    def _validate_agent_data(self, agent_data: Dict[str, Any]) -> None:
        """Validate agent data"""
        if not agent_data.get('name'):
            raise ValueError("name is required")

        if not agent_data.get('type'):
            raise ValueError("type is required")

        # Validate configuration if provided
        config = agent_data.get('configuration')
        if config is not None and not isinstance(config, dict):
            raise ValueError("configuration must be a dictionary")

    def _to_response_dict(self, agent: Agent) -> Dict[str, Any]:
        """Convert entity to response dictionary"""
        return {
            'id': agent.id,
            'name': agent.name,
            'type': agent.type,
            'description': agent.description,
            'configuration': agent.configuration,
            'is_active': agent.is_active,
            'created_at': agent.created_at.isoformat() if agent.created_at else None,
            'updated_at': agent.updated_at.isoformat() if agent.updated_at else None
        }