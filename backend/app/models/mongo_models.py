from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId
from backend.app.db.base import get_mongodb
import logging
from zoneinfo import ZoneInfo 

logger = logging.getLogger(__name__)

IST = ZoneInfo('Asia/Kolkata')

class UserRole(Enum):
    STUDENT = "student"
    ADMIN = "admin"

class TicketStatus(Enum):
    OPEN = "Open"
    WIP = "Work in Progress"
    STUDENT_ACTION_REQUIRED = "Student Action Required"
    ADMIN_ACTION_REQUIRED = "Admin Action Required"
    RESOLVED = "Resolved"

class TicketCategory(Enum):
    PRODUCT_SUPPORT = "Product Support"
    LEAVE = "Leave"
    ATTENDANCE_COUNSELLING_SUPPORT = "Attendance/Counselling Support"
    REFERRAL = "Referral"
    EVALUATION_SCORE = "Evaluation Score"
    COURSE_QUERY = "Course Query"
    OTHER_COURSE_QUERY = "Other Course Query"
    CODE_REVIEW = "Code Review"
    PERSONAL_QUERY = "Personal Query"
    NBFC_ISA = "NBFC/ISA"
    IA_SUPPORT = "IA Support"
    MISSED_EVALUATION_SUBMISSION = "Missed Evaluation Submission"
    REVISION = "Revision"
    MAC = "MAC"
    WITHDRAWAL = "Withdrawal"
    LATE_EVALUATION_SUBMISSION = "Late Evaluation Submission"
    FEEDBACK = "Feedback"
    PLACEMENT_SUPPORT = "Placement Support - Placements"
    OFFER_STAGE_PLACEMENTS = "Offer Stage- Placements"
    ISA_EMI_NBFC_GLIDE_PLACEMENTS = "ISA/EMI/NBFC/Glide Related - Placements"
    SESSION_SUPPORT_PLACEMENT = "Session Support - Placement"

class MongoBaseService:
    def __init__(self):
        self.db = get_mongodb()

