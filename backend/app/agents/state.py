from typing import TypedDict, List, Optional, Dict, Any
from enum import Enum

class AgentState(TypedDict):
    # Core ticket information
    ticket_id: int
    user_id: int
    query: str
    category: str
    subcategory_data: Optional[Dict[str, Any]]
    attachments: Optional[List[str]]
    
    # User course information
    user_course_category: Optional[str]
    user_course_name: Optional[str]
    
    # Workflow state
    current_step: str
    confidence_score: Optional[float]
    response: Optional[str]
    cached_response: Optional[str]
    retrieved_context: Optional[List[str]]
    
    # Routing information
    admin_type: Optional[str]  # "EC" or "IA"
    requires_escalation: bool
    missing_information: Optional[List[str]]
    
    # Context and metadata
    conversation_history: List[Dict[str, Any]]
    ticket_status: str
    error_message: Optional[str]

class WorkflowStep(Enum):
    ROUTING = "routing"
    CACHE_CHECK = "cache_check"
    RETRIEVAL = "retrieval"
    RESPONSE_GENERATION = "response_generation"
    ESCALATION = "escalation"
    COMPLETION = "completion"

    