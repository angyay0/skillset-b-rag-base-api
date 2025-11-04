from flask import Blueprint
from src.infrastructure.database.connection import get_db_context
from src.infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from src.infrastructure.repositories.postgres_conversation_repository import (
    PostgresConversationRepository,
    PostgresMessageRepository
)
from src.infrastructure.repositories.postgres_agent_repository import PostgresAgentRepository
from src.infrastructure.database.metric_repository_impl import MetricRepositoryImpl
from src.infrastructure.ai.vertex_ai_service import VertexAIService
from src.application.services.chat_service import ChatService
from src.application.services.agent_service import AgentService
from src.presentation.controllers.integration_controller import IntegrationController


def create_integration_blueprint():
    """Create and configure the integration blueprint"""
    bp = Blueprint('integrations', __name__, url_prefix='/api/integrations')
    
    def get_controller():
        """Get integration controller with dependencies"""
        db = get_db_context().__enter__()
        user_repo = PostgresUserRepository(db)
        conversation_repo = PostgresConversationRepository(db)
        message_repo = PostgresMessageRepository(db)
        agent_repo = PostgresAgentRepository(db)
        metric_repo = MetricRepositoryImpl(db)
        ai_service = VertexAIService()
        
        chat_service = ChatService(
            user_repo=user_repo,
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            ai_service=ai_service,
            metric_repo=metric_repo
        )
        agent_service = AgentService(agent_repo)
        
        return IntegrationController(chat_service, agent_service), db
    
    # Slack endpoints
    @bp.route('/<int:agent_id>/slack/webhook', methods=['POST'])
    def slack_webhook(agent_id):
        """Slack webhook endpoint for agent"""
        with get_db_context() as db:
            user_repo = PostgresUserRepository(db)
            conversation_repo = PostgresConversationRepository(db)
            message_repo = PostgresMessageRepository(db)
            agent_repo = PostgresAgentRepository(db)
            metric_repo = MetricRepositoryImpl(db)
            ai_service = VertexAIService()
            
            chat_service = ChatService(
                user_repo=user_repo,
                conversation_repo=conversation_repo,
                message_repo=message_repo,
                ai_service=ai_service,
                metric_repo=metric_repo
            )
            agent_service = AgentService(agent_repo)
            controller = IntegrationController(chat_service, agent_service)
            return controller.slack_webhook(agent_id)
    
    @bp.route('/<int:agent_id>/slack/oauth', methods=['GET'])
    def slack_oauth(agent_id):
        """Slack OAuth callback endpoint"""
        with get_db_context() as db:
            user_repo = PostgresUserRepository(db)
            conversation_repo = PostgresConversationRepository(db)
            message_repo = PostgresMessageRepository(db)
            agent_repo = PostgresAgentRepository(db)
            metric_repo = MetricRepositoryImpl(db)
            ai_service = VertexAIService()
            
            chat_service = ChatService(
                user_repo=user_repo,
                conversation_repo=conversation_repo,
                message_repo=message_repo,
                ai_service=ai_service,
                metric_repo=metric_repo
            )
            agent_service = AgentService(agent_repo)
            controller = IntegrationController(chat_service, agent_service)
            return controller.slack_oauth_callback(agent_id)
    
    # Teams endpoints
    @bp.route('/<int:agent_id>/teams/webhook', methods=['POST'])
    def teams_webhook(agent_id):
        """Microsoft Teams webhook endpoint for agent"""
        with get_db_context() as db:
            user_repo = PostgresUserRepository(db)
            conversation_repo = PostgresConversationRepository(db)
            message_repo = PostgresMessageRepository(db)
            agent_repo = PostgresAgentRepository(db)
            metric_repo = MetricRepositoryImpl(db)
            ai_service = VertexAIService()
            
            chat_service = ChatService(
                user_repo=user_repo,
                conversation_repo=conversation_repo,
                message_repo=message_repo,
                ai_service=ai_service,
                metric_repo=metric_repo
            )
            agent_service = AgentService(agent_repo)
            controller = IntegrationController(chat_service, agent_service)
            return controller.teams_webhook(agent_id)
    
    # Status endpoint
    @bp.route('/<int:agent_id>/status', methods=['GET'])
    def integration_status(agent_id):
        """Get integration status for agent"""
        with get_db_context() as db:
            user_repo = PostgresUserRepository(db)
            conversation_repo = PostgresConversationRepository(db)
            message_repo = PostgresMessageRepository(db)
            agent_repo = PostgresAgentRepository(db)
            metric_repo = MetricRepositoryImpl(db)
            ai_service = VertexAIService()
            
            chat_service = ChatService(
                user_repo=user_repo,
                conversation_repo=conversation_repo,
                message_repo=message_repo,
                ai_service=ai_service,
                metric_repo=metric_repo
            )
            agent_service = AgentService(agent_repo)
            controller = IntegrationController(chat_service, agent_service)
            return controller.get_integration_status(agent_id)
    
    return bp
