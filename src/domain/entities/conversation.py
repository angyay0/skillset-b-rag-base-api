from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Conversation:
    """Conversation entity"""
    id: Optional[int]
    user_id: int
    channel: str  # 'whatsapp', 'whatsapp_twilio', 'voice'
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


@dataclass
class Message:
    """Message entity"""
    id: Optional[int]
    conversation_id: int
    user_message: str
    assistant_response: str
    language: str
    created_at: datetime
    metadata: Optional[dict] = None  # For storing message_sid, call_sid, etc.
    response_time_ms: Optional[int] = None  # Time taken to generate response in milliseconds
