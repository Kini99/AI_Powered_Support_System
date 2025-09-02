from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from backend.app.db.base import Base

class TicketStatus(PyEnum):
    OPEN = "Open"
    WIP = "Work in Progress"
    STUDENT_ACTION_REQUIRED = "Student Action Required"
    ADMIN_ACTION_REQUIRED = "Admin Action Required"
    RESOLVED = "Resolved"

class TicketCategory(PyEnum):
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

class ProductType(PyEnum):
    COURSE_PLATFORM = "Course Platform"
    OJ = "OJ"
    ZOOM = "Zoom"
    SLACK = "Slack"
    HUKUMU_INTERVIEW = "HUKUMU Interview"
    CONCEPT_EXPLAINER = "Concept Explainer (CE)"

class IssueType(PyEnum):
    ACC_REQUIRED_LOGIN = "Acc required / Unable to login"
    QUERY_HOW_TO_USE = "Query on how to use the product"
    INTERVIEW = "Interview"
    LINKS = "Links"
    TECHNICAL_ISSUES = "Technical issues"

class LeaveType(PyEnum):
    PHYSICAL_HEALTH = "Physical health issues"
    DEMISE_FAMILY = "Demise of a family member"
    COLLEGE_EXAMS = "College Exams"
    NATURAL_CALAMITY = "Natural Calamity"
    OTHER = "Other"

class CounsellingReason(PyEnum):
    MENTAL_HEALTH = "Mental health problem"
    TIME_MANAGEMENT = "Time management guidance"
    NON_TECHNICAL_GUIDANCE = "Non-technical personal guidance"
    SCHEDULE_DIFFICULTY = "Difficulty in managing with schedule"
    OTHER = "Other"

class MACActivity(PyEnum):
    PORTFOLIO_GITHUB = "Portfolio and Github"
    RESUME = "Resume"
    PROJECT_REVIEW = "Project Review / Support"

class PlacementSupportReason(PyEnum):
    GRADUATION_CERT_NOT_RECEIVED = "Graduation certificate not received"
    DISCREPANCY_GRADUATION_CERT = "Discrepancy in Graduation Certificate is Incorrect"
    DISCREPANCY_NAME = "Discrepancy in Graduation Certificate - Name is Incorrect"
    UPDATE_CONTACT = "Update Contact details"

class OfferStageReason(PyEnum):
    RECEIVED_EXTERNAL_OFFER = "Received an external offer"
    UNCLEAR_OFFER_DETAILS = "Unclear on the details in the offer letter"
    UNABLE_UPLOAD_OFFER = "Unable to upload offer letter on placement product"

class ISAEMIReason(PyEnum):
    ISA = "ISA"
    EMI = "EMI"
    NBFC = "NBFC"
    GLIDE = "Glide"

class SessionType(PyEnum):
    CODING_DSA = "Coding / DSA"
    MASTERCLASS = "MasterClass"
    SCRUM = "Scrum"
    CSBT = "CSBT"
    INTERVIEW_PREPARATION = "Interview Preparation"

class SessionSupportReason(PyEnum):
    NOT_ATTEND_SESSIONS = "Not able to attend scheduled sessions"
    NOT_ATTEMPT_ASSIGNMENT = "Not able to Attempt assignment/contest"
    NEED_HELP_ASSIGNMENT = "Need help to do assignment/contest"
    FEEDBACK_PROGRAM = "Feedback on the program that is currently ongoing"
    UNDERSTAND_PROGRESS = "Need to understand my progress in the program"
    NEED_CONTENT_ACCESS = "Need content/access to session that was part of intervention program"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(Enum(TicketCategory), nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Category-specific fields stored as JSON
    subcategory_data = Column(JSON)  # Will store product_type, issue_type, leave_type, etc.
    from_date = Column(String, nullable=True)  # For leave tickets
    to_date = Column(String, nullable=True)    # For leave tickets
    
    attachments = Column(JSON)  # List of attachment URLs
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    rating = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="tickets")
    assigned_admin = relationship("User", foreign_keys=[assigned_to])
    conversations = relationship("Conversation", back_populates="ticket")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    sender_role = Column(String, nullable=False)  # student/agent/admin
    sender_id = Column(Integer, nullable=True)  # User ID (null for agent)
    message = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=True)  # For agent responses
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ticket = relationship("Ticket", back_populates="conversations")