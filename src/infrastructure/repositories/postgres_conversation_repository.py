from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from src.domain.entities.conversation import Conversation, Message
from src.domain.repositories.conversation_repository import ConversationRepository, MessageRepository
from src.infrastructure.database.models import ConversationModel, MessageModel, UserModel, user_agents


class PostgresConversationRepository(ConversationRepository):
    """PostgreSQL implementation of ConversationRepository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, conversation: Conversation) -> Conversation:
        """Create a new conversation"""
        db_conversation = ConversationModel(
            user_id=conversation.user_id,
            channel=conversation.channel,
            is_active=conversation.is_active
        )
        self.db.add(db_conversation)
        self.db.commit()
        self.db.refresh(db_conversation)
        return self._to_entity(db_conversation)
    
    def get_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """Get conversation by ID"""
        db_conversation = self.db.query(ConversationModel).filter(
            ConversationModel.id == conversation_id
        ).first()
        return self._to_entity(db_conversation) if db_conversation else None
    
    def get_by_user_and_channel(self, user_id: int, channel: str) -> Optional[Conversation]:
        """Get active conversation by user and channel"""
        db_conversation = self.db.query(ConversationModel).filter(
            ConversationModel.user_id == user_id,
            ConversationModel.channel == channel,
            ConversationModel.is_active == True
        ).first()
        return self._to_entity(db_conversation) if db_conversation else None
    
    def list_by_user(self, user_id: int, limit: int = 100) -> List[Conversation]:
        """List conversations by user"""
        db_conversations = self.db.query(ConversationModel).filter(
            ConversationModel.user_id == user_id
        ).order_by(ConversationModel.created_at.desc()).limit(limit).all()
        return [self._to_entity(conv) for conv in db_conversations]
    
    def update(self, conversation: Conversation) -> Conversation:
        """Update conversation"""
        db_conversation = self.db.query(ConversationModel).filter(
            ConversationModel.id == conversation.id
        ).first()
        if not db_conversation:
            raise ValueError(f"Conversation with id {conversation.id} not found")
        
        db_conversation.is_active = conversation.is_active
        
        self.db.commit()
        self.db.refresh(db_conversation)
        return self._to_entity(db_conversation)
    
    def list_by_agent(
        self,
        agent_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        List all conversations from all users of an agent with pagination
        
        Args:
            agent_id: Agent ID
            limit: Maximum conversations to return
            offset: Number of conversations to skip
            
        Returns:
            Tuple of (conversations list with user info, total count)
        """
        # Build query with JOINs
        # conversations -> users -> user_agents
        query = self.db.query(
            ConversationModel,
            UserModel.name.label('user_name'),
            UserModel.phone_number.label('user_phone')
        ).join(
            UserModel, ConversationModel.user_id == UserModel.id
        ).join(
            user_agents, UserModel.id == user_agents.c.user_id
        ).filter(
            user_agents.c.agent_id == agent_id
        )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply ordering and pagination
        query = query.order_by(ConversationModel.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        # Execute query
        results = query.all()
        
        # Build enriched conversation data
        conversations = []
        for conv, user_name, user_phone in results:
            conversations.append({
                'conversation': self._to_entity(conv),
                'user_name': user_name,
                'user_phone': user_phone
            })
        
        return conversations, total_count
    
    @staticmethod
    def _to_entity(db_conversation: ConversationModel) -> Conversation:
        """Convert database model to entity"""
        return Conversation(
            id=db_conversation.id,
            user_id=db_conversation.user_id,
            channel=db_conversation.channel,
            is_active=db_conversation.is_active,
            created_at=db_conversation.created_at,
            updated_at=db_conversation.updated_at
        )


class PostgresMessageRepository(MessageRepository):
    """PostgreSQL implementation of MessageRepository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, message: Message) -> Message:
        """Create a new message"""
        db_message = MessageModel(
            conversation_id=message.conversation_id,
            user_message=message.user_message,
            assistant_response=message.assistant_response,
            language=message.language,
            message_metadata=message.metadata,
            response_time_ms=message.response_time_ms
        )
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        return self._to_entity(db_message)
    
    def get_by_id(self, message_id: int) -> Optional[Message]:
        """Get message by ID"""
        db_message = self.db.query(MessageModel).filter(MessageModel.id == message_id).first()
        return self._to_entity(db_message) if db_message else None
    
    def list_by_conversation(self, conversation_id: int, limit: int = 50) -> List[Message]:
        """List messages by conversation"""
        db_messages = self.db.query(MessageModel).filter(
            MessageModel.conversation_id == conversation_id
        ).order_by(MessageModel.created_at.desc()).limit(limit).all()
        return [self._to_entity(msg) for msg in db_messages]
    
    def list_by_conversation_filtered(
        self,
        conversation_id: int,
        limit: int = 50,
        offset: int = 0,
        order: str = 'desc',
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> tuple[List[Message], int]:
        """
        List messages by conversation with advanced filtering
        
        Args:
            conversation_id: Conversation ID
            limit: Maximum messages to return
            offset: Number of messages to skip
            order: 'asc' for oldest first, 'desc' for newest first
            from_date: Filter messages from this date (inclusive)
            to_date: Filter messages until this date (inclusive)
            
        Returns:
            Tuple of (messages list, total count)
        """
        # Build base query
        query = self.db.query(MessageModel).filter(
            MessageModel.conversation_id == conversation_id
        )
        
        # Apply date filters
        if from_date:
            query = query.filter(MessageModel.created_at >= from_date)
        if to_date:
            query = query.filter(MessageModel.created_at <= to_date)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply ordering
        if order == 'asc':
            query = query.order_by(MessageModel.created_at.asc())
        else:  # default to desc
            query = query.order_by(MessageModel.created_at.desc())
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        # Execute query
        db_messages = query.all()
        messages = [self._to_entity(msg) for msg in db_messages]
        
        return messages, total_count
    
    def get_conversation_history(self, conversation_id: int, limit: int = 10) -> List[Message]:
        """Get recent conversation history"""
        return self.list_by_conversation(conversation_id, limit)
    
    @staticmethod
    def _to_entity(db_message: MessageModel) -> Message:
        """Convert database model to entity"""
        return Message(
            id=db_message.id,
            conversation_id=db_message.conversation_id,
            user_message=db_message.user_message,
            assistant_response=db_message.assistant_response,
            language=db_message.language,
            metadata=db_message.message_metadata,
            response_time_ms=db_message.response_time_ms,
            created_at=db_message.created_at
        )
