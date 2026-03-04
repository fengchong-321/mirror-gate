"""Authentication API Routes.

This module defines the REST API endpoints for user authentication.
"""

from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
)
from app.models.user import User, UserRole


router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency injection for AuthService."""
    return AuthService(db)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Get the current authenticated user from the token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)

    # Decode token
    payload = auth_service.decode_token(token)

    # Get user
    user = auth_service.get_user(payload["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return UserResponse.model_validate(user)


def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Verify the current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_admin(
    current_user: UserResponse = Depends(get_current_active_user),
) -> UserResponse:
    """Require admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ============ Auth Endpoints ============

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    user_data: UserCreate,
    service: AuthService = Depends(get_auth_service),
):
    """Register a new user account."""
    user = service.create_user(user_data, role=UserRole.TESTER)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login and get tokens",
)
def login(
    login_data: LoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Authenticate and receive access token."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return service.login(
        login_data,
        ip_address=ip_address,
        user_agent=user_agent
    )


@router.post(
    "/logout",
    summary="Logout and revoke token",
)
def logout(
    request: Request,
    service: AuthService = Depends(get_auth_service),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """Logout and revoke the current session."""
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header else ""

    service.logout(token)
    return {"message": "Successfully logged out"}


@router.post(
    "/refresh",
    summary="Refresh access token",
)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using refresh token."""
    access_token, expires_at = service.refresh_access_token(refresh_data.refresh_token)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expires_at.isoformat(),
    }


@router.post(
    "/change-password",
    summary="Change user password",
)
def change_password(
    password_data: ChangePasswordRequest,
    service: AuthService = Depends(get_auth_service),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """Change the current user's password."""
    service.change_password(current_user.id, password_data)
    return {"message": "Password changed successfully"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info",
)
def get_me(
    current_user: UserResponse = Depends(get_current_active_user),
):
    """Get the current authenticated user's information."""
    return current_user


# ============ User Management Endpoints (Admin only) ============

@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List all users (Admin only)",
)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    service: AuthService = Depends(get_auth_service),
    current_user: UserResponse = Depends(require_admin),
):
    """List all users (Admin only)."""
    total, users = service.get_users(skip=skip, limit=limit, search=search)
    return UserListResponse(
        total=total,
        items=[UserResponse.model_validate(u) for u in users],
    )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID (Admin only)",
)
def get_user(
    user_id: int,
    service: AuthService = Depends(get_auth_service),
    current_user: UserResponse = Depends(require_admin),
):
    """Get a specific user by ID (Admin only)."""
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update user (Admin only)",
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    service: AuthService = Depends(get_auth_service),
    current_user: UserResponse = Depends(require_admin),
):
    """Update a user's information (Admin only)."""
    user = service.update_user(user_id, user_data)
    return UserResponse.model_validate(user)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user (Admin only)",
)
def delete_user(
    user_id: int,
    service: AuthService = Depends(get_auth_service),
    current_user: UserResponse = Depends(require_admin),
):
    """Delete a user (Admin only)."""
    service.delete_user(user_id)
    return None
