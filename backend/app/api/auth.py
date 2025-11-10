"""
Authentication API routes.
"""
from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from loguru import logger
from ..auth.models import UserCreate, UserLogin, Token, UserResponse
from ..auth.jwt_auth import hash_password, verify_password, create_access_token, get_current_user
from ..db import couch_client
from ..config import config
from fastapi import Depends


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
    
    Returns:
        Access token
    """
    try:
        # Check if user already exists
        existing_user = couch_client.find_user_by_email(user_data.email)
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create user document
        user_doc = {
            "type": "user",
            "email": user_data.email,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save to CouchDB
        user_id = couch_client.save_doc(config.users_db, user_doc)
        
        # Create access token
        access_token = create_access_token(data={"sub": user_id, "email": user_data.email})
        
        logger.info(f"New user registered: {user_data.email}")
        
        return Token(access_token=access_token)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """
    Login and get access token.
    
    Args:
        user_data: User login credentials
    
    Returns:
        Access token
    """
    try:
        # Find user by email
        user = couch_client.find_user_by_email(user_data.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        if not verify_password(user_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user["_id"], "email": user["email"]}
        )
        
        logger.info(f"User logged in: {user_data.email}")
        
        return Token(access_token=access_token)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User information
    """
    return UserResponse(
        id=current_user["_id"],
        email=current_user["email"],
        created_at=current_user["created_at"]
    )

