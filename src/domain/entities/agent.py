from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


# Default system prompts by agent type
AGENT_TYPE_PROMPTS = {
    'customer_support': """You are a helpful customer support assistant. Your role is to:
- Answer customer questions clearly and professionally
- Help resolve issues and complaints
- Provide accurate information about products and services
- Escalate complex issues when necessary
Always be polite, patient, and solution-oriented.""",
    
    'sales': """You are a friendly sales assistant. Your role is to:
- Help customers find the right products or services
- Provide pricing and availability information
- Answer questions about features and benefits
- Guide customers through the purchase process
Be helpful without being pushy, and focus on customer needs.""",
    
    'general': """You are a helpful AI assistant. Your role is to:
- Answer questions accurately and helpfully
- Provide clear and concise information
- Assist with various tasks as needed
Be friendly, professional, and informative.""",
    
    'technical': """You are a technical support specialist. Your role is to:
- Help diagnose and resolve technical issues
- Provide step-by-step troubleshooting guidance
- Explain technical concepts in understandable terms
- Document issues for escalation when needed
Be patient and thorough in your explanations."""
}


@dataclass
class Agent:
    """Agent entity for managing AI agents"""
    id: Optional[int]
    name: str
    type: str
    description: Optional[str]
    configuration: Optional[Dict[str, Any]]
    is_active: bool = True
    auto_respond: bool = True
    learning_mode: bool = False
    response_temperature: float = 0.7
    max_response_tokens: int = 300
    system_prompt: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    users: List['User'] = field(default_factory=list)
    
    def __post_init__(self):
        """Set default system prompt based on agent type if not provided"""
        if self.system_prompt is None:
            self.system_prompt = AGENT_TYPE_PROMPTS.get(self.type, AGENT_TYPE_PROMPTS['general'])
    
    def get_effective_system_prompt(self) -> str:
        """Get the effective system prompt (custom or type-based default)"""
        if self.system_prompt:
            return self.system_prompt
        return AGENT_TYPE_PROMPTS.get(self.type, AGENT_TYPE_PROMPTS['general'])