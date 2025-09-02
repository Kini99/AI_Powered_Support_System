from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer
from backend.app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
serializer = URLSafeTimedSerializer(settings.SESSION_SECRET_KEY)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_session_token(user_id: str, role: str) -> str:
    """Create a session token for the user"""
    return serializer.dumps({"user_id": user_id, "role": role})

def verify_session_token(token: str) -> dict:
    """Verify and extract user info from session token"""
    try:
        return serializer.loads(token, max_age=86400 * 7)  # 7 days
    except:
        return None