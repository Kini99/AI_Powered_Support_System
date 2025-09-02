from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from backend.app.models import user_service, ticket_service, conversation_service, TicketStatus
from backend.app.core.deps import get_current_admin, get_document_service
from backend.app.api.tickets.schemas import TicketListResponse, TicketDetailResponse, ConversationResponse, TicketResponse
from backend.app.services.document_service import DocumentService
import logging
from .schemas import AnalyticsResponse
from backend.app.services.analytics_service import analytics_service
import json 

logger = logging.getLogger(__name__)
router = APIRouter()
    
# --------------------------------------------------------------------------
# NOTE on Ticket Listing:
# The original code had an "N+1" query problem, causing many database calls.
# This improved version assumes the ticket_service has a more efficient method
# like `get_admin_tickets_with_details` that fetches all required data 
# (ticket info, conversation counts, user details) in a single, optimized query.
# --------------------------------------------------------------------------
@router.get("/tickets", response_model=List[TicketListResponse])
async def get_admin_tickets(
    status_filter: Optional[str] = None,
    admin_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_admin)
):
    """Get all tickets that can be viewed by the admin."""
    
    # This single service call is assumed to efficiently fetch all data
    tickets_with_details = ticket_service.get_admin_tickets_with_details(
        admin_id=current_user["id"],
        admin_type=admin_type,
        status_filter=status_filter
    )
    
    # The response from the service should already be structured for the API
    return [TicketListResponse(**ticket) for ticket in tickets_with_details]

@router.post("/tickets/{ticket_id}/respond")
async def respond_to_ticket(
    ticket_id: str,
    message: str = Form(...),
    current_user: Dict[str, Any] = Depends(get_current_admin)
):
    """Admin responds to a ticket, setting status to Work in Progress"""
    
    ticket = ticket_service.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Update ticket status to Work in Progress
    new_status = TicketStatus.WIP.value
    ticket_service.update_ticket_status(ticket_id, new_status, current_user["id"])
    
    conversation_service.create_conversation(
        ticket_id=ticket_id,
        sender_role="admin",
        sender_id=current_user["id"],
        message=message
    )
    
    return {
        "message": "Response submitted successfully",
        "ticket_status": new_status
    }

@router.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    message: str = Form(...),
    current_user: Dict[str, Any] = Depends(get_current_admin)
):
    """Admin resolves a ticket"""
    
    # Get ticket
    ticket = ticket_service.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Update ticket status to Resolved
    new_status = TicketStatus.RESOLVED.value
    ticket_service.update_ticket_status(ticket_id, new_status, current_user["id"])

    # Log human resolved event
    analytics_service.log_event("human_resolved")
    
    try:
        # Get original query from first conversation
        conversations = conversation_service.get_ticket_conversations(ticket_id)
        original_conv = next((c for c in conversations if c["sender_role"] == "student"), None)
        
        last_admin_msg = None
        for c in reversed(conversations):  # reverse so we get latest first
            if c["sender_role"] == "admin":
                last_admin_msg = c["message"]
                break
        print('Last admin msg being cached', original_conv["message"], last_admin_msg)
        if original_conv and last_admin_msg:
            from backend.app.agents.cache_service import SemanticCacheService
            cache_service = SemanticCacheService()
            
            # Fetch user details to get course info
            user = user_service.get_user_by_id(ticket["user_id"])
            user_course_category = user.get("course_category") if user else None
            user_course_name = user.get("course_name") if user else None
            
            await cache_service.store_response(
                query=original_conv["message"],
                response=last_admin_msg,
                confidence=0.95,  # High confidence for human responses
                category=ticket["category"],
                metadata={
                    "course_category": user_course_category,
                    "course_names": user_course_name
                }
            )
            
            # Store in Pinecone using the same helper
            from backend.app.services.document_service import DocumentService
            doc_service = DocumentService()

            await doc_service._store_in_pinecone(
                index=doc_service._get_index("qa_documents"),
                doc_id=f"ticket_{ticket_id}",
                chunks=[original_conv["message"]],
                category="qa_documents",
                filename=f"ticket_{ticket_id}_qa",
                metadata_list=[{
                    "potential_response": last_admin_msg
                }],
                course_categories=[user_course_category],
                course_names=[user_course_name]
            )

            print(f"Stored ticket Q&A in Pinecone for ticket {ticket_id}")
            
    except Exception as e:
        logger.error(f"Error storing admin response in cache: {str(e)}")
    
    # Add conversation entry
    conversation_service.create_conversation(
        ticket_id=ticket_id,
        sender_role="admin",
        sender_id=current_user["id"],
        message=message
    )
    
    if status == "Resolved":
        analytics_service.log_event('human_resolved', {'category': ticket.get("category")})
    
    return {
        "message": "Ticket resolved successfully",
        "ticket_status": new_status
    }

@router.post("/documents/upload")
async def upload_document(
    categories: str = Form(...), # Changed from 'category'
    course_categories: Optional[str] = Form(None), # Changed from 'course_category'
    course_names: Optional[str] = Form(None),
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
    current_user: Dict[str, Any] = Depends(get_current_admin)
):
    """Upload a document to the knowledge base under multiple categories."""
    logger.info(f"Uploading document '{file.filename}' to categories '{categories}'.")
    try:
        # Parse categories, course categories, and course names from JSON strings
        parsed_categories = []
        parsed_course_categories = None
        parsed_course_names = None

        try:
            parsed_categories = json.loads(categories)
            if not isinstance(parsed_categories, list) or not parsed_categories:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Categories must be a non-empty JSON array of strings."
                )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid categories format. Must be a valid JSON array."
            )

        if course_categories:
            try:
                parsed_course_categories = json.loads(course_categories)
                if not isinstance(parsed_course_categories, list):
                     raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="course_categories must be a valid JSON array."
                    )
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid course_categories format. Must be a valid JSON array."
                )

        if course_names:
            try:
                parsed_course_names = json.loads(course_names)
                if not isinstance(parsed_course_names, list):
                     raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="course_names must be a valid JSON array."
                    )
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid course_names format. Must be a valid JSON array."
                )
        
        # Use the injected service instance.
        result = await document_service.upload_document(
            file, 
            parsed_categories, 
            parsed_course_categories, 
            parsed_course_names
        )
        return {
            "message": "Document uploaded successfully",
            "document_id": result["document_id"],
            "categories": result["categories"],
            "course_categories": parsed_course_categories,
            "course_names": parsed_course_names,
            "items_created": result["items_created"]
        }
    except ValueError as e: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Document upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    document_service: DocumentService = Depends(get_document_service),
    current_user: Dict[str, Any] = Depends(get_current_admin)
):
    """Delete a document from the knowledge base."""
    try:
        # Use the injected service instance
        await document_service.delete_document(doc_id)
        return {"message": "Document deleted successfully"}
    except ValueError as e: # Catch not found error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        print(f"Document deletion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

@router.get("/documents")
async def list_documents(
    category: Optional[str] = None,
    document_service: DocumentService = Depends(get_document_service),
    current_user: Dict[str, Any] = Depends(get_current_admin)
):
    """List documents in the knowledge base."""
    try:
        # Use the injected service instance. Validation for category is handled inside.
        documents = await document_service.list_documents(category)
        # Get the list of valid categories directly from the service
        valid_categories = list(document_service.valid_categories)
        return {"documents": documents, "categories": valid_categories}
    except Exception as e:
        print(f"Document listing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )
        
@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
        current_user: Dict[str, Any] = Depends(get_current_admin)
    ):
        """
        Get analytics for the admin dashboard.
        """
        analytics_data = analytics_service.get_analytics(days=7)
        return analytics_data