#!/usr/bin/env python
"""
Seed script to generate random conversations, messages, and metrics
for existing users and agents in the database.
"""
import sys
import os
import argparse
import random
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

# Load env BEFORE importing DB modules
load_dotenv(override=True)

from src.infrastructure.database.connection import get_db_context
from src.infrastructure.database.models import (
    AgentModel,
    ConversationModel,
    MessageModel,
    MetricModel,
    UserModel,
)


# Sample user messages for different categories
GREETING_MESSAGES = [
    "Hola",
    "Buenos días",
    "Buenas tardes",
    "Hola, necesito ayuda",
    "Hi there",
    "Hello",
]

SUPPORT_MESSAGES = [
    "Tengo un problema con mi cuenta",
    "No puedo acceder a mi perfil",
    "Mi pago no se procesó correctamente",
    "Necesito hablar con soporte",
    "¿Cómo puedo cambiar mi contraseña?",
    "¿Cuál es el horario de atención?",
    "¿Tienen soporte en español?",
    "I need help with my account",
    "How do I reset my password?",
    "Can you help me with billing?",
]

PRODUCT_MESSAGES = [
    "¿Cuánto cuesta el servicio premium?",
    "¿Qué planes tienen disponibles?",
    "¿Cuáles son las características del plan básico?",
    "¿Tienen descuentos para empresas?",
    "What are your pricing options?",
    "Do you offer a free trial?",
    "What features are included?",
]

GENERAL_MESSAGES = [
    "Gracias por la información",
    "Perfecto, eso es todo",
    "Una pregunta más",
    "No entiendo",
    "¿Puedes explicar mejor?",
    "Ok, gracias",
    "Thank you",
    "That helps, thanks",
]

# Sample assistant responses
ASSISTANT_RESPONSES = [
    "¡Hola! ¿En qué puedo ayudarte hoy?",
    "Claro, con gusto te ayudo con eso.",
    "Entiendo tu situación. Déjame revisar.",
    "Gracias por contactarnos. Te explico...",
    "Por supuesto, aquí está la información que necesitas.",
    "Lamento los inconvenientes. Vamos a solucionarlo.",
    "Excelente pregunta. Te comento...",
    "Perfecto, he procesado tu solicitud.",
    "¿Hay algo más en lo que pueda ayudarte?",
    "Gracias por tu paciencia. Ya está resuelto.",
]

# Metric types and severities
METRIC_TYPES = ["error", "warning", "info", "access_denied", "expired_user"]
SEVERITIES = ["low", "medium", "high", "critical"]

ERROR_MESSAGES = {
    "error": [
        "Failed to process AI response",
        "Database connection timeout",
        "External API call failed",
        "Message delivery failed",
        "Unexpected error in conversation handler",
    ],
    "warning": [
        "Slow response time detected",
        "Rate limit approaching",
        "User session about to expire",
        "High memory usage detected",
        "Retry attempt on message send",
    ],
    "info": [
        "New user registered",
        "Conversation started",
        "User upgraded plan",
        "Agent configuration updated",
        "Daily report generated",
    ],
    "access_denied": [
        "Phone number not registered",
        "User subscription expired",
        "Invalid authentication token",
        "User not assigned to agent",
        "Access blocked by admin",
    ],
    "expired_user": [
        "User validity period expired",
        "Subscription ended",
        "Trial period over",
        "Account deactivated due to expiry",
    ],
}


def get_random_message():
    """Get a random user message from various categories"""
    all_messages = GREETING_MESSAGES + SUPPORT_MESSAGES + PRODUCT_MESSAGES + GENERAL_MESSAGES
    return random.choice(all_messages)


def get_random_response():
    """Get a random assistant response"""
    return random.choice(ASSISTANT_RESPONSES)


def seed_conversations_and_messages(
    db,
    users: list,
    days: int,
    conversations_per_user: int,
    messages_per_conversation: int,
):
    """Create conversations and messages for existing users"""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    channels = ["whatsapp", "whatsapp_twilio", "voice"]
    languages = ["es", "en", "pt"]
    
    conversations_created = 0
    messages_created = 0
    
    for user in users:
        for _ in range(conversations_per_user):
            # Random conversation start time
            conv_start_seconds = random.randint(0, int((now - start).total_seconds()))
            conv_start = start + timedelta(seconds=conv_start_seconds)
            
            conv = ConversationModel(
                user_id=user.id,
                channel=random.choice(channels),
                is_active=random.random() > 0.2,  # 80% active
                created_at=conv_start,
            )
            db.add(conv)
            db.flush()
            conversations_created += 1
            
            # Create messages for this conversation
            message_time = conv_start
            for msg_idx in range(messages_per_conversation):
                # Messages spaced 1-30 minutes apart
                message_time += timedelta(minutes=random.randint(1, 30))
                
                # Don't create messages in the future
                if message_time > now:
                    break
                
                # Simulate response time (50ms to 5000ms, with occasional slow ones)
                response_time_ms = int(max(50, random.gauss(1500, 800)))
                if random.random() < 0.08:  # 8% slow responses
                    response_time_ms = random.randint(5000, 15000)
                
                msg = MessageModel(
                    conversation_id=conv.id,
                    user_message=get_random_message(),
                    assistant_response=get_random_response(),
                    language=user.language or random.choice(languages),
                    response_time_ms=response_time_ms,
                    message_metadata={"seed": True, "message_index": msg_idx},
                    created_at=message_time,
                )
                db.add(msg)
                messages_created += 1
    
    return conversations_created, messages_created


