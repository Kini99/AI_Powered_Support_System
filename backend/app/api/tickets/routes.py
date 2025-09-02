from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Dict, Any
from backend.app.models import user_service, ticket_service, conversation_service, TicketStatus
from backend.app.core.deps import get_current_user, get_current_student, get_current_admin
from .schemas import (
    TicketCreateRequest, TicketMessageRequest, TicketResponse, TicketListResponse, 
    TicketDetailResponse, ConversationResponse, TicketRatingRequest,
    TicketReopenResponse
)
from backend.app.agents.langgraph_workflow import process_ticket_async

router = APIRouter()

# -------------------------------
# STUDENT: Create a new ticket
# -------------------------------
@router.post("/create", response_model=dict)
async def create_ticket(
    ticket_data: TicketCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_student)
):
    # Student creates a new ticket with details
    ticket_id = ticket_service.create_ticket(
        user_id=current_user["id"],
        category=ticket_data.category,
        title=ticket_data.title,
        message=ticket_data.message,
        subcategory_data=ticket_data.subcategory_data,
        from_date=ticket_data.from_date,
        to_date=ticket_data.to_date,
        attachments=ticket_data.attachments or []
    )
    
    # Add the first message to the ticket's conversation
    conversation_service.create_conversation(
        ticket_id=ticket_id,
        sender_role="student",
        sender_id=current_user["id"],
        message=ticket_data.message
    )
    
    # Start background processing for the ticket (AI workflow)
    background_tasks.add_task(process_ticket_async, ticket_id)
    
    return {
        "message": "Ticket submitted successfully",
        "ticket_id": f"TKT-{ticket_id}"
    }

@router.post("/{ticket_id}/messages", response_model=ConversationResponse)
async def add_message_to_ticket(
    ticket_id: str,
    message_data: TicketMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    ticket = ticket_service.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Check if the user is authorized to add messages to this ticket
    # Students can only add messages to their own tickets
    # Admins can add messages to any assigned or unassigned ticket
    if current_user["role"] == "student" and ticket["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add messages to this ticket"
        )
    
    # If admin, check if assigned or unassigned
    if current_user["role"] == "admin" and \
       ticket.get("assigned_to") is not None and \
       ticket.get("assigned_to") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add messages to this ticket"
        )

    # Create conversation entry
    conv_id = conversation_service.create_conversation(
        ticket_id=ticket_id,
        sender_role=current_user["role"],
        sender_id=current_user["id"],
        message=message_data.message,
        attachments=message_data.attachments or []
    )

    # Update ticket's updated_at timestamp
    ticket_service.update_ticket_timestamp(ticket_id)

    # Process ticket through LangGraph workflow in background
    if current_user["role"] == "student":
        background_tasks.add_task(process_ticket_async, ticket_id)

    # Fetch the newly created conversation to return
    new_conv = conversation_service.get_conversation_by_id(conv_id)
    sender_email = None
    if new_conv.get("sender_id"):
        sender = user_service.get_user_by_id(new_conv["sender_id"])
        if sender:
            sender_email = sender["email"]

    return ConversationResponse(
        id=new_conv["id"],
        ticket_id=new_conv["ticket_id"],
        sender_role=new_conv["sender_role"],
        sender_id=new_conv.get("sender_id"),
        message=new_conv["message"],
        confidence_score=new_conv.get("confidence_score"),
        timestamp=new_conv["timestamp"],
        sender_email=sender_email
    )

