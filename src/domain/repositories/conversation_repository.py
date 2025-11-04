from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.conversation import Conversation, Message


class ConversationRepository(ABC):
    """Conversation repository interface"""
    
    @abstractmethod
    def create(self, conversation: Conversation) -> Conversation:
        """Create a new conversation"""
        raise NotImplementedError
    
    @abstractmethod
    def get_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """Get conversation by ID"""
        raise NotImplementedError
    
    @abstractmethod
    def get_by_user_and_channel(self, user_id: int, channel: str) -> Optional[Conversation]:
        """Get active conversation by user and channel"""
        raise NotImplementedError
    
    @abstractmethod
    def list_by_user(self, user_id: int, limit: int = 100) -> List[Conversation]:
        """List conversations by user"""
        raise NotImplementedError
    
    @abstractmethod
    def list_all(self, channel: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Conversation]:
        """List all conversations with optional channel filter"""
        raise NotImplementedError
    
    @abstractmethod
    def update(self, conversation: Conversation) -> Conversation:
        """Update conversation"""
        raise NotImplementedError


class MessageRepository(ABC):
    """Message repository interface"""
    
    @abstractmethod
    def create(self, message: Message) -> Message:
        """Create a new message"""
        raise NotImplementedError
    
    @abstractmethod
    def get_by_id(self, message_id: int) -> Optional[Message]:
        """Get message by ID"""
        raise NotImplementedError
    
    @abstractmethod
    def list_by_conversation(self, conversation_id: int, limit: int = 50) -> List[Message]:
        """List messages by conversation"""
        raise NotImplementedError
    
    @abstractmethod
    def get_conversation_history(self, conversation_id: int, limit: int = 10) -> List[Message]:
        """Get recent conversation history"""
        raise NotImplementedError
