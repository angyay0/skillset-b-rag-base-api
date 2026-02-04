from flask import Blueprint
from src.infrastructure.database.connection import get_db_context
from src.infrastructure.repositories.postgres_agent_repository import PostgresAgentRepository
from src.infrastructure.repositories.postgres_conversation_repository import (
    PostgresConversationRepository,
    PostgresMessageRepository
)
from src.infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from src.infrastructure.ai.vertex_ai_service import VertexAIService
from src.application.services.agent_service import AgentService
from src.application.services.conversation_service import ConversationService
from src.presentation.controllers.agent_controller import AgentController
from src.presentation.controllers.conversation_controller import ConversationController


def create_agent_blueprint() -> Blueprint:
    """Create and configure agent blueprint"""
    bp = Blueprint('agents', __name__, url_prefix='/api/agents')

    # Helper function to create controller with proper session management
    def with_agent_controller(handler_method):
        """Decorator to provide controller with proper DB session management"""
        def wrapper(*args, **kwargs):
            with get_db_context() as db:
                agent_repo = PostgresAgentRepository(db)
                agent_service = AgentService(agent_repo)
                controller = AgentController(agent_service)
                return getattr(controller, handler_method)(*args, **kwargs)
        wrapper.__name__ = handler_method
        return wrapper
    
    # Helper for conversation endpoint within agent context
    def with_conversation_controller(handler_method):
        """Decorator for conversation endpoints in agent context"""
        def wrapper(*args, **kwargs):
            with get_db_context() as db:
                conversation_repo = PostgresConversationRepository(db)
                message_repo = PostgresMessageRepository(db)
                user_repo = PostgresUserRepository(db)
                agent_repo = PostgresAgentRepository(db)
                ai_service = VertexAIService()
                
                conversation_service = ConversationService(
                    conversation_repo=conversation_repo,
                    message_repo=message_repo,
                    user_repo=user_repo,
                    ai_service=ai_service,
                    agent_repo=agent_repo
                )
                controller = ConversationController(conversation_service)
                return getattr(controller, handler_method)(*args, **kwargs)
        wrapper.__name__ = handler_method
        return wrapper

    # Register routes with session management
    bp.route('', methods=['POST'])(with_agent_controller('create_agent'))
    bp.route('/<int:agent_id>', methods=['GET'])(with_agent_controller('get_agent'))
    bp.route('/<int:agent_id>', methods=['PUT'])(with_agent_controller('update_agent'))
    bp.route('/<int:agent_id>', methods=['DELETE'])(with_agent_controller('delete_agent'))
    bp.route('/name/<name>', methods=['GET'])(with_agent_controller('get_agent_by_name'))
    bp.route('/type/<agent_type>', methods=['GET'])(with_agent_controller('get_agents_by_type'))
    bp.route('', methods=['GET'])(with_agent_controller('get_all_agents'))
    bp.route('/active', methods=['GET'])(with_agent_controller('get_active_agents'))
    
    # Conversation routes for agents
    bp.route('/<int:agent_id>/conversations', methods=['GET'])(
        with_conversation_controller('get_agent_conversations')
    )
    
    # User-Agent management routes
    bp.route('/<int:agent_id>/users', methods=['GET'])(with_agent_controller('get_agent_users'))
    bp.route('/<int:agent_id>/users', methods=['POST'])(with_agent_controller('add_users_to_agent'))
    bp.route('/<int:agent_id>/users', methods=['PUT'])(with_agent_controller('update_agent_users'))
    bp.route('/<int:agent_id>/users', methods=['DELETE'])(with_agent_controller('remove_users_from_agent'))

    return bp