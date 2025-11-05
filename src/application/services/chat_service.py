from datetime import datetime
from typing import Optional
import os
import time
import traceback
from src.domain.entities.user import User
from src.domain.entities.conversation import Conversation, Message
from src.domain.entities.metric import Metric
from src.domain.repositories.user_repository import UserRepository
from src.domain.repositories.conversation_repository import ConversationRepository, MessageRepository
from src.domain.repositories.metric_repository import MetricRepository
from src.infrastructure.ai.vertex_ai_service import VertexAIService


class ChatService:
    """Service for handling chat interactions"""
    
    def __init__(
        self,
        user_repo: UserRepository,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        ai_service: VertexAIService,
        metric_repo: Optional[MetricRepository] = None
    ):
        self.user_repo = user_repo
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.ai_service = ai_service
        self.metric_repo = metric_repo
        # Get max output tokens from environment or use default
        self.max_output_tokens = int(os.getenv('MAX_OUTPUT_TOKENS', '110'))
    
    def process_message(
        self,
        phone_number: str,
        message_text: str,
        channel: str,
        language: str = 'es',
        metadata: Optional[dict] = None
    ) -> str:
        """Process incoming message and return AI response"""
        start_time = time.time()
        user = None
        conversation = None
        
        try:
            # Get user (don't create automatically)
            user = self.user_repo.get_by_phone(phone_number)
            #print(f"{phone_number}")
            if not user:
                self._log_metric(
                    metric_type='access_denied',
                    severity='medium',
                    message=f'Access denied for phone number: {phone_number}',
                    phone_number=phone_number,
                    channel=channel
                )
                return self._get_no_access_message(language)
            
            # Check if user is valid
            if not user.is_valid():
                self._log_metric(
                    metric_type='expired_user',
                    severity='medium',
                    message=f'Expired user attempted access: {phone_number}',
                    user_id=user.id,
                    phone_number=phone_number,
                    channel=channel
                )
                return self._get_expired_message(language, user)
            
            # Get or create conversation
            conversation = self.conversation_repo.get_by_user_and_channel(user.id, channel)
            if not conversation:
                conversation = self._create_conversation(user.id, channel)
            
            # Get conversation history for context
            history = self.message_repo.get_conversation_history(conversation.id, limit=5)
            context = self._build_context(history)
            
            # Generate AI response with configurable max tokens and timing
            ai_start_time = time.time()
            ai_response = self.ai_service.generate_response(
                question=message_text,
                context=context,
                language=user.language,
                max_output_tokens=self.max_output_tokens
            )
            response_time_ms = int((time.time() - ai_start_time) * 1000)
            
            # Save message with response time
            message = Message(
                id=None,
                conversation_id=conversation.id,
                user_message=message_text,
                assistant_response=ai_response,
                language=user.language,
                metadata=metadata,
                response_time_ms=response_time_ms,
                created_at=datetime.utcnow()
            )
            self.message_repo.create(message)
            
            # Log slow responses
            if response_time_ms > 5000:  # More than 5 seconds
                self._log_metric(
                    metric_type='warning',
                    severity='medium',
                    message=f'Slow AI response: {response_time_ms}ms',
                    user_id=user.id,
                    conversation_id=conversation.id,
                    phone_number=phone_number,
                    channel=channel,
                    error_details={'response_time_ms': response_time_ms}
                )
            
            return ai_response
            
        except Exception as e:
            # Log error with full context
            error_msg = f'Error processing message: {str(e)}'
            self._log_metric(
                metric_type='error',
                severity='high',
                message=error_msg,
                user_id=user.id if user else None,
                conversation_id=conversation.id if conversation else None,
                phone_number=phone_number,
                channel=channel,
                error_details={
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                    'message_text': message_text[:100]  # First 100 chars
                }
            )
            
            # Return user-friendly error message
            error_messages = {
                'es': 'Lo siento, ocurrió un error al procesar tu mensaje. Por favor, intenta de nuevo.',
                'en': 'Sorry, an error occurred while processing your message. Please try again.',
                'pt': 'Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.'
            }
            return error_messages.get(language, error_messages['es'])
    
    def _create_user(self, phone_number: str, language: str) -> User:
        """Create a new user"""
        user = User(
            id=None,
            phone_number=phone_number,
            name=None,
            language=language,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return self.user_repo.create(user)
    
    def _create_conversation(self, user_id: int, channel: str) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            id=None,
            user_id=user_id,
            channel=channel,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return self.conversation_repo.create(conversation)
    
    def _build_context(self, history: list[Message]) -> str:
        """Build context from conversation history"""
        if not history:
            return "Nueva conversación"
        
        context_parts = []
        for msg in reversed(history[-3:]):  # Last 3 messages
            context_parts.append(f"Usuario: {msg.user_message}")
            context_parts.append(f"Asistente: {msg.assistant_response}")
        
        return "\n".join(context_parts)
    
    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        return self.user_repo.get_by_phone(phone_number)
    
    def get_conversation_history(self, phone_number: str, channel: str, limit: int = 10) -> list[Message]:
        """Get conversation history for a user and channel"""
        user = self.user_repo.get_by_phone(phone_number)
        if not user:
            return []
        
        conversation = self.conversation_repo.get_by_user_and_channel(user.id, channel)
        if not conversation:
            return []
        
        return self.message_repo.get_conversation_history(conversation.id, limit)
    
    def _get_no_access_message(self, language: str) -> str:
        """Get message for users without access"""
        messages = {
            'es': 'Lo sentimos, no tienes acceso a este servicio. Por favor, contacta a tu administrador para obtener acceso.',
            'en': 'Sorry, you do not have access to this service. Please contact your administrator to get access.',
            'pt': 'Desculpe, você não tem acesso a este serviço. Entre em contato com seu administrador para obter acesso.'
        }
        return messages.get(language, messages['es'])
    
    def _get_expired_message(self, language: str, user: User) -> str:
        """Get message for users with expired access"""
        days_remaining = user.days_remaining()
        expiration_date = user.expiration_date()
        
        messages = {
            'es': f'Tu período de servicio ha expirado. Tu acceso venció el {expiration_date.strftime("%d/%m/%Y")}. Por favor, contacta a tu administrador para renovar tu suscripción.',
            'en': f'Your service period has expired. Your access expired on {expiration_date.strftime("%m/%d/%Y")}. Please contact your administrator to renew your subscription.',
            'pt': f'Seu período de serviço expirou. Seu acesso expirou em {expiration_date.strftime("%d/%m/%Y")}. Entre em contato com seu administrador para renovar sua assinatura.'
        }
        return messages.get(language, messages['es'])
    
    def _log_metric(
        self,
        metric_type: str,
        severity: str,
        message: str,
        user_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        phone_number: Optional[str] = None,
        channel: Optional[str] = None,
        error_details: Optional[dict] = None
    ):
        """Log a metric event"""
        if not self.metric_repo:
            return
        
        try:
            metric = Metric(
                id=None,
                metric_type=metric_type,
                severity=severity,
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                phone_number=phone_number,
                channel=channel,
                error_details=error_details,
                created_at=datetime.utcnow()
            )
            self.metric_repo.create(metric)
        except Exception as e:
            # Don't let metric logging break the main flow
            print(f"Error logging metric: {str(e)}")
