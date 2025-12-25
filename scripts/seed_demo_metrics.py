import argparse
import os
import random
from datetime import datetime, timedelta

from dotenv import load_dotenv

# Load env BEFORE importing DB modules
load_dotenv(override=True)

from src.infrastructure.database.connection import get_db_context
from src.infrastructure.database.models import ConversationModel, MessageModel, MetricModel, UserModel


def _rand_phone(mx_country_prefix: str = "+521") -> str:
    return f"{mx_country_prefix}{random.randint(1000000000, 9999999999)}"


def seed_demo(days: int, users: int, conversations_per_user: int, messages_per_conversation: int, seed: int) -> None:
    random.seed(seed)

    now = datetime.utcnow()
    start = now - timedelta(days=days)

    # A small pool of repeated questions so frequent-questions is populated (requires count > 1)
    repeated_questions = [
        "como cambio mi contraseña?",
        "cual es el precio?",
        "como puedo hablar con un humano?",
        "tienen soporte 24/7?",
        "no me llega el codigo de verificacion",
        "quiero cancelar mi suscripcion",
    ]

    varied_questions = [
        "hola",
        "necesito soporte",
        "me ayudas con mi cuenta?",
        "como funciona esto?",
        "quiero informacion",
        "gracias",
    ]

    with get_db_context() as db:
        # Create demo users + conversations
        created_users: list[UserModel] = []
        for i in range(users):
            phone = _rand_phone()
            user = UserModel(
                phone_number=phone,
                name=f"Demo User {i+1}",
                language="es",
                validity_days=30,
                is_active=True,
            )
            db.add(user)
            created_users.append(user)

        db.flush()  # allocate IDs

        conversations: list[ConversationModel] = []
        channels = ["whatsapp", "whatsapp_twilio", "voice"]
        for user in created_users:
            for _ in range(conversations_per_user):
                conv = ConversationModel(
                    user_id=user.id,
                    channel=random.choice(channels),
                    is_active=True,
                )
                db.add(conv)
                conversations.append(conv)

        db.flush()

        # Create messages spread across days/hours with varied response_time_ms
        for conv in conversations:
            for _ in range(messages_per_conversation):
                # Spread timestamps across [start, now]
                delta_seconds = random.randint(0, int((now - start).total_seconds()))
                created_at = start + timedelta(seconds=delta_seconds)

                # Mix repeated and random questions
                if random.random() < 0.55:
                    user_message = random.choice(repeated_questions)
                else:
                    user_message = random.choice(varied_questions)

                response_time_ms = int(max(50, random.gauss(1800, 900)))
                # Add some slow responses to populate slow_responses_24h
                if random.random() < 0.12:
                    response_time_ms = random.randint(5200, 12000)

                msg = MessageModel(
                    conversation_id=conv.id,
                    user_message=user_message,
                    assistant_response="demo response",
                    language="es",
                    response_time_ms=response_time_ms,
                    created_at=created_at,
                )
                db.add(msg)

                # Create some warning/error metrics tied to conversation/user
                if random.random() < 0.10:
                    metric = MetricModel(
                        metric_type=random.choice(["warning", "error"]),
                        severity=random.choice(["low", "medium", "high"]),
                        message="Demo metric generated",
                        user_id=conv.user_id,
                        conversation_id=conv.id,
                        phone_number=None,
                        channel=conv.channel,
                        error_details={"seed": True},
                        created_at=created_at,
                    )
                    db.add(metric)

        # Create access_denied metrics with phone numbers NOT present in users
        for _ in range(max(3, users)):
            created_at = start + timedelta(seconds=random.randint(0, int((now - start).total_seconds())))
            metric = MetricModel(
                metric_type="access_denied",
                severity=random.choice(["medium", "high"]),
                message="Phone not registered",
                user_id=None,
                conversation_id=None,
                phone_number=_rand_phone(),
                channel="whatsapp",
                error_details={"reason": "not_in_users", "seed": True},
                created_at=created_at,
            )
            db.add(metric)

        db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data for metrics dashboard")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--users", type=int, default=5)
    parser.add_argument("--conversations-per-user", type=int, default=2)
    parser.add_argument("--messages-per-conversation", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    seed_demo(
        days=args.days,
        users=args.users,
        conversations_per_user=args.conversations_per_user,
        messages_per_conversation=args.messages_per_conversation,
        seed=args.seed,
    )

    print("✓ Demo seed completed")
    print(f"  - days: {args.days}")
    print(f"  - users: {args.users}")
    print(f"  - conversations/user: {args.conversations_per_user}")
    print(f"  - messages/conversation: {args.messages_per_conversation}")


if __name__ == "__main__":
    main()
