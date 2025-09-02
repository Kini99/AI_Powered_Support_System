from typing import Dict, Any
from backend.app.models import ticket_service, conversation_service, user_service, TicketStatus
from .state import AgentState
import logging

logger = logging.getLogger(__name__)

class EscalationAgent:
    def __init__(self):
        pass
    
    async def _find_available_admin( self, admin_type: str) -> Dict[str, Any]:
        """
        Finds an available admin.
        In a real system, this would check for load, online status, and specialty.
        For now, it returns the first available admin.
        """
        try:
            # This logic can be expanded to filter by EC/IA roles if they are stored in the user model
            admins = user_service.get_admins(admin_type=admin_type)
            print(f"available admins {admins}.")
            return admins[0] if admins else None
        except Exception as e:
            print(f"Error finding admin: {e}")
            return None

    
    async def process(self, state: AgentState) -> AgentState:
        """
        Handles the escalation of a ticket to a human admin.
        This involves finding an admin, assigning the ticket, and notifying the user.
        """
        try:
            ticket_id = state["ticket_id"]
            admin_type = state.get("admin_type", "EC")  # Default to EC if not specified

            print(f"Escalating ticket {ticket_id} to an {admin_type} admin.")

            # 1. Find an available admin of the specified type
            admin = await self._find_available_admin(admin_type)
            admin_id = admin["id"] if admin else None
            
            # 2. Update ticket status to Admin Action Required and assign to admin
            ticket_service.update_ticket_status(
                ticket_id, 
                TicketStatus.ADMIN_ACTION_REQUIRED.value, 
                admin_id
            )

            # 3. Create a predefined message for the student
            student_message = ( state.get("response") or f"Thank you for contacting support. Your query is under review. We will get back to you soon with a detailed response.")           
            print("student msg adding to conversaion:", student_message, state.get("response"))
            conversation_service.create_conversation(
                ticket_id=ticket_id,
                sender_role="agent",
                message=student_message
            )

            # 4. Notify the assigned admin (placeholder for a real notification system)
            if admin:
                await self._notify_admin(admin, {"id": ticket_id})
                logger.info(f"Ticket {ticket_id} assigned to admin {admin['email']}")
            else:
                logger.warning(f"No available admin found for ticket {ticket_id}. It is in the unassigned queue.")

            return state
                
        except Exception as e:
            print(f"Error in escalation agent for ticket {state['ticket_id']}:",e)
            state["error_message"] = str(e)
            return state
    
    async def _notify_admin(self, admin: Dict[str, Any], ticket: Dict[str, Any]):
        """Placeholder for a real-time notification system (e.g., email, Slack, WebSocket)."""
        logger.info(f"NOTIFICATION SENT (simulated): Admin {admin['email']} assigned to ticket {ticket['id']}")