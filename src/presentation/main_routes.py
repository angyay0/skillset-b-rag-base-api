from flask import Blueprint, jsonify
from src.infrastructure.database.connection import get_db_context
from src.infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from src.infrastructure.repositories.postgres_conversation_repository import (
    PostgresConversationRepository,
    PostgresMessageRepository
)
from src.infrastructure.database.metric_repository_impl import MetricRepositoryImpl
from src.infrastructure.ai.vertex_ai_service import VertexAIService
from src.application.services.chat_service import ChatService
from src.presentation.controllers.whatsapp_controller import WhatsAppController
from src.presentation.controllers.voice_controller import VoiceController

# Create blueprints
whatsapp_bp = Blueprint('whatsapp', __name__)
voice_bp = Blueprint('voice', __name__)
health_bp = Blueprint('health', __name__)


# WhatsApp routes
@whatsapp_bp.route('/webhook', methods=['GET', 'POST'])
def webhook_meta():
    """WhatsApp Business API webhook (Meta)"""
    with get_db_context() as db:
        user_repo = PostgresUserRepository(db)
        conversation_repo = PostgresConversationRepository(db)
        message_repo = PostgresMessageRepository(db)
        metric_repo = MetricRepositoryImpl(db)
        ai_service = VertexAIService()
        
        chat_service = ChatService(
            user_repo=user_repo,
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            ai_service=ai_service,
            metric_repo=metric_repo
        )
        controller = WhatsAppController(chat_service)
        return controller.webhook_meta()


@whatsapp_bp.route('/whatsapp/twilio', methods=['POST'])
def webhook_twilio():
    """WhatsApp webhook via Twilio"""
    with get_db_context() as db:
        user_repo = PostgresUserRepository(db)
        conversation_repo = PostgresConversationRepository(db)
        message_repo = PostgresMessageRepository(db)
        metric_repo = MetricRepositoryImpl(db)
        ai_service = VertexAIService()
        
        chat_service = ChatService(
            user_repo=user_repo,
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            ai_service=ai_service,
            metric_repo=metric_repo
        )
        controller = WhatsAppController(chat_service)
        return controller.webhook_twilio()


# Voice routes
@voice_bp.route('/voice/incoming', methods=['POST'])
def voice_incoming():
    """Handle incoming voice calls"""
    with get_db_context() as db:
        user_repo = PostgresUserRepository(db)
        conversation_repo = PostgresConversationRepository(db)
        message_repo = PostgresMessageRepository(db)
        metric_repo = MetricRepositoryImpl(db)
        ai_service = VertexAIService()
        
        chat_service = ChatService(
            user_repo=user_repo,
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            ai_service=ai_service,
            metric_repo=metric_repo
        )
        controller = VoiceController(chat_service)
        return controller.incoming()


@voice_bp.route('/voice/process', methods=['POST'])
def voice_process():
    """Process speech input"""
    with get_db_context() as db:
        user_repo = PostgresUserRepository(db)
        conversation_repo = PostgresConversationRepository(db)
        message_repo = PostgresMessageRepository(db)
        metric_repo = MetricRepositoryImpl(db)
        ai_service = VertexAIService()
        
        chat_service = ChatService(
            user_repo=user_repo,
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            ai_service=ai_service,
            metric_repo=metric_repo
        )
        controller = VoiceController(chat_service)
        return controller.process()


@voice_bp.route('/voice/status', methods=['POST'])
def voice_status():
    """Handle call status callbacks"""
    with get_db_context() as db:
        user_repo = PostgresUserRepository(db)
        conversation_repo = PostgresConversationRepository(db)
        message_repo = PostgresMessageRepository(db)
        metric_repo = MetricRepositoryImpl(db)
        ai_service = VertexAIService()
        
        chat_service = ChatService(
            user_repo=user_repo,
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            ai_service=ai_service,
            metric_repo=metric_repo
        )
        controller = VoiceController(chat_service)
        return controller.status()


# Health check route
@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "blinky-base-api"}), 200


def register_routes(app):
    """Register all blueprints with the app"""
    # Import here to avoid circular imports
    from src.presentation.routes.metrics_routes import create_metrics_blueprint
    from src.presentation.routes.dashboard_routes import create_dashboard_blueprint
    from src.presentation.routes.agent_routes import create_agent_blueprint
    from src.presentation.routes.user_routes import create_user_blueprint
    from src.presentation.routes.conversation_routes import create_conversation_blueprint

    app.register_blueprint(whatsapp_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(health_bp)

    # Register metrics, dashboard, agent, user and conversation blueprints
    metrics_bp = create_metrics_blueprint()
    dashboard_bp = create_dashboard_blueprint()
    agent_bp = create_agent_blueprint()
    user_bp = create_user_blueprint()
    conversation_bp = create_conversation_blueprint()
    app.register_blueprint(metrics_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(conversation_bp)
