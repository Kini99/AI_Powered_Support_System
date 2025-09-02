from fastapi import APIRouter, HTTPException, status, Response, Depends
from backend.app.models import user_service
from backend.app.core.security import verify_password, create_session_token
from backend.app.core.deps import get_current_user
from .schemas import LoginRequest, LoginResponse, UserResponse
from typing import Dict, Any

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    response: Response
):
    # Find user by email
    user = user_service.get_user_by_email(login_data.email)
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create session token
    session_token = create_session_token(user["id"], user["role"])
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=86400 * 7,  # 7 days
        samesite="none",
        secure=True
    )
    
    return LoginResponse(
        message="Login successful",
        role=user["role"],
        user_id=user["id"],
        email=user["email"],
        session_token=session_token
    )

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="session_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        role=current_user["role"],
        created_at=current_user["created_at"].isoformat()
    )