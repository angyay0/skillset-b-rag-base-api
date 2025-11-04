from datetime import datetime
from typing import Optional, List, Dict, Any
from src.domain.entities.conversation import Conversation, Message
from src.domain.entities.user import User
from src.domain.repositories.conversation_repository import ConversationRepository, MessageRepository
from src.domain.repositories.user_repository import UserRepository
from src.domain.repositories.agent_repository import AgentRepository
from src.infrastructure.ai.vertex_ai_service import VertexAIService


class ConversationService:
    """Service for managing conversations and messages"""
    
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        user_repo: UserRepository,
        ai_service: Optional[VertexAIService] = None,
        agent_repo: Optional[AgentRepository] = None
    ):
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.user_repo = user_repo
        self.ai_service = ai_service
        self.agent_repo = agent_repo
    
    def get_user_conversations(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all conversations for a user with message count
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation dictionaries with message counts
        """
        # Verify user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        conversations = self.conversation_repo.list_by_user(user_id, limit)
        
        # Enrich with message counts
        result = []
        for conv in conversations:
            messages = self.message_repo.list_by_conversation(conv.id, limit=1)
            message_count = len(self.message_repo.list_by_conversation(conv.id, limit=10000))
            
            result.append({
                'id': conv.id,
                'user_id': conv.user_id,
                'channel': conv.channel,
                'is_active': conv.is_active,
                'created_at': conv.created_at.isoformat() if conv.created_at else None,
                'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
                'message_count': message_count
            })
        
        return result
    
    def list_all_conversations(
        self, 
        channel: Optional[str] = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all conversations with optional channel filter
        
        Args:
            channel: Optional channel filter (e.g., 'whatsapp', 'whatsapp_twilio')
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            
        Returns:
            List of conversation dictionaries with message counts
        """
        conversations = self.conversation_repo.list_all(channel, limit, offset)
        
        # Enrich with message counts
        result = []
        for conv in conversations:
            message_count = len(self.message_repo.list_by_conversation(conv.id, limit=10000))
            
            result.append({
                'id': conv.id,
                'user_id': conv.user_id,
                'channel': conv.channel,
                'is_active': conv.is_active,
                'created_at': conv.created_at.isoformat() if conv.created_at else None,
                'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
                'message_count': message_count
            })
        
        return result
    
    def get_conversation_with_messages(
        self, 
        conversation_id: int, 
        message_limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get a conversation with its messages (CASCADE)
        
        Args:
            conversation_id: Conversation ID
            message_limit: Maximum number of messages to return
            
        Returns:
            Dictionary with conversation data and nested messages
            
        Raises:
            ValueError: If conversation not found
        """
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation with id {conversation_id} not found")
        
        # Get messages ordered by created_at descending
        messages = self.message_repo.list_by_conversation(conversation_id, limit=message_limit)
        
        # Convert messages to dictionaries
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'conversation_id': msg.conversation_id,
                'user_message': msg.user_message,
                'assistant_response': msg.assistant_response,
                'language': msg.language,
                'created_at': msg.created_at.isoformat() if msg.created_at else None,
                'response_time_ms': msg.response_time_ms,
                'metadata': msg.metadata
            })
        
        # Reverse to show oldest first
        messages_data.reverse()
        
        return {
            'id': conversation.id,
            'user_id': conversation.user_id,
            'channel': conversation.channel,
            'is_active': conversation.is_active,
            'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
            'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
            'messages': messages_data
        }
    
    def send_message(
        self,
        conversation_id: int,
        user_message: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a conversation and get AI response
        
        Args:
            conversation_id: Conversation ID
            user_message: User's message text
            metadata: Optional metadata (e.g., message_sid, source)
            
        Returns:
            Dictionary with created message including AI response
            
        Raises:
            ValueError: If conversation not found or AI service not available
        """
        if not user_message or not user_message.strip():
            raise ValueError("user_message is required and cannot be empty")
        
        # Verify conversation exists
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation with id {conversation_id} not found")
        
        # Get user for language preference
        user = self.user_repo.get_by_id(conversation.user_id)
        if not user:
            raise ValueError(f"User with id {conversation.user_id} not found")
        
        # Get conversation history for context
        history = self.message_repo.get_conversation_history(conversation_id, limit=5)
        context = self._build_context(history)
        
        # Generate AI response if service is available
        if self.ai_service:
            import time
            ai_start_time = time.time()
            ai_response = self.ai_service.generate_response(
                question=user_message,
                context=context,
                language=user.language,
                max_output_tokens=110
            )
            response_time_ms = int((time.time() - ai_start_time) * 1000)
        else:
            # Fallback if no AI service
            ai_response = "AI service not available"
            response_time_ms = 0
        
        # Create message
        message = Message(
            id=None,
            conversation_id=conversation_id,
            user_message=user_message.strip(),
            assistant_response=ai_response,
            language=user.language,
            metadata=metadata,
            response_time_ms=response_time_ms,
            created_at=datetime.utcnow()
        )
        
        created_message = self.message_repo.create(message)
        
        return {
            'id': created_message.id,
            'conversation_id': created_message.conversation_id,
            'user_message': created_message.user_message,
            'assistant_response': created_message.assistant_response,
            'language': created_message.language,
            'created_at': created_message.created_at.isoformat() if created_message.created_at else None,
            'response_time_ms': created_message.response_time_ms,
            'metadata': created_message.metadata
        }
    
    def create_conversation(self, user_id: int, channel: str) -> Dict[str, Any]:
        """
        Create a new conversation
        
        Args:
            user_id: User ID
            channel: Communication channel ('whatsapp', 'whatsapp_twilio', 'voice')
            
        Returns:
            Dictionary with created conversation data
            
        Raises:
            ValueError: If user not found or invalid channel
        """
        # Verify user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        # Validate channel
        valid_channels = ['whatsapp', 'whatsapp_twilio', 'voice']
        if channel not in valid_channels:
            raise ValueError(f"Invalid channel. Must be one of: {', '.join(valid_channels)}")
        
        # Check if active conversation already exists for this user and channel
        existing_conversation = self.conversation_repo.get_by_user_and_channel(user_id, channel)
        if existing_conversation:
            # Return existing conversation instead of creating a new one
            return {
                'id': existing_conversation.id,
                'user_id': existing_conversation.user_id,
                'channel': existing_conversation.channel,
                'is_active': existing_conversation.is_active,
                'created_at': existing_conversation.created_at.isoformat() if existing_conversation.created_at else None,
                'updated_at': existing_conversation.updated_at.isoformat() if existing_conversation.updated_at else None
            }
        
        # Create new conversation
        conversation = Conversation(
            id=None,
            user_id=user_id,
            channel=channel,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        created_conversation = self.conversation_repo.create(conversation)
        
        return {
            'id': created_conversation.id,
            'user_id': created_conversation.user_id,
            'channel': created_conversation.channel,
            'is_active': created_conversation.is_active,
            'created_at': created_conversation.created_at.isoformat() if created_conversation.created_at else None,
            'updated_at': created_conversation.updated_at.isoformat() if created_conversation.updated_at else None
        }
    
    def get_conversation_messages(
        self,
        conversation_id: int,
        limit: int = 50,
        offset: int = 0,
        order: str = 'desc',
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get messages from a conversation with advanced filtering
        
        Args:
            conversation_id: Conversation ID
            limit: Maximum messages to return (pagination)
            offset: Number of messages to skip (pagination)
            order: 'asc' for oldest first, 'desc' for newest first
            from_date: ISO format date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
            to_date: ISO format date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
            
        Returns:
            Dictionary with messages and pagination metadata
            
        Raises:
            ValueError: If conversation not found or invalid parameters
        """
        # Verify conversation exists
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation with id {conversation_id} not found")
        
        # Validate order parameter
        if order not in ['asc', 'desc']:
            raise ValueError("order must be 'asc' or 'desc'")
        
        # Parse date parameters
        from_datetime = None
        to_datetime = None
        
        if from_date:
            try:
                # Try parsing as ISO datetime first
                from_datetime = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try parsing as date only
                    from_datetime = datetime.strptime(from_date, '%Y-%m-%d')
                except ValueError:
                    raise ValueError(f"Invalid from_date format: {from_date}. Use YYYY-MM-DD or ISO format")
        
        if to_date:
            try:
                # Try parsing as ISO datetime first
                to_datetime = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try parsing as date only (set to end of day)
                    to_datetime = datetime.strptime(to_date, '%Y-%m-%d')
                    to_datetime = to_datetime.replace(hour=23, minute=59, second=59)
                except ValueError:
                    raise ValueError(f"Invalid to_date format: {to_date}. Use YYYY-MM-DD or ISO format")
        
        # Get filtered messages with total count
        messages, total_count = self.message_repo.list_by_conversation_filtered(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
            order=order,
            from_date=from_datetime,
            to_date=to_datetime
        )
        
        # Convert messages to dictionaries
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'conversation_id': msg.conversation_id,
                'user_message': msg.user_message,
                'assistant_response': msg.assistant_response,
                'language': msg.language,
                'created_at': msg.created_at.isoformat() if msg.created_at else None,
                'response_time_ms': msg.response_time_ms,
                'metadata': msg.metadata
            })
        
        # Calculate pagination metadata
        has_more = (offset + limit) < total_count
        
        return {
            'conversation_id': conversation_id,
            'messages': messages_data,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': has_more
        }
    
    def get_agent_conversations(
        self,
        agent_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get all conversations from all users of an agent
        
        Args:
            agent_id: Agent ID
            limit: Conversations per page (default: 20)
            offset: Number to skip for pagination
            
        Returns:
            Dict with conversations and pagination metadata
            
        Raises:
            ValueError: If agent not found
        """
        # Validate agent exists (if agent_repo available)
        if self.agent_repo:
            agent = self.agent_repo.get_by_id(agent_id)
            if not agent:
                raise ValueError(f"Agent with id {agent_id} not found")
        
        # Get conversations with user info
        conversations_data, total_count = self.conversation_repo.list_by_agent(
            agent_id=agent_id,
            limit=limit,
            offset=offset
        )
        
        # Enrich with message counts
        enriched_conversations = []
        for conv_data in conversations_data:
            conv = conv_data['conversation']
            
            # Get message count for this conversation
            messages = self.message_repo.list_by_conversation(conv.id, limit=10000)
            message_count = len(messages)
            
            enriched_conversations.append({
                'id': conv.id,
                'user_id': conv.user_id,
                'user_name': conv_data['user_name'],
                'user_phone': conv_data['user_phone'],
                'channel': conv.channel,
                'is_active': conv.is_active,
                'message_count': message_count,
                'created_at': conv.created_at.isoformat() if conv.created_at else None,
                'updated_at': conv.updated_at.isoformat() if conv.updated_at else None
            })
        
        # Calculate pagination metadata
        has_more = (offset + limit) < total_count
        
        return {
            'agent_id': agent_id,
            'conversations': enriched_conversations,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': has_more
        }
    
    def _build_context(self, history: List[Message]) -> str:
        """
        Build context string from conversation history
        
        Args:
            history: List of messages
            
        Returns:
            Context string for AI
        """
        if not history:
            return "Nueva conversación"
        
        context_parts = []
        for msg in reversed(history[-3:]):  # Last 3 messages
            context_parts.append(f"Usuario: {msg.user_message}")
            context_parts.append(f"Asistente: {msg.assistant_response}")
        
        return "\n".join(context_parts)
