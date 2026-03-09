"""Authentication Service.

This module provides business logic for user authentication.
"""

import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from passlib.context import CryptContext
import jwt

from app.models.user import User, UserSession, UserRole
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    LoginResponse,
    ChangePasswordRequest,
)
from app.config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
JWT_SECRET_KEY = settings.SECRET_KEY or "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days


class AuthService:
    """认证服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ============ Password Methods ============

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    # ============ JWT Methods ============

    @staticmethod
    def create_access_token(user_id: int, username: str, role: UserRole) -> Tuple[str, datetime]:
        """Create an access token."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "user_id": user_id,
            "username": username,
            "role": role.value,
            "exp": expires_at,
            "iat": now,
            "type": "access",
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token, expires_at

    @staticmethod
    def create_refresh_token() -> str:
        """Create a refresh token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # ============ User CRUD ============

    def create_user(self, user_data: UserCreate, role: UserRole = UserRole.TESTER) -> User:
        """Create a new user."""
        # Check if username exists
        if self.db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Check if email exists
        if self.db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=self.hash_password(user_data.password),
            full_name=user_data.full_name,
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def get_users(self, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> Tuple[int, list]:
        """Get all users with optional search."""
        query = self.db.query(User)

        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                )
            )

        total = query.count()
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        return total, users

    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update a user."""
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        update_data = user_data.model_dump(exclude_unset=True)

        # Check email uniqueness
        if "email" in update_data:
            existing = self.db.query(User).filter(
                User.email == update_data["email"],
                User.id != user_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        # Hash password if provided
        if "REDACTED" in update_data:
            update_data["password_hash"] = self.hash_password(update_data.pop("REDACTED"))

        for key, value in update_data.items():
            setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        self.db.delete(user)
        self.db.commit()
        return True

    # ============ Authentication ============

    def login(self, login_data: LoginRequest, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> LoginResponse:
        """Authenticate a user and return tokens."""
        user = self.get_user_by_username(login_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )

        if not self.verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create tokens
        access_token, expires_at = self.create_access_token(user.id, user.username, user.role)
        refresh_token = self.create_refresh_token()

        # Revoke existing sessions for this user
        self.db.query(UserSession).filter(
            UserSession.user_id == user.id
        ).delete()

        # Create new session
        session = UserSession(
            user_id=user.id,
            token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        self.db.add(session)

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)

        self.db.commit()

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )

    def logout(self, token: str) -> bool:
        """Logout a user by revoking their session."""
        session = self.db.query(UserSession).filter(
            UserSession.token == token,
            UserSession.is_revoked == False
        ).first()

        if session:
            session.is_revoked = True
            session.revoked_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
        return False

    def refresh_access_token(self, refresh_token: str) -> Tuple[str, datetime]:
        """Refresh an access token using a refresh token."""
        session = self.db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token,
            UserSession.is_revoked == False
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        user = self.get_user(session.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or disabled"
            )

        # Create new access token
        access_token, expires_at = self.create_access_token(user.id, user.username, user.role)

        # Update session
        session.token = access_token
        session.expires_at = expires_at

        self.db.commit()

        return access_token, expires_at

    def change_password(self, user_id: int, password_data: ChangePasswordRequest) -> bool:
        """Change a user's password."""
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if not self.verify_password(password_data.old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password"
            )

        user.password_hash = self.hash_password(password_data.new_password)
        self.db.commit()
        return True

    def revoke_all_sessions(self, user_id: int) -> int:
        """Revoke all sessions for a user."""
        now = datetime.now(timezone.utc)
        result = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_revoked == False
        ).update({
            "is_revoked": True,
            "revoked_at": now
        })
        self.db.commit()
        return result
