from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.agent import Agent


class AgentRepository(ABC):
    """Abstract repository for agents"""

    @abstractmethod
    def create(self, agent: Agent) -> Agent:
        """Create a new agent"""
        pass

    @abstractmethod
    def get_by_id(self, agent_id: int) -> Optional[Agent]:
        """Get agent by ID"""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Agent]:
        """Get agent by name"""
        pass

    @abstractmethod
    def get_by_type(self, agent_type: str, limit: int = 100) -> List[Agent]:
        """Get agents by type"""
        pass

    @abstractmethod
    def get_all(self, limit: int = 100) -> List[Agent]:
        """Get all agents"""
        pass

    @abstractmethod
    def get_active(self, limit: int = 100) -> List[Agent]:
        """Get active agents"""
        pass

    @abstractmethod
    def update(self, agent: Agent) -> bool:
        """Update an agent"""
        pass

    @abstractmethod
    def delete(self, agent_id: int) -> bool:
        """Delete an agent"""
        pass