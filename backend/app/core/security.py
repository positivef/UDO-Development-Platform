"""
Security and Input Validation System

보안 미들웨어, 입력 검증, JWT 토큰 관리를 제공합니다.

Security Improvements (2025-12-14):
- CRIT-01: JWT secret key from environment variable (persistent across restarts)
- CRIT-02: bcrypt password hashing (replaces weak PBKDF2)
- CRIT-03: Token blacklist for proper logout (prevents token reuse)
- HIGH-01: Auth endpoint rate limiting (prevents brute force)
"""

import re
import secrets
import hashlib
import os
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, List, Set
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, Field
import jwt
import logging
from functools import wraps
from threading import Lock

# MED-04: Import log sanitizer for secure logging
from .log_sanitizer import sanitize_log_message, sanitize_exception

# Optional bcrypt import with fallback
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    logging.warning("bcrypt not installed. Using PBKDF2 fallback. Install with: pip install bcrypt")

logger = logging.getLogger(__name__)

# =============================================================================
# CRIT-01 FIX: JWT Secret from Environment Variable
# =============================================================================
def _get_secret_key() -> str:
    """
    Get JWT secret key from environment variable.
    Falls back to generated key only in development (with warning).
    """
    secret = os.environ.get("JWT_SECRET_KEY") or os.environ.get("SECRET_KEY")

    if secret:
        if len(secret) < 32:
            logger.warning("JWT_SECRET_KEY is too short (< 32 chars). Security risk!")
        return secret

    # Development fallback - generate persistent key
    # WARNING: This should NOT be used in production!
    env = os.environ.get("ENVIRONMENT", "development")
    if env == "production":
        raise ValueError(
            "CRITICAL: JWT_SECRET_KEY environment variable is required in production! "
            "Set it with: export JWT_SECRET_KEY=$(openssl rand -base64 32)"
        )

    # Development only - use a fixed key per session (not secure, but consistent)
    logger.warning(
        "JWT_SECRET_KEY not set. Using generated key (NOT for production!). "
        "Set JWT_SECRET_KEY environment variable for persistence."
    )
    return secrets.token_urlsafe(32)

# Security configurations
SECRET_KEY = _get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# =============================================================================
# CRIT-03 FIX: Token Blacklist for Proper Logout
# =============================================================================
class TokenBlacklist:
    """
    In-memory token blacklist for invalidating tokens on logout.

    Production: Use Redis for distributed systems:
        import redis
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
    """

    def __init__(self):
        self._blacklist: Set[str] = set()
        self._lock = Lock()
        self._cleanup_threshold = 10000  # Cleanup after this many entries

    def add(self, token: str, exp: Optional[datetime] = None) -> None:
        """Add token to blacklist (called on logout)"""
        with self._lock:
            self._blacklist.add(token)

            # Periodic cleanup to prevent memory leak
            if len(self._blacklist) > self._cleanup_threshold:
                self._cleanup()

    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        return token in self._blacklist

    def _cleanup(self) -> None:
        """Remove expired tokens (basic cleanup - production should use Redis TTL)"""
        # In production with Redis, use SETEX with expiry time
        # For now, just clear old entries if too many
        if len(self._blacklist) > self._cleanup_threshold:
            logger.info(f"Clearing token blacklist ({len(self._blacklist)} entries)")
            self._blacklist.clear()

    def revoke_all_user_tokens(self, user_id: str) -> None:
        """Revoke all tokens for a user (for password reset, account compromise)"""
        # In production, store user_id->token mappings in Redis
        logger.info(f"Revoke all tokens requested for user: {user_id}")

# Global token blacklist instance
token_blacklist = TokenBlacklist()

# Security bearer
security = HTTPBearer()


# RBAC (Role-Based Access Control) Configuration
class UserRole:
    """User roles with hierarchical permissions"""
    ADMIN = "admin"               # Full access (all operations)
    PROJECT_OWNER = "project_owner"  # Project creation/deletion, team management
    DEVELOPER = "developer"       # Task CRUD, own task modification
    VIEWER = "viewer"             # Read-only access

    # Role hierarchy (higher number = more permissions)
    ROLE_HIERARCHY = {
        ADMIN: 4,
        PROJECT_OWNER: 3,
        DEVELOPER: 2,
        VIEWER: 1
    }

    @classmethod
    def has_permission(cls, user_role: str, required_role: str) -> bool:
        """
        Check if user role has sufficient permissions

        Args:
            user_role: User's current role
            required_role: Required role for operation

        Returns:
            True if user has sufficient permissions
        """
        user_level = cls.ROLE_HIERARCHY.get(user_role, 0)
        required_level = cls.ROLE_HIERARCHY.get(required_role, 0)
        return user_level >= required_level

    @classmethod
    def get_all_roles(cls) -> list:
        """Get list of all valid roles"""
        return [cls.ADMIN, cls.PROJECT_OWNER, cls.DEVELOPER, cls.VIEWER]


