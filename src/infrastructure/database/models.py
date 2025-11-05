from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.infrastructure.database.connection import Base


class UserModel(Base):
    """User database model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    language = Column(String(10), default='es', nullable=False)
    validity_days = Column(Integer, default=30, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    conversations = relationship("ConversationModel", back_populates="user", cascade="all, delete-orphan")


class ConversationModel(Base):
    """Conversation database model"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    channel = Column(String(50), nullable=False)  # 'whatsapp', 'whatsapp_twilio', 'voice'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("UserModel", back_populates="conversations")
    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")


class MessageModel(Base):
    """Message database model"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    language = Column(String(10), nullable=False)
    message_metadata = Column(JSON, nullable=True)  # For storing message_sid, call_sid, etc.
    response_time_ms = Column(Integer, nullable=True)  # Response generation time in milliseconds
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    conversation = relationship("ConversationModel", back_populates="messages")


class MetricModel(Base):
    """Metrics database model for tracking errors and important events"""
    __tablename__ = 'metrics'
    
    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), nullable=False, index=True)  # 'error', 'warning', 'info', 'access_denied', 'expired_user'
    severity = Column(String(20), nullable=False, index=True)  # 'low', 'medium', 'high', 'critical'
    message = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True, index=True)
    phone_number = Column(String(20), nullable=True, index=True)  # For cases where user doesn't exist
    channel = Column(String(50), nullable=True)
    error_details = Column(JSON, nullable=True)  # Stack trace, error code, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("UserModel")
    conversation = relationship("ConversationModel")
