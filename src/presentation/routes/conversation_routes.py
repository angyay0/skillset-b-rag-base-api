from flask import Blueprint
from src.infrastructure.database.connection import get_db_context
from src.infrastructure.repositories.postgres_conversation_repository import (
    PostgresConversationRepository,
    PostgresMessageRepository
)
from src.infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from src.infrastructure.ai.vertex_ai_service import VertexAIService
from src.application.services.conversation_service import ConversationService
from src.presentation.controllers.conversation_controller import ConversationController


def create_conversation_blueprint() -> Blueprint:
    """Create and configure conversation blueprint"""
    bp = Blueprint('conversations', __name__, url_prefix='/api/conversations')
    
    # Helper function to create controller with proper session management
    def with_conversation_controller(handler_method):
        """Decorator to provide controller with proper DB session management"""
        def wrapper(*args, **kwargs):
            with get_db_context() as db:
                conversation_repo = PostgresConversationRepository(db)
                message_repo = PostgresMessageRepository(db)
                user_repo = PostgresUserRepository(db)
                ai_service = VertexAIService()
                
                conversation_service = ConversationService(
                    conversation_repo=conversation_repo,
                    message_repo=message_repo,
                    user_repo=user_repo,
                    ai_service=ai_service
                )
                controller = ConversationController(conversation_service)
                return getattr(controller, handler_method)(*args, **kwargs)
        wrapper.__name__ = handler_method
        return wrapper
    
    # Register routes with session management
    # GET /api/conversations - List all conversations for a user
    bp.route('', methods=['GET'])(with_conversation_controller('list_conversations'))
    
    # GET /api/conversations/:id - Get single conversation with messages
    bp.route('/<int:conversation_id>', methods=['GET'])(
        with_conversation_controller('get_conversation')
    )
    
    # GET /api/conversations/:id/messages - Get messages with filtering (NEW)
    bp.route('/<int:conversation_id>/messages', methods=['GET'])(
        with_conversation_controller('get_conversation_messages_handler')
    )
    
    # POST /api/conversations/:id/messages - Send a message to a conversation
    bp.route('/<int:conversation_id>/messages', methods=['POST'])(
        with_conversation_controller('send_message')
    )
    
    # POST /api/conversations - Create a new conversation
    bp.route('', methods=['POST'])(with_conversation_controller('create_conversation'))
    
    return bp