class UserService(MongoBaseService):
    def __init__(self):
        super().__init__()
        self.collection = self.db.users
    
    def create_user(self, email: str, password_hash: str, role: str, user_type: Optional[str] = None, 
                   course_category: Optional[str] = None, course_name: Optional[str] = None) -> str:
        """Create a new user"""
        user_doc = {
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "created_at": datetime.now(IST)
        }
        if user_type:
            user_doc["type"] = user_type
        if course_category:
            user_doc["course_category"] = course_category
        if course_name:
            user_doc["course_name"] = course_name
        
        result = self.collection.insert_one(user_doc)
        return str(result.inserted_id)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        user = self.collection.find_one({"email": email})
        if user:
            user["id"] = str(user["_id"])
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            user = self.collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user["id"] = str(user["_id"])
            return user
        except:
            return None
    
    def get_admins(self, admin_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all admin users, optionally filtered by type"""
        query = {"role": UserRole.ADMIN.value}
        if admin_type:
            query["type"] = admin_type
        users = list(self.collection.find(query))
        for user in users:
            user["id"] = str(user["_id"])
        return users

class TicketService(MongoBaseService):
    def __init__(self):
        super().__init__()
        self.collection = self.db.tickets
    
    def create_ticket(self, user_id: str, category: str, title: str, message: str, 
                     subcategory_data: Optional[Dict[str, Any]] = None,
                     from_date: Optional[str] = None, to_date: Optional[str] = None,
                     attachments: Optional[List[str]] = None) -> str:
        """Create a new ticket"""
        print('Received Create request',title, message, datetime.now(IST))
        ticket_doc = {
            "user_id": user_id,
            "category": category,
            "status": TicketStatus.OPEN.value,
            "title": title,
            "message": message,
            "subcategory_data": subcategory_data or {},
            "from_date": from_date,
            "to_date": to_date,
            "attachments": attachments or [],
            "assigned_to": None,
            "rating": None,
            "created_at": datetime.now(IST),
            "updated_at": datetime.now(IST),
        }
        
        result = self.collection.insert_one(ticket_doc)
        return str(result.inserted_id)
    
    def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket by ID"""
        try:
            ticket = self.collection.find_one({"_id": ObjectId(ticket_id)})
            if ticket:
                ticket["id"] = str(ticket["_id"])
            return ticket
        except:
            return None

    def update_ticket_timestamp(self, ticket_id: str):
        """Update the updated_at timestamp of a ticket"""
        self.update_ticket(ticket_id, {"updated_at": datetime.now(IST)})
        try:
            ticket = self.collection.find_one({"_id": ObjectId(ticket_id)})
            if ticket:
                ticket["id"] = str(ticket["_id"])
            return ticket
        except:
            return None
    
    def get_user_tickets(self, user_id: str, role:str) -> List[Dict[str, Any]]:
        """Get all tickets for a user"""
        query = {"assigned_to": user_id} if role == "admin" else {"user_id": user_id}
        tickets = list(self.collection.find(query).sort("created_at", -1))        
        for ticket in tickets:
            ticket["id"] = str(ticket["_id"])
        return tickets
    
    def get_admin_tickets(self, admin_id: Optional[str] = None, admin_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tickets for admin (assigned or unassigned)"""
        if admin_id:
            query = {"$or": [
                {"assigned_to": admin_id},
                {"assigned_to": None},
            ]}
        else:
            query = {"status": TicketStatus.ADMIN_ACTION_REQUIRED.value}

        if admin_type:
            query["assigned_to_type"] = admin_type
        
        tickets = list(self.collection.find(query).sort("created_at", -1))
        for ticket in tickets:
            ticket["id"] = str(ticket["_id"])
        return tickets
    
    def update_ticket(self, ticket_id: str, update_data: Dict[str, Any]) -> bool:
        """Update ticket"""
        try:
            update_data["updated_at"] = datetime.now(IST)
            result = self.collection.update_one(
                {"_id": ObjectId(ticket_id)}, 
                {"$set": update_data}
            )
            return result.modified_count > 0
        except:
            return False
    
    def update_ticket_status(self, ticket_id: str, status: str, assigned_to: Optional[str] = None) -> bool:
        """Update ticket status"""
        update_data = {"status": status}
        if assigned_to is not None:
            update_data["assigned_to"] = assigned_to
        return self.update_ticket(ticket_id, update_data)
    
    def rate_ticket(self, ticket_id: str, rating: float) -> bool:
        """Rate a ticket"""
        return self.update_ticket(ticket_id, {"rating": rating})

class ConversationService(MongoBaseService):
    def __init__(self):
        super().__init__()
        self.collection = self.db.conversations
    
    def create_conversation(self, ticket_id: str, sender_role: str, message: str,
                          sender_id: Optional[str] = None, confidence_score: Optional[float] = None, attachments: Optional[List[str]] = None) -> str:
        """Create a new conversation entry"""
        conversation_doc = {
            "ticket_id": ticket_id,
            "sender_role": sender_role,
            "sender_id": sender_id,
            "message": message,
            "confidence_score": confidence_score,
            "attachments": attachments,
            "timestamp": datetime.now(IST)
        }
        
        result = self.collection.insert_one(conversation_doc)
        return str(result.inserted_id)

    def get_conversation_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""
        try:
            conversation = self.collection.find_one({"_id": ObjectId(conversation_id)})
            if conversation:
                conversation["id"] = str(conversation["_id"])
                return conversation
            return None
        except Exception as e:
            logger.error(f"Error getting conversation by ID {conversation_id}: {e}")
            return None
    
    def get_ticket_conversations(self, ticket_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a ticket"""
        conversations = list(self.collection.find({"ticket_id": ticket_id}).sort("timestamp", 1))
        for conv in conversations:
            conv["id"] = str(conv["_id"])
        return conversations
    
    def get_conversation_count(self, ticket_id: str) -> int:
        """Get conversation count for a ticket"""
        return self.collection.count_documents({"ticket_id": ticket_id})
    
    def get_last_conversation(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get the last conversation for a ticket"""
        conv = self.collection.find_one({"ticket_id": ticket_id}, sort=[("timestamp", -1)])
        if conv:
            conv["id"] = str(conv["_id"])
        return conv

# Convenience instances
user_service = UserService()
ticket_service = TicketService()
conversation_service = ConversationService()