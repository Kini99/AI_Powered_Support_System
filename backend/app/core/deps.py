from fastapi import Depends, HTTPException, status, Cookie
from backend.app.models import user_service, UserRole
from backend.app.core.security import verify_session_token
from typing import Optional, Dict, Any
from backend.app.services.document_service import DocumentService


def get_current_user(
    session_token: Optional[str] = Cookie(None, alias="session_token")
) -> Dict[str, Any]:
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    payload = verify_session_token(session_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token"
        )
    
    user = user_service.get_user_by_id(payload["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

def get_current_student(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user["role"] != UserRole.STUDENT.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def get_current_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user["role"] != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

document_service_instance = DocumentService()

# 3. Define the dependency function that the router is looking for
def get_document_service():
    """Dependency to get the singleton DocumentService instance."""
    return document_service_instance

