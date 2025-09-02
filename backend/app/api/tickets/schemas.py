from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel

class TicketCreateRequest(BaseModel):
    category: str
    title: str
    message: str
    subcategory_data: Optional[Dict[str, Any]] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    attachments: Optional[List[str]] = None

class TicketResponse(BaseModel):
    id: str
    user_id: str
    category: str
    status: str
    title: str
    message: str
    subcategory_data: Optional[Dict[str, Any]]
    from_date: Optional[str]
    to_date: Optional[str]
    attachments: Optional[List[str]]
    assigned_to: Optional[str]
    rating: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class TicketListResponse(BaseModel):
    id: str
    user_id: str
    category: str
    status: str
    title: str
    created_at: datetime
    updated_at: Optional[datetime]
    rating: Optional[float]
    assigned_to: Optional[str]
    assigned_admin_email: Optional[str] = None  # Will be populated from join
    response_count: int = 0  # Count of conversations
    last_response: Optional[str] = None  # Last conversation message
    last_response_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: str
    ticket_id: str
    sender_role: str
    sender_id: Optional[str]
    message: Optional[str] = None
    confidence_score: Optional[float]
    timestamp: datetime
    sender_email: Optional[str] = None  # For display purposes
    
    class Config:
        from_attributes = True

class TicketDetailResponse(BaseModel):
    ticket: TicketResponse
    conversations: List[ConversationResponse]

class TicketRatingRequest(BaseModel):
    rating: float  # 1-5 star rating

# For ticket reopening - just reopen the same ticket, don't need additional message
class TicketReopenResponse(BaseModel):
    message: str
    ticket_id: str
    status: str

class TicketMessageRequest(BaseModel):
    message: str
    attachments: Optional[List[str]] = None