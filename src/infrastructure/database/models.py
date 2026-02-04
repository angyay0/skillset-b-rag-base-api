from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.infrastructure.database.connection import Base

# Association table for many-to-many relationship between users and agents
user_agents = Table('user_agents', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('agent_id', Integer, ForeignKey('agents.id'), primary_key=True)
)


class UserModel(Base):
    """User database model"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    language = Column(String(10), default='es', nullable=False)
    validity_days = Column(Integer, default=30, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Subscription plan fields
    subscription_plan = Column(String(50), default='free', nullable=False)
    subscription_start_date = Column(DateTime(timezone=True), nullable=True)
    subscription_end_date = Column(DateTime(timezone=True), nullable=True)
    max_messages_per_month = Column(Integer, default=100, nullable=False)
    max_agents = Column(Integer, default=1, nullable=False)
    
    # Profile fields (from frontend form)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    company_name = Column(String(200), nullable=True)
    team_size = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    primary_use_case = Column(String(200), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    conversations = relationship("ConversationModel", back_populates="user", cascade="all, delete-orphan")
    agents = relationship("AgentModel", secondary=user_agents, back_populates="users")


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


class ReportRequestModel(Base):
    """Report request database model"""
    __tablename__ = 'report_requests'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), index=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=True, index=True)
    metrics = Column(JSON, nullable=False)
    period_days = Column(Integer, nullable=False)
    format = Column(String(20), nullable=False)
    requested_for = Column(Text, nullable=True)
    requested_by = Column(String(255), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='pending', index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    agent = relationship("AgentModel")


class AgentModel(Base):
    """Agent database model"""
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    configuration = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, server_default='true', nullable=False)
    auto_respond = Column(Boolean, default=True, server_default='true', nullable=False)
    learning_mode = Column(Boolean, default=False, server_default='false', nullable=False)
    response_temperature = Column(String(10), default='0.7', server_default='0.7', nullable=False)
    max_response_tokens = Column(Integer, default=300, server_default='300', nullable=False)
    system_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    users = relationship("UserModel", secondary=user_agents, back_populates="agents")