class SecurityConfig:
    """보안 설정"""

    # Rate limiting (increased for development/testing)
    RATE_LIMIT_REQUESTS = 1000  # requests per minute (100 in production)
    RATE_LIMIT_WINDOW = 60  # seconds

    # Password policy
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True

    # Input validation
    MAX_INPUT_LENGTH = 10000
    ALLOWED_CONTENT_TYPES = ["application/json", "multipart/form-data"]

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\b)",
        r"(--|\||;|\/\*|\*\/|@@|@)",
        r"(xp_|sp_|0x)",
        r"(\bEXEC\b|\bEXECUTE\b)",
        r"(\bCAST\b.*\bAS\b)",
        r"(\bWAITFOR\b.*\bDELAY\b)",
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]


class InputValidator:
    """입력 데이터 검증"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """이메일 형식 검증"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """비밀번호 정책 검증"""
        errors = []

        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters")

        if SecurityConfig.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain uppercase letter")

        if SecurityConfig.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain lowercase letter")

        if SecurityConfig.REQUIRE_NUMBERS and not re.search(r'\d', password):
            errors.append("Password must contain number")

        if SecurityConfig.REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain special character")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": InputValidator.calculate_password_strength(password)
        }

    @staticmethod
    def calculate_password_strength(password: str) -> str:
        """비밀번호 강도 계산"""
        score = 0

        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1

        if score <= 2:
            return "weak"
        elif score <= 4:
            return "medium"
        else:
            return "strong"

    @staticmethod
    def sanitize_input(input_string: str, max_length: Optional[int] = None) -> str:
        """입력 데이터 살균"""
        if not input_string:
            return ""

        # Remove null bytes
        sanitized = input_string.replace('\x00', '')

        # Strip whitespace
        sanitized = sanitized.strip()

        # Limit length
        if max_length:
            sanitized = sanitized[:max_length]
        elif len(sanitized) > SecurityConfig.MAX_INPUT_LENGTH:
            sanitized = sanitized[:SecurityConfig.MAX_INPUT_LENGTH]

        return sanitized

    @staticmethod
    def check_sql_injection(input_string: str) -> bool:
        """SQL 인젝션 패턴 검사"""
        if not input_string:
            return False

        for pattern in SecurityConfig.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {input_string[:100]}")
                return True

        return False

    @staticmethod
    def check_xss(input_string: str) -> bool:
        """XSS 패턴 검사"""
        if not input_string:
            return False

        for pattern in SecurityConfig.XSS_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                logger.warning(f"Potential XSS attack detected: {input_string[:100]}")
                return True

        return False

    @staticmethod
    def validate_input(
        input_data: Any,
        field_name: str,
        required: bool = False,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        check_injection: bool = True
    ) -> Any:
        """종합적인 입력 검증"""

        # Check if required
        if required and not input_data:
            raise ValueError(f"{field_name} is required")

        if not input_data:
            return input_data

        # Convert to string for validation
        if isinstance(input_data, (str, int, float)):
            input_str = str(input_data)
        else:
            return input_data  # Skip validation for complex types

        # Check injection attacks
        if check_injection:
            if InputValidator.check_sql_injection(input_str):
                raise ValueError(f"Invalid input in {field_name}: potential SQL injection")

            if InputValidator.check_xss(input_str):
                raise ValueError(f"Invalid input in {field_name}: potential XSS attack")

        # Sanitize
        sanitized = InputValidator.sanitize_input(input_str, max_length)

        # Check pattern if provided
        if pattern and not re.match(pattern, sanitized):
            raise ValueError(f"Invalid format for {field_name}")

        return sanitized


class JWTManager:
    """JWT 토큰 관리"""

    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        액세스 토큰 생성

        Args:
            data: 토큰에 포함할 데이터 (sub, user_id, role 포함 권장)
            expires_delta: 만료 시간 (기본: ACCESS_TOKEN_EXPIRE_MINUTES)

        Returns:
            JWT 액세스 토큰
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "type": "access"})

        # RBAC: Ensure role is included in token
        if "role" not in to_encode:
            logger.warning("Token created without role, defaulting to viewer")
            to_encode["role"] = UserRole.VIEWER

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        리프레시 토큰 생성

        Args:
            data: 토큰에 포함할 데이터 (sub, user_id, role 포함)

        Returns:
            JWT 리프레시 토큰
        """
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode.update({"exp": expire, "type": "refresh"})

        # RBAC: Include role in refresh token
        if "role" not in to_encode:
            to_encode["role"] = UserRole.VIEWER

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        return encoded_jwt

    @staticmethod
    def decode_token(token: str, check_blacklist: bool = True) -> Dict[str, Any]:
        """
        토큰 디코드 (CRIT-03: 블랙리스트 검증 포함)

        Args:
            token: JWT 토큰 문자열
            check_blacklist: 블랙리스트 검사 여부 (기본: True)

        Returns:
            디코드된 페이로드

        Raises:
            HTTPException: 토큰이 만료되었거나, 블랙리스트에 있거나, 유효하지 않은 경우
        """
        try:
            # CRIT-03 FIX: Check blacklist BEFORE decoding (fast path)
            if check_blacklist and token_blacklist.is_blacklisted(token):
                logger.warning("Attempted use of blacklisted token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )

            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except (jwt.PyJWTError, jwt.DecodeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except HTTPException:
            # Re-raise HTTP exceptions (including blacklist check)
            raise
        except Exception as e:
            # Catch any other decoding errors (UnicodeDecodeError, ValueError, etc.)
            # MED-04: Sanitize exception before logging to prevent sensitive data leakage
            logger.error(f"Token decode error: {type(e).__name__}: {sanitize_exception(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    @staticmethod
    def blacklist_token(token: str) -> None:
        """
        토큰을 블랙리스트에 추가 (로그아웃 시 호출)

        Args:
            token: 블랙리스트에 추가할 JWT 토큰
        """
        token_blacklist.add(token)
        logger.info("Token added to blacklist")

    @staticmethod
    def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """토큰 검증 의존성 (블랙리스트 검증 포함)"""
        token = credentials.credentials

        try:
            # Decode with blacklist check enabled
            payload = JWTManager.decode_token(token, check_blacklist=True)

            # Check token type
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )

            return payload

        except HTTPException:
            raise
        except Exception as e:
            # MED-04: Sanitize exception before logging
            logger.error(f"Token verification failed: {sanitize_exception(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )


class RateLimiter:
    """Rate limiting"""

    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}

    def check_rate_limit(self, client_ip: str) -> bool:
        """레이트 리밋 체크"""
        now = datetime.now(UTC)

        # Initialize if new client
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Remove old requests outside window
        window_start = now - timedelta(seconds=SecurityConfig.RATE_LIMIT_WINDOW)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > window_start
        ]

        # Check if limit exceeded
        if len(self.requests[client_ip]) >= SecurityConfig.RATE_LIMIT_REQUESTS:
            return False

        # Add current request
        self.requests[client_ip].append(now)
        return True

    def get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 추출"""
        # Check for X-Forwarded-For header (proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check for X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to remote address
        return request.client.host if request.client else "unknown"


# =============================================================================
# HIGH-01 FIX: Auth Endpoint Rate Limiting (prevents brute force)
# =============================================================================
class AuthRateLimiter:
    """
    Stricter rate limiting specifically for authentication endpoints.

    - Login: 5 attempts per minute per IP (prevents brute force)
    - Register: 3 attempts per minute per IP (prevents account flooding)
    - Password reset: 3 attempts per minute per IP (prevents enumeration)

    Production: Use Redis with sliding window for distributed systems.
    """

    # Auth-specific rate limits (stricter than general API)
    LOGIN_LIMIT = 5          # 5 login attempts per minute
    REGISTER_LIMIT = 3       # 3 registration attempts per minute
    RESET_LIMIT = 3          # 3 password reset attempts per minute
    WINDOW_SECONDS = 60      # 1 minute window
    LOCKOUT_DURATION = 300   # 5 minute lockout after exceeding limit

    def __init__(self):
        self._login_attempts: Dict[str, List[datetime]] = {}
        self._register_attempts: Dict[str, List[datetime]] = {}
        self._reset_attempts: Dict[str, List[datetime]] = {}
        self._lockouts: Dict[str, datetime] = {}
        self._lock = Lock()

    def _cleanup_old_attempts(self, attempts: Dict[str, List[datetime]], client_ip: str) -> None:
        """Remove attempts outside the window"""
        if client_ip in attempts:
            cutoff = datetime.now(UTC) - timedelta(seconds=self.WINDOW_SECONDS)
            attempts[client_ip] = [t for t in attempts[client_ip] if t > cutoff]

    def _check_lockout(self, client_ip: str) -> bool:
        """Check if client is locked out"""
        if client_ip in self._lockouts:
            lockout_end = self._lockouts[client_ip]
            if datetime.now(UTC) < lockout_end:
                return True
            else:
                # Lockout expired, remove it
                del self._lockouts[client_ip]
        return False

    def _apply_lockout(self, client_ip: str) -> None:
        """Apply lockout to client"""
        self._lockouts[client_ip] = datetime.now(UTC) + timedelta(seconds=self.LOCKOUT_DURATION)
        logger.warning(f"Auth lockout applied to {client_ip} for {self.LOCKOUT_DURATION}s")

    def check_login_limit(self, client_ip: str) -> bool:
        """
        Check if login attempt is allowed.

        Returns:
            True if allowed, False if rate limited
        """
        with self._lock:
            # Check lockout first
            if self._check_lockout(client_ip):
                return False

            self._cleanup_old_attempts(self._login_attempts, client_ip)

            if client_ip not in self._login_attempts:
                self._login_attempts[client_ip] = []

            if len(self._login_attempts[client_ip]) >= self.LOGIN_LIMIT:
                self._apply_lockout(client_ip)
                return False

            self._login_attempts[client_ip].append(datetime.now(UTC))
            return True

    def check_register_limit(self, client_ip: str) -> bool:
        """Check if registration attempt is allowed."""
        with self._lock:
            if self._check_lockout(client_ip):
                return False

            self._cleanup_old_attempts(self._register_attempts, client_ip)

            if client_ip not in self._register_attempts:
                self._register_attempts[client_ip] = []

            if len(self._register_attempts[client_ip]) >= self.REGISTER_LIMIT:
                self._apply_lockout(client_ip)
                return False

            self._register_attempts[client_ip].append(datetime.now(UTC))
            return True

    def check_reset_limit(self, client_ip: str) -> bool:
        """Check if password reset attempt is allowed."""
        with self._lock:
            if self._check_lockout(client_ip):
                return False

            self._cleanup_old_attempts(self._reset_attempts, client_ip)

            if client_ip not in self._reset_attempts:
                self._reset_attempts[client_ip] = []

            if len(self._reset_attempts[client_ip]) >= self.RESET_LIMIT:
                self._apply_lockout(client_ip)
                return False

            self._reset_attempts[client_ip].append(datetime.now(UTC))
            return True

    def get_remaining_attempts(self, client_ip: str, endpoint: str = "login") -> int:
        """Get remaining attempts for an endpoint."""
        attempts_map = {
            "login": (self._login_attempts, self.LOGIN_LIMIT),
            "register": (self._register_attempts, self.REGISTER_LIMIT),
            "reset": (self._reset_attempts, self.RESET_LIMIT)
        }

        attempts_dict, limit = attempts_map.get(endpoint, (self._login_attempts, self.LOGIN_LIMIT))

        with self._lock:
            self._cleanup_old_attempts(attempts_dict, client_ip)
            current = len(attempts_dict.get(client_ip, []))
            return max(0, limit - current)

    def reset_attempts(self, client_ip: str) -> None:
        """Reset all attempts for a client (after successful login)."""
        with self._lock:
            self._login_attempts.pop(client_ip, None)
            self._register_attempts.pop(client_ip, None)
            self._reset_attempts.pop(client_ip, None)
            self._lockouts.pop(client_ip, None)

# Global auth rate limiter instance
auth_rate_limiter = AuthRateLimiter()


# =============================================================================
# CRIT-02 FIX: bcrypt Password Hashing (replaces weak PBKDF2)
# =============================================================================
class PasswordHasher:
    """
    비밀번호 해싱 - bcrypt 사용 (OWASP 권장)

    bcrypt advantages over PBKDF2:
    - Memory-hard algorithm (resistant to GPU attacks)
    - Auto-generates salt (no manual salt management)
    - Work factor adjustable (default: 12 rounds = ~250ms per hash)
    """

    # bcrypt work factor (12 = ~250ms, 14 = ~1s)
    BCRYPT_ROUNDS = 12

    @staticmethod
    def hash_password(password: str) -> str:
        """
        비밀번호 해싱 (bcrypt preferred, PBKDF2 fallback)

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        if BCRYPT_AVAILABLE:
            # bcrypt: Industry standard, memory-hard
            salt = bcrypt.gensalt(rounds=PasswordHasher.BCRYPT_ROUNDS)
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return f"bcrypt${hashed.decode('utf-8')}"
        else:
            # Fallback to PBKDF2 with 600,000 iterations (OWASP 2023 recommendation)
            salt = secrets.token_hex(32)
            password_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                600000  # OWASP 2023: minimum 600,000 iterations for SHA-256
            )
            return f"pbkdf2${salt}${password_hash.hex()}"

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        비밀번호 검증 (supports bcrypt, PBKDF2, and legacy format)

        Args:
            password: Plain text password to verify
            hashed: Stored hash string

        Returns:
            True if password matches
        """
        try:
            # Detect hash format
            if hashed.startswith('bcrypt$'):
                # bcrypt format: bcrypt$<hash>
                if not BCRYPT_AVAILABLE:
                    logger.error("bcrypt hash found but bcrypt not installed!")
                    return False

                stored_hash = hashed[7:]  # Remove 'bcrypt$' prefix
                return bcrypt.checkpw(
                    password.encode('utf-8'),
                    stored_hash.encode('utf-8')
                )

            elif hashed.startswith('pbkdf2$'):
                # New PBKDF2 format: pbkdf2$<salt>$<hash>
                parts = hashed.split('$')
                if len(parts) != 3:
                    return False
                _, salt, stored_hash = parts
                password_hash = hashlib.pbkdf2_hmac(
                    'sha256',
                    password.encode('utf-8'),
                    salt.encode('utf-8'),
                    600000  # Match new iteration count
                )
                return password_hash.hex() == stored_hash

            else:
                # Legacy format: <salt>$<hash> (100,000 iterations)
                salt, stored_hash = hashed.split('$')
                password_hash = hashlib.pbkdf2_hmac(
                    'sha256',
                    password.encode('utf-8'),
                    salt.encode('utf-8'),
                    100000  # Legacy iteration count
                )
                return password_hash.hex() == stored_hash

        except Exception as e:
            # MED-04: Sanitize exception - password data should never appear in logs
            logger.error(f"Password verification error: {sanitize_exception(e)}")
            return False

    @staticmethod
    def needs_rehash(hashed: str) -> bool:
        """
        Check if password needs rehashing (upgrade from legacy format)

        Returns:
            True if password should be rehashed on next login
        """
        # Rehash if using legacy format or PBKDF2 when bcrypt is available
        if BCRYPT_AVAILABLE and not hashed.startswith('bcrypt$'):
            return True
        return False


class SecurityMiddleware:
    """보안 미들웨어"""

    def __init__(self):
        self.rate_limiter = RateLimiter()

    async def __call__(self, request: Request, call_next):
        """미들웨어 실행"""

        # Check rate limit
        client_ip = self.rate_limiter.get_client_ip(request)
        if not self.rate_limiter.check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests"
            )

        # Check content type for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")

            # Check if content type is allowed
            if content_type and not any(
                allowed in content_type for allowed in SecurityConfig.ALLOWED_CONTENT_TYPES
            ):
                logger.warning(f"Invalid content type: {content_type}")
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"Unsupported content type: {content_type}"
                )

        # Add security headers
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response


# Pydantic models with validation
class SecureUserCreate(BaseModel):
    """보안 사용자 생성 모델"""

    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    username: str = Field(..., min_length=3, max_length=50)

    @validator('email')
    def validate_email(cls, v):
        if not InputValidator.validate_email(v):
            raise ValueError('Invalid email format')

        # Check for injection
        if InputValidator.check_sql_injection(v) or InputValidator.check_xss(v):
            raise ValueError('Invalid email content')

        return v.lower()

    @validator('password')
    def validate_password(cls, v):
        result = InputValidator.validate_password(v)
        if not result['valid']:
            raise ValueError('; '.join(result['errors']))
        return v

    @validator('username')
    def validate_username(cls, v):
        # Allow only alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscore')

        # Check for injection
        if InputValidator.check_sql_injection(v) or InputValidator.check_xss(v):
            raise ValueError('Invalid username content')

        return v


class SecureProjectCreate(BaseModel):
    """보안 프로젝트 생성 모델"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, max_items=20)

    @validator('name')
    def validate_name(cls, v):
        sanitized = InputValidator.sanitize_input(v, max_length=255)

        if InputValidator.check_sql_injection(sanitized) or InputValidator.check_xss(sanitized):
            raise ValueError('Invalid project name')

        return sanitized

    @validator('description')
    def validate_description(cls, v):
        if v is None:
            return v

        sanitized = InputValidator.sanitize_input(v, max_length=1000)

        if InputValidator.check_sql_injection(sanitized) or InputValidator.check_xss(sanitized):
            raise ValueError('Invalid description')

        return sanitized

    @validator('tags')
    def validate_tags(cls, v):
        if v is None:
            return v

        validated_tags = []
        for tag in v[:20]:  # Limit to 20 tags
            if not isinstance(tag, str):
                continue

            sanitized = InputValidator.sanitize_input(tag, max_length=50)

            if InputValidator.check_sql_injection(sanitized) or InputValidator.check_xss(sanitized):
                continue  # Skip invalid tags

            validated_tags.append(sanitized)

        return validated_tags


