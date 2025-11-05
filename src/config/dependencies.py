from functools import lru_cache
from src.infrastructure.database.connection import get_db
from src.infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from src.infrastructure.repositories.postgres_conversation_repository import (
    PostgresConversationRepository,
    PostgresMessageRepository
)
from src.infrastructure.database.metric_repository_impl import MetricRepositoryImpl
from src.infrastructure.ai.vertex_ai_service import VertexAIService
from src.application.services.chat_service import ChatService
from src.application.services.metrics_service import MetricsService
from src.presentation.controllers.whatsapp_controller import WhatsAppController
from src.presentation.controllers.voice_controller import VoiceController


@lru_cache()
def get_ai_service() -> VertexAIService:
    """Get AI service singleton"""
    return VertexAIService()


def get_chat_service() -> ChatService:
    """Get chat service with dependencies"""
    db = get_db()
    user_repo = PostgresUserRepository(db)
    conversation_repo = PostgresConversationRepository(db)
    message_repo = PostgresMessageRepository(db)
    metric_repo = MetricRepositoryImpl(db)
    ai_service = get_ai_service()
    
    return ChatService(
        user_repo=user_repo,
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        ai_service=ai_service,
        metric_repo=metric_repo
    )


def get_whatsapp_controller() -> WhatsAppController:
    """Get WhatsApp controller"""
    chat_service = get_chat_service()
    return WhatsAppController(chat_service)


def get_voice_controller() -> VoiceController:
    """Get voice controller"""
    chat_service = get_chat_service()
    return VoiceController(chat_service)


def get_metrics_service() -> MetricsService:
    """Get metrics service with dependencies"""
    db = get_db()
    metric_repo = MetricRepositoryImpl(db)
    return MetricsService(metric_repo, db)
