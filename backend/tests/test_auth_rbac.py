"""
JWT Authentication + RBAC Tests

Week 2 Day 1-2: Test JWT authentication and role-based access control.

Test Coverage:
- JWT token generation and validation (6 tests)
- Role-based permissions (8 tests)
- Auth endpoints (6 tests)

Total: 20 tests
"""

import pytest
from datetime import timedelta
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.app.core.security import JWTManager, UserRole, require_role, PasswordHasher
from backend.app.services.auth_service import AuthService


@pytest.fixture(autouse=True)
def disable_dev_auth_bypass(monkeypatch):
    """
    테스트 중 dev auth bypass 비활성화.
    CRIT-01 보안 수정 후 테스트가 올바른 에러 동작을 검증하도록 함.
    """
    monkeypatch.setenv("DISABLE_DEV_AUTH_BYPASS", "true")


# ============================================================================
# 1. JWT Token Tests (6 tests)
# ============================================================================


class TestJWTTokens:
    """JWT 토큰 생성 및 검증 테스트"""

    def test_create_access_token(self):
        """액세스 토큰 생성 - role 포함 확인"""
        # Given: 사용자 데이터 (role 포함)
        data = {"sub": "test@udo.dev", "user_id": 1, "role": UserRole.DEVELOPER}

        # When: 액세스 토큰 생성
        token = JWTManager.create_access_token(data)

        # Then: 토큰 디코드 및 role 확인
        payload = JWTManager.decode_token(token)
        assert payload["sub"] == "test@udo.dev"
        assert payload["user_id"] == 1
        assert payload["role"] == UserRole.DEVELOPER
        assert payload["type"] == "access"

    def test_create_access_token_without_role(self):
        """Role 없이 액세스 토큰 생성 - viewer로 기본값 설정"""
        # Given: role이 없는 데이터
        data = {"sub": "test@udo.dev", "user_id": 1}

        # When: 토큰 생성
        token = JWTManager.create_access_token(data)

        # Then: role이 viewer로 기본 설정됨
        payload = JWTManager.decode_token(token)
        assert payload["role"] == UserRole.VIEWER

    def test_create_refresh_token(self):
        """리프레시 토큰 생성 - role 포함 확인"""
        # Given: 사용자 데이터
        data = {"sub": "test@udo.dev", "user_id": 1, "role": UserRole.PROJECT_OWNER}

        # When: 리프레시 토큰 생성
        token = JWTManager.create_refresh_token(data)

        # Then: 토큰 디코드 및 role 확인
        payload = JWTManager.decode_token(token)
        assert payload["type"] == "refresh"
        assert payload["role"] == UserRole.PROJECT_OWNER

    def test_decode_valid_token(self):
        """유효한 토큰 디코드"""
        # Given: 유효한 토큰
        data = {"sub": "test@udo.dev", "user_id": 1, "role": UserRole.ADMIN}
        token = JWTManager.create_access_token(data)

        # When: 토큰 디코드
        payload = JWTManager.decode_token(token)

        # Then: 페이로드 검증
        assert payload["sub"] == "test@udo.dev"
        assert payload["role"] == UserRole.ADMIN

    def test_decode_expired_token(self):
        """만료된 토큰 디코드 - 401 에러"""
        # Given: 만료된 토큰 (만료 시간 0초)
        data = {"sub": "test@udo.dev", "user_id": 1, "role": UserRole.DEVELOPER}
        token = JWTManager.create_access_token(data, expires_delta=timedelta(seconds=-1))  # 이미 만료됨

        # When/Then: HTTPException 발생
        with pytest.raises(HTTPException) as exc_info:
            JWTManager.decode_token(token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_decode_invalid_token(self):
        """잘못된 토큰 디코드 - 401 에러"""
        # Given: 잘못된 토큰
        invalid_token = "invalid.jwt.token"

        # When/Then: HTTPException 발생
        with pytest.raises(HTTPException) as exc_info:
            JWTManager.decode_token(invalid_token)

        assert exc_info.value.status_code == 401


# ============================================================================
# 2. RBAC Permission Tests (8 tests)
# ============================================================================


class TestRBACPermissions:
    """Role-based access control 권한 검증 테스트"""

    def test_role_hierarchy(self):
        """Role 계층 구조 확인 - admin > project_owner > developer > viewer"""
        # Role hierarchy 확인
        assert UserRole.ROLE_HIERARCHY[UserRole.ADMIN] == 4
        assert UserRole.ROLE_HIERARCHY[UserRole.PROJECT_OWNER] == 3
        assert UserRole.ROLE_HIERARCHY[UserRole.DEVELOPER] == 2
        assert UserRole.ROLE_HIERARCHY[UserRole.VIEWER] == 1

    def test_admin_has_all_permissions(self):
        """Admin은 모든 권한 보유"""
        # Admin은 모든 role에 접근 가능
        assert UserRole.has_permission(UserRole.ADMIN, UserRole.ADMIN) is True
        assert UserRole.has_permission(UserRole.ADMIN, UserRole.PROJECT_OWNER) is True
        assert UserRole.has_permission(UserRole.ADMIN, UserRole.DEVELOPER) is True
        assert UserRole.has_permission(UserRole.ADMIN, UserRole.VIEWER) is True

    def test_project_owner_permissions(self):
        """Project Owner 권한 확인"""
        # Project Owner는 developer, viewer 접근 가능, admin은 불가
        assert UserRole.has_permission(UserRole.PROJECT_OWNER, UserRole.ADMIN) is False
        assert UserRole.has_permission(UserRole.PROJECT_OWNER, UserRole.PROJECT_OWNER) is True
        assert UserRole.has_permission(UserRole.PROJECT_OWNER, UserRole.DEVELOPER) is True
        assert UserRole.has_permission(UserRole.PROJECT_OWNER, UserRole.VIEWER) is True

    def test_developer_permissions(self):
        """Developer 권한 확인"""
        # Developer는 developer, viewer 접근 가능
        assert UserRole.has_permission(UserRole.DEVELOPER, UserRole.ADMIN) is False
        assert UserRole.has_permission(UserRole.DEVELOPER, UserRole.PROJECT_OWNER) is False
        assert UserRole.has_permission(UserRole.DEVELOPER, UserRole.DEVELOPER) is True
        assert UserRole.has_permission(UserRole.DEVELOPER, UserRole.VIEWER) is True

    def test_viewer_permissions(self):
        """Viewer 권한 확인 - 최소 권한"""
        # Viewer는 viewer만 접근 가능
        assert UserRole.has_permission(UserRole.VIEWER, UserRole.ADMIN) is False
        assert UserRole.has_permission(UserRole.VIEWER, UserRole.PROJECT_OWNER) is False
        assert UserRole.has_permission(UserRole.VIEWER, UserRole.DEVELOPER) is False
        assert UserRole.has_permission(UserRole.VIEWER, UserRole.VIEWER) is True

    def test_get_all_roles(self):
        """모든 role 목록 조회"""
        roles = UserRole.get_all_roles()

        assert len(roles) == 4
        assert UserRole.ADMIN in roles
        assert UserRole.PROJECT_OWNER in roles
        assert UserRole.DEVELOPER in roles
        assert UserRole.VIEWER in roles

    @pytest.mark.asyncio
    async def test_require_role_admin_success(self):
        """require_role: Admin 권한으로 Admin 엔드포인트 접근 - 성공"""
        # Given: Admin 토큰
        data = {"sub": "admin@udo.dev", "user_id": 1, "role": UserRole.ADMIN}
        token = JWTManager.create_access_token(data)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # When: Admin 권한 요구하는 함수 호출
        role_checker = require_role(UserRole.ADMIN)
        result = await role_checker(credentials)

        # Then: 성공 (예외 없음)
        assert result["role"] == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_require_role_insufficient_permission(self):
        """require_role: Developer가 Admin 엔드포인트 접근 - 403 에러"""
        # Given: Developer 토큰
        data = {"sub": "dev@udo.dev", "user_id": 2, "role": UserRole.DEVELOPER}
        token = JWTManager.create_access_token(data)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # When/Then: Admin 권한 필요 → 403 Forbidden
        role_checker = require_role(UserRole.ADMIN)

        with pytest.raises(HTTPException) as exc_info:
            await role_checker(credentials)

        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail


# ============================================================================
# 3. Auth Endpoint Tests (6 tests)
# ============================================================================


class TestAuthEndpoints:
    """인증 엔드포인트 테스트 (AuthService 통합)"""

    @pytest.mark.asyncio
    async def test_create_user_with_default_role(self):
        """사용자 생성 - 기본 role은 developer"""
        # Given: 새로운 사용자 정보
        auth_service = AuthService()
        auth_service.clear_all_users()  # Reset for clean test

        # When: 사용자 생성
        user = await auth_service.create_user(email="newuser@test.com", password="Test123!@#", username="newuser")

        # Then: role이 developer로 생성됨
        assert user is not None
        assert user["role"] == UserRole.DEVELOPER

    @pytest.mark.asyncio
    async def test_authenticate_user_with_role(self):
        """사용자 인증 - role 정보 반환"""
        # Given: 기본 사용자 (admin@udo.dev)
        auth_service = AuthService()

        # When: 인증
        user = await auth_service.authenticate_user(email="admin@udo.dev", password="admin123!@#")

        # Then: role 포함된 사용자 정보 반환
        assert user is not None
        assert user["role"] == UserRole.ADMIN
        assert user["email"] == "admin@udo.dev"

    @pytest.mark.asyncio
    async def test_get_user_includes_role(self):
        """사용자 조회 - role 포함"""
        # Given: 기본 사용자
        auth_service = AuthService()

        # When: 사용자 조회
        user = await auth_service.get_user("dev@udo.dev")

        # Then: role 포함
        assert user is not None
        assert user["role"] == UserRole.DEVELOPER

    @pytest.mark.asyncio
    async def test_update_user_role(self):
        """사용자 role 업데이트"""
        # Given: Developer 사용자
        auth_service = AuthService()
        user = await auth_service.get_user("dev@udo.dev")
        assert user["role"] == UserRole.DEVELOPER

        # When: Project Owner로 업그레이드
        updated_user = await auth_service.update_user(email="dev@udo.dev", update_data={"role": UserRole.PROJECT_OWNER})

        # Then: role 업데이트 확인
        assert updated_user["role"] == UserRole.PROJECT_OWNER

    @pytest.mark.asyncio
    async def test_list_users_shows_roles(self):
        """사용자 목록 조회 - 모든 role 표시"""
        # Given: 기본 사용자 4명 (4 roles)
        auth_service = AuthService()

        # When: 사용자 목록 조회
        result = await auth_service.list_users(limit=10)

        # Then: 4명의 role이 모두 표시됨
        users = result["users"]
        assert len(users) == 4

        roles_found = {user["role"] for user in users}
        assert UserRole.ADMIN in roles_found
        assert UserRole.PROJECT_OWNER in roles_found
        assert UserRole.DEVELOPER in roles_found
        assert UserRole.VIEWER in roles_found

    def test_password_hasher(self):
        """비밀번호 해싱 및 검증"""
        # Given: 평문 비밀번호
        password = "Test123!@#"

        # When: 해싱
        hashed = PasswordHasher.hash_password(password)

        # Then: 검증 성공
        assert PasswordHasher.verify_password(password, hashed) is True
        assert PasswordHasher.verify_password("wrong_password", hashed) is False


# ============================================================================
# 4. Rate Limiting Tests (HIGH-02 FIX) - 5 tests
# ============================================================================


class TestRateLimiting:
    """Rate limiting 테스트 - HIGH-02 보안 수정 검증"""

    def setup_method(self):
        """각 테스트 전 rate limiter 리셋"""
        from backend.app.core.security import auth_rate_limiter

        # Reset all attempts for test isolation
        auth_rate_limiter._login_attempts = {}
        auth_rate_limiter._register_attempts = {}
        auth_rate_limiter._reset_attempts = {}
        auth_rate_limiter._lockouts = {}

    def test_login_rate_limit_allows_under_threshold(self):
        """로그인 시도 5회 미만 허용"""
        from backend.app.core.security import auth_rate_limiter

        client_ip = "192.168.1.100"

        # 4번 시도 (5회 제한 미만)
        for i in range(4):
            assert auth_rate_limiter.check_login_limit(client_ip) is True

        # 5번째도 허용 (5회까지 OK)
        assert auth_rate_limiter.check_login_limit(client_ip) is True

    def test_login_rate_limit_blocks_after_threshold(self):
        """로그인 시도 5회 초과 후 차단"""
        from backend.app.core.security import auth_rate_limiter

        client_ip = "192.168.1.101"

        # 5번 시도
        for i in range(5):
            auth_rate_limiter.check_login_limit(client_ip)

        # 6번째 시도 차단
        assert auth_rate_limiter.check_login_limit(client_ip) is False

    def test_register_rate_limit_blocks_after_threshold(self):
        """등록 시도 3회 초과 후 차단"""
        from backend.app.core.security import auth_rate_limiter

        client_ip = "192.168.1.102"

        # 3번 시도
        for i in range(3):
            auth_rate_limiter.check_register_limit(client_ip)

        # 4번째 시도 차단
        assert auth_rate_limiter.check_register_limit(client_ip) is False

    def test_remaining_attempts_calculation(self):
        """남은 시도 횟수 계산"""
        from backend.app.core.security import auth_rate_limiter

        client_ip = "192.168.1.103"

        # 초기 상태: 5회 남음
        assert auth_rate_limiter.get_remaining_attempts(client_ip, "login") == 5

        # 2번 시도 후: 3회 남음
        auth_rate_limiter.check_login_limit(client_ip)
        auth_rate_limiter.check_login_limit(client_ip)
        assert auth_rate_limiter.get_remaining_attempts(client_ip, "login") == 3

    def test_reset_attempts_clears_all(self):
        """성공 시 모든 시도 횟수 리셋"""
        from backend.app.core.security import auth_rate_limiter

        client_ip = "192.168.1.104"

        # 4번 시도
        for i in range(4):
            auth_rate_limiter.check_login_limit(client_ip)

        # 남은 횟수 1회
        assert auth_rate_limiter.get_remaining_attempts(client_ip, "login") == 1

        # 리셋 후 5회로 복원
        auth_rate_limiter.reset_attempts(client_ip)
        assert auth_rate_limiter.get_remaining_attempts(client_ip, "login") == 5


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    # Run: pytest backend/tests/test_auth_rbac.py -v
    pytest.main([__file__, "-v", "--tb=short"])