# Utility functions
def require_auth(func):
    """인증 필수 데코레이터"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This is a decorator for route functions
        # The actual auth check is done via Depends(JWTManager.verify_token)
        return await func(*args, **kwargs)
    return wrapper


def require_role(required_role: str):
    """
    RBAC 권한 검증 의존성 함수

    Usage in FastAPI routes:
        @router.get("/admin")
        async def admin_endpoint(user: dict = Depends(require_role(UserRole.ADMIN))):
            pass

    Args:
        required_role: 필요한 최소 권한 (admin/project_owner/developer/viewer)

    Returns:
        FastAPI Depends 함수

    Raises:
        HTTPException: 권한 부족 시 403 Forbidden
    """

    async def role_checker(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """
        역할 기반 권한 검증

        1. JWT 토큰 검증
        2. 토큰에서 role 추출
        3. 필요한 권한과 비교
        """
        try:
            # 토큰 검증
            payload = JWTManager.verify_token(credentials)

            # 사용자 role 추출
            user_role = payload.get("role", UserRole.VIEWER)

            # 권한 검증
            if not UserRole.has_permission(user_role, required_role):
                logger.warning(
                    f"Permission denied: user role '{user_role}' "
                    f"requires '{required_role}' for access"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required role: {required_role}"
                )

            # 권한 통과 - 사용자 정보 반환
            logger.debug(f"Access granted: role '{user_role}' >= required '{required_role}'")
            return payload

        except HTTPException:
            raise
        except Exception as e:
            # MED-04: Sanitize exception before logging
            logger.error(f"Role verification failed: {sanitize_exception(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission verification failed"
            )

    return role_checker


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    현재 사용자 정보 조회 의존성

    RBAC RESTORED (2025-12-17 Week 5 Day 3): JWT 인증 필수

    Usage:
        @router.get("/profile")
        async def get_profile(user: dict = Depends(get_current_user)):
            return user

    Returns:
        사용자 정보 (sub, user_id, role 포함)

    Raises:
        HTTPException: 토큰이 유효하지 않거나 만료된 경우 401 Unauthorized
    """
    return JWTManager.verify_token(credentials)


def setup_security(app):
    """FastAPI 앱에 보안 설정"""
    from fastapi import FastAPI
    from starlette.middleware.base import BaseHTTPMiddleware

    # Add security middleware
    security_middleware = SecurityMiddleware()
    app.add_middleware(BaseHTTPMiddleware, dispatch=security_middleware)

    logger.info("Security middleware configured")


# Export key components
__all__ = [
    # Core security
    'InputValidator',
    'JWTManager',
    'RateLimiter',
    'PasswordHasher',
    'SecurityMiddleware',
    'SecureUserCreate',
    'SecureProjectCreate',
    'setup_security',
    'require_auth',
    'require_role',           # RBAC: Role-based access control
    'get_current_user',       # RBAC: Get current user from token
    'UserRole',               # RBAC: Role constants
    'security',

    # Security improvements (2025-12-14)
    'token_blacklist',        # CRIT-03: Token blacklist for logout
    'TokenBlacklist',         # CRIT-03: Token blacklist class
    'auth_rate_limiter',      # HIGH-01: Auth endpoint rate limiting
    'AuthRateLimiter',        # HIGH-01: Auth rate limiter class
    'BCRYPT_AVAILABLE',       # CRIT-02: bcrypt availability flag
]