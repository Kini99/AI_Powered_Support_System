import sys
from pathlib import Path

# Add project root to path for standalone execution
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.models import user_service, UserRole
from backend.app.core.security import get_password_hash
import logging

logger = logging.getLogger(__name__)

def init_database():
    """Initialize MongoDB database with sample users"""
    try:
        # Check if users already exist
        existing_user = user_service.get_user_by_email("student1@masaischool.com")
        if existing_user:
            logger.info("Database already initialized with users")
            return
        
        # Create sample students with course information
        students = [
            {"email": "student1@masaischool.com", "password": "password123", 
             "course_category": "Software Development", "course_name": "Full Stack Web Development"},
            {"email": "student2@masaischool.com", "password": "password123", 
             "course_category": "Data Science", "course_name": "Data Analytics Fundamentals"},
            {"email": "student3@masaischool.com", "password": "password123", 
             "course_category": "AI/ML", "course_name": "Machine Learning Basics"},
        ]
        
        for student_data in students:
            user_service.create_user(
                email=student_data["email"],
                password_hash=get_password_hash(student_data["password"]),
                role=UserRole.STUDENT.value,
                course_category=student_data["course_category"],
                course_name=student_data["course_name"]
            )
        
        # Create sample admins (EC and IA)
        admins = [
            {"email": "ec1@masaischool.com", "password": "admin123"},
            {"email": "ec2@masaischool.com", "password": "admin123"},
            {"email": "ia1@masaischool.com", "password": "admin123"},
            {"email": "ia2@masaischool.com", "password": "admin123"},
        ]
        
        for admin_data in admins:
            admin_type = "EC" if "ec" in admin_data["email"] else "IA"
            user_service.create_user(
                email=admin_data["email"],
                password_hash=get_password_hash(admin_data["password"]),
                role=UserRole.ADMIN.value,
                user_type=admin_type
            )
        
        logger.info("MongoDB database initialized with sample users")
        logger.info("Sample student credentials: student1@masaischool.com / password123")
        logger.info("Sample admin credentials: ec1@masaischool.com / admin123")
        
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise e

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()