def seed_metrics(
    db,
    users: list,
    conversations: list,
    days: int,
    metrics_count: int,
):
    """Create metrics for existing users and conversations"""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    channels = ["whatsapp", "whatsapp_twilio", "voice"]
    
    metrics_created = 0
    
    for _ in range(metrics_count):
        metric_type = random.choice(METRIC_TYPES)
        severity = random.choice(SEVERITIES)
        
        # Higher severity for errors
        if metric_type == "error":
            severity = random.choice(["medium", "high", "critical"])
        elif metric_type == "info":
            severity = random.choice(["low", "medium"])
        
        message = random.choice(ERROR_MESSAGES.get(metric_type, ["Unknown event"]))
        
        # Random timestamp within the period
        delta_seconds = random.randint(0, int((now - start).total_seconds()))
        created_at = start + timedelta(seconds=delta_seconds)
        
        # Link to user/conversation for some metrics
        user_id = None
        conversation_id = None
        phone_number = None
        channel = random.choice(channels)
        
        if metric_type in ["error", "warning", "info"] and users and random.random() > 0.3:
            user = random.choice(users)
            user_id = user.id
            if conversations and random.random() > 0.5:
                user_convs = [c for c in conversations if c.user_id == user.id]
                if user_convs:
                    conversation_id = random.choice(user_convs).id
        elif metric_type in ["access_denied", "expired_user"]:
            # These often have phone numbers but might not have user_id
            if random.random() > 0.5 and users:
                user = random.choice(users)
                user_id = user.id
                phone_number = user.phone_number
            else:
                phone_number = f"+52{random.randint(1000000000, 9999999999)}"
        
        metric = MetricModel(
            metric_type=metric_type,
            severity=severity,
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            phone_number=phone_number,
            channel=channel,
            error_details={"seed": True, "generated_at": now.isoformat()},
            created_at=created_at,
        )
        db.add(metric)
        metrics_created += 1
    
    return metrics_created


def main():
    parser = argparse.ArgumentParser(
        description="Seed random data for conversations, messages, and metrics using existing users/agents"
    )
    parser.add_argument("--days", type=int, default=30, help="Number of days to spread data across (default: 30)")
    parser.add_argument("--conversations-per-user", type=int, default=3, help="Conversations per user (default: 3)")
    parser.add_argument("--messages-per-conversation", type=int, default=10, help="Messages per conversation (default: 10)")
    parser.add_argument("--metrics", type=int, default=50, help="Number of metrics to generate (default: 50)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without actually creating")
    args = parser.parse_args()
    
    random.seed(args.seed)
    
    print("=" * 50)
    print("Seed Data Script")
    print("=" * 50)
    
    with get_db_context() as db:
        # Get existing users and agents
        users = db.query(UserModel).filter(UserModel.is_active == True).all()
        agents = db.query(AgentModel).filter(AgentModel.is_active == True).all()
        
        if not users:
            print("❌ No active users found in database. Please create users first.")
            return
        
        print(f"\n📊 Found {len(users)} active users and {len(agents)} active agents")
        print(f"\nConfiguration:")
        print(f"  - Days: {args.days}")
        print(f"  - Conversations per user: {args.conversations_per_user}")
        print(f"  - Messages per conversation: {args.messages_per_conversation}")
        print(f"  - Metrics to generate: {args.metrics}")
        print(f"  - Random seed: {args.seed}")
        
        if args.dry_run:
            print("\n🔍 DRY RUN - No data will be created")
            total_convs = len(users) * args.conversations_per_user
            total_msgs = total_convs * args.messages_per_conversation
            print(f"\nWould create:")
            print(f"  - ~{total_convs} conversations")
            print(f"  - ~{total_msgs} messages")
            print(f"  - {args.metrics} metrics")
            return
        
        print("\n🔄 Creating conversations and messages...")
        convs_created, msgs_created = seed_conversations_and_messages(
            db,
            users,
            args.days,
            args.conversations_per_user,
            args.messages_per_conversation,
        )
        
        # Get all conversations for metrics
        conversations = db.query(ConversationModel).all()
        
        print("🔄 Creating metrics...")
        metrics_created = seed_metrics(
            db,
            users,
            conversations,
            args.days,
            args.metrics,
        )
        
        db.commit()
        
        print("\n✅ Seed completed successfully!")
        print(f"\nCreated:")
        print(f"  - {convs_created} conversations")
        print(f"  - {msgs_created} messages")
        print(f"  - {metrics_created} metrics")


if __name__ == "__main__":
    main()
