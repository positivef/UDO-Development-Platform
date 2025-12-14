"""
Authentication Router

사용자 인증 관련 엔드포인트를 제공합니다.
"""

from typing import Dict, Any
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import logging

# Security imports
from app.core.security import (
    JWTManager,
    PasswordHasher,
    InputValidator,
    SecureUserCreate,
    security
)

# Mock user storage (실제 환경에서는 데이터베이스 사용)
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Authentication failed"},
        403: {"description": "Forbidden"},
    }
)

# Request/Response models
class LoginRequest(BaseModel):
    """로그인 요청 모델"""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")

class LoginResponse(BaseModel):
    """로그인 응답 모델"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class RegisterRequest(BaseModel):
    """회원가입 요청 모델"""
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    full_name: str = Field(None, description="Full name")

class RefreshTokenRequest(BaseModel):
    """토큰 갱신 요청 모델"""
    refresh_token: str = Field(..., description="Refresh token")

class TokenResponse(BaseModel):
    """토큰 응답 모델"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Initialize auth service
auth_service = AuthService()


@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest):
    """
    새로운 사용자 등록

    - Email 중복 검사
    - 비밀번호 강도 검증
    - 사용자 생성 후 토큰 발급
    """
    try:
        # Email 유효성 검사
        if not InputValidator.validate_email(request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )

        # 비밀번호 강도 검증
        password_validation = InputValidator.validate_password(request.password)
        if not password_validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="; ".join(password_validation["errors"])
            )

        # 사용자 생성 (SecureUserCreate 모델 사용)
        secure_user = SecureUserCreate(
            email=request.email,
            password=request.password,
            username=request.username
        )

        # AuthService를 통해 사용자 생성
        user = await auth_service.create_user(
            email=secure_user.email,
            password=request.password,  # Raw password (will be hashed in service)
            username=secure_user.username,
            full_name=request.full_name
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )

        # 토큰 생성 (RBAC: role 포함)
        access_token = JWTManager.create_access_token(
            data={"sub": user["email"], "user_id": user["id"], "role": user.get("role", "viewer")}
        )
        refresh_token = JWTManager.create_refresh_token(
            data={"sub": user["email"], "user_id": user["id"], "role": user.get("role", "viewer")}
        )

        logger.info(f"New user registered: {user['email']}")

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user={
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "full_name": user.get("full_name")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    사용자 로그인

    - Email/비밀번호 검증
    - 액세스 토큰 및 리프레시 토큰 발급
    """
    try:
        # Email 유효성 검사
        if not InputValidator.validate_email(request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )

        # 사용자 인증
        user = await auth_service.authenticate_user(
            email=request.email,
            password=request.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # 토큰 생성 (RBAC: role 포함)
        access_token = JWTManager.create_access_token(
            data={"sub": user["email"], "user_id": user["id"], "role": user.get("role", "viewer")}
        )
        refresh_token = JWTManager.create_refresh_token(
            data={"sub": user["email"], "user_id": user["id"], "role": user.get("role", "viewer")}
        )

        logger.info(f"User logged in: {user['email']}")

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user={
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "full_name": user.get("full_name")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    토큰 갱신

    - 리프레시 토큰 검증
    - 새로운 액세스 토큰 발급
    - 새로운 리프레시 토큰 발급 (rotate)
    """
    try:
        # 리프레시 토큰 디코드
        payload = JWTManager.decode_token(request.refresh_token)

        # 토큰 타입 확인
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # 사용자 확인
        user_email = payload.get("sub")
        user_id = payload.get("user_id")
        user_role = payload.get("role", "viewer")  # RBAC: Preserve role in refresh

        if not user_email or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        # 새 토큰 생성 (RBAC: role 포함)
        new_access_token = JWTManager.create_access_token(
            data={"sub": user_email, "user_id": user_id, "role": user_role}
        )
        new_refresh_token = JWTManager.create_refresh_token(
            data={"sub": user_email, "user_id": user_id, "role": user_role}
        )

        logger.info(f"Token refreshed for user: {user_email}")

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    현재 로그인한 사용자 정보 조회

    - JWT 토큰 검증
    - 사용자 정보 반환
    """
    try:
        # 토큰 검증
        payload = JWTManager.verify_token(credentials)

        # 사용자 정보 조회
        user_email = payload.get("sub")
        user_id = payload.get("user_id")

        user = await auth_service.get_user(user_email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
            "full_name": user.get("full_name"),
            "created_at": user.get("created_at")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    사용자 로그아웃

    - 토큰 무효화 (실제 환경에서는 Redis 등에 블랙리스트 저장)
    - 로그아웃 성공 응답
    """
    try:
        # 토큰 검증
        payload = JWTManager.verify_token(credentials)
        user_email = payload.get("sub")

        # TODO: 실제 환경에서는 토큰을 블랙리스트에 추가
        # await auth_service.blacklist_token(credentials.credentials)

        logger.info(f"User logged out: {user_email}")

        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        # 로그아웃은 항상 성공 응답
        return {"message": "Logged out"}


# Export router
__all__ = ['router']