@router.get("/my_tickets", response_model=List[TicketListResponse])
async def get_my_tickets(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # Get user tickets
    tickets = ticket_service.get_user_tickets(current_user["id"], current_user["role"])
    
    result = []
    for ticket in tickets:
        # Get number of responses and last message for each ticket
        response_count = conversation_service.get_conversation_count(ticket["id"])
        last_conversation = conversation_service.get_last_conversation(ticket["id"])
        
        # Get assigned admin's email if ticket is assigned
        assigned_admin_email = None
        if ticket.get("assigned_to"):
            admin = user_service.get_user_by_id(ticket["assigned_to"])
            if admin:
                assigned_admin_email = admin["email"]
        
        result.append(TicketListResponse(
            id=ticket["id"],
            user_id=ticket["user_id"],
            category=ticket["category"],
            status=ticket["status"],
            title=ticket["title"],
            created_at=ticket["created_at"],
            updated_at=ticket.get("updated_at"),
            rating=ticket.get("rating"),
            assigned_to=ticket.get("assigned_to"),
            assigned_admin_email=assigned_admin_email,
            response_count=response_count,
            last_response=last_conversation["message"] if last_conversation else None,
            last_response_time=last_conversation["timestamp"] if last_conversation else None
        ))
    
    return result

# -------------------------------------------------
# STUDENT or ADMIN: Get details of a specific ticket
# -------------------------------------------------
@router.get("/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket_detail(
    ticket_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # Fetch ticket details by ID
    ticket = ticket_service.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Only the student who created the ticket or the assigned admin can view
    if (current_user["role"] == "student" and ticket["user_id"] != current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this ticket"
        )
    
    if (current_user["role"] == "admin" and 
        ticket.get("assigned_to") != current_user["id"] and 
        ticket.get("assigned_to") is not None):
        # Allow admins to see unassigned tickets
        pass
    
    # Get all conversations/messages for this ticket
    conversations = conversation_service.get_ticket_conversations(ticket_id)
    
    conversations_response = []
    for conv in conversations:
        sender_email = None
        if conv.get("sender_id"):
            sender = user_service.get_user_by_id(conv["sender_id"])
            if sender:
                sender_email = sender["email"]
        
        conversations_response.append(ConversationResponse(
            id=conv["id"],
            ticket_id=conv["ticket_id"],
            sender_role=conv["sender_role"],
            sender_id=conv.get("sender_id"),
            message=conv["message"],
            confidence_score=conv.get("confidence_score"),
            timestamp=conv["timestamp"],
            sender_email=sender_email
        ))
    
    return TicketDetailResponse(
        ticket=TicketResponse(
            id=ticket["id"],
            user_id=ticket["user_id"],
            category=ticket["category"],
            status=ticket["status"],
            title=ticket["title"],
            message=ticket["message"],
            subcategory_data=ticket.get("subcategory_data"),
            from_date=ticket.get("from_date"),
            to_date=ticket.get("to_date"),
            attachments=ticket.get("attachments", []),
            assigned_to=ticket.get("assigned_to"),
            rating=ticket.get("rating"),
            created_at=ticket["created_at"],
            updated_at=ticket.get("updated_at")
        ),
        conversations=conversations_response
    )

# -------------------------------------------
# STUDENT: Reopen a resolved ticket
# -------------------------------------------
@router.post("/{ticket_id}/reopen", response_model=TicketReopenResponse)
async def reopen_ticket(
    ticket_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_student)
):
    # Student can reopen their own resolved ticket
    ticket = ticket_service.get_ticket_by_id(ticket_id)
    if not ticket or ticket["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    if ticket["status"] != TicketStatus.RESOLVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only resolved tickets can be reopened"
        )
    
    # Change ticket status to open
    ticket_service.update_ticket_status(ticket_id, TicketStatus.OPEN.value, None)
    
    # Add a message indicating the ticket was reopened
    conversation_service.create_conversation(
        ticket_id=ticket_id,
        sender_role="student",
        sender_id=current_user["id"],
        message="Ticket reopened by student"
    )
    
    # Start background processing for the reopened ticket
    # background_tasks.add_task(process_ticket_async, ticket_id)
    
    return TicketReopenResponse(
        message="Ticket reopened successfully. Send new messages to continue the conversation.",
        ticket_id=ticket_id,
        status=TicketStatus.OPEN.value
    )

# -------------------------------------------
# STUDENT: Rate a resolved ticket
# -------------------------------------------
@router.post("/{ticket_id}/rate", response_model=dict)
async def rate_ticket(
    ticket_id: str,
    rating_data: TicketRatingRequest,
    current_user: Dict[str, Any] = Depends(get_current_student)
):
    # Student can rate their own resolved ticket
    ticket = ticket_service.get_ticket_by_id(ticket_id)
    if not ticket or ticket["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    if ticket["status"] != TicketStatus.RESOLVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only resolved tickets can be rated"
        )
    
    # Save the rating for the ticket
    ticket_service.rate_ticket(ticket_id, rating_data.rating)
    
    return {"message": "Rating submitted successfully"}