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

from backend.app.core.security import (
    JWTManager,
    UserRole,
    require_role,
    get_current_user,
    PasswordHasher
)
from backend.app.services.auth_service import AuthService


# ============================================================================
# 1. JWT Token Tests (6 tests)
# ============================================================================

class TestJWTTokens:
    """JWT [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]"""

    def test_create_access_token(self):
        """[EMOJI] [EMOJI] [EMOJI] - role [EMOJI] [EMOJI]"""
        # Given: [EMOJI] [EMOJI] (role [EMOJI])
        data = {
            "sub": "test@udo.dev",
            "user_id": 1,
            "role": UserRole.DEVELOPER
        }

        # When: [EMOJI] [EMOJI] [EMOJI]
        token = JWTManager.create_access_token(data)

        # Then: [EMOJI] [EMOJI] [EMOJI] role [EMOJI]
        payload = JWTManager.decode_token(token)
        assert payload["sub"] == "test@udo.dev"
        assert payload["user_id"] == 1
        assert payload["role"] == UserRole.DEVELOPER
        assert payload["type"] == "access"

    def test_create_access_token_without_role(self):
        """Role [EMOJI] [EMOJI] [EMOJI] [EMOJI] - viewer[EMOJI] [EMOJI] [EMOJI]"""
        # Given: role[EMOJI] [EMOJI] [EMOJI]
        data = {"sub": "test@udo.dev", "user_id": 1}

        # When: [EMOJI] [EMOJI]
        token = JWTManager.create_access_token(data)

        # Then: role[EMOJI] viewer[EMOJI] [EMOJI] [EMOJI]
        payload = JWTManager.decode_token(token)
        assert payload["role"] == UserRole.VIEWER

    def test_create_refresh_token(self):
        """[EMOJI] [EMOJI] [EMOJI] - role [EMOJI] [EMOJI]"""
        # Given: [EMOJI] [EMOJI]
        data = {
            "sub": "test@udo.dev",
            "user_id": 1,
            "role": UserRole.PROJECT_OWNER
        }

        # When: [EMOJI] [EMOJI] [EMOJI]
        token = JWTManager.create_refresh_token(data)

        # Then: [EMOJI] [EMOJI] [EMOJI] role [EMOJI]
        payload = JWTManager.decode_token(token)
        assert payload["type"] == "refresh"
        assert payload["role"] == UserRole.PROJECT_OWNER

    def test_decode_valid_token(self):
        """[EMOJI] [EMOJI] [EMOJI]"""
        # Given: [EMOJI] [EMOJI]
        data = {"sub": "test@udo.dev", "user_id": 1, "role": UserRole.ADMIN}
        token = JWTManager.create_access_token(data)

        # When: [EMOJI] [EMOJI]
        payload = JWTManager.decode_token(token)

        # Then: [EMOJI] [EMOJI]
        assert payload["sub"] == "test@udo.dev"
        assert payload["role"] == UserRole.ADMIN

    def test_decode_expired_token(self):
        """[EMOJI] [EMOJI] [EMOJI] - 401 [EMOJI]"""
        # Given: [EMOJI] [EMOJI] ([EMOJI] [EMOJI] 0[EMOJI])
        data = {"sub": "test@udo.dev", "user_id": 1, "role": UserRole.DEVELOPER}
        token = JWTManager.create_access_token(
            data,
            expires_delta=timedelta(seconds=-1)  # [EMOJI] [EMOJI]
        )

        # When/Then: HTTPException [EMOJI]
        with pytest.raises(HTTPException) as exc_info:
            JWTManager.decode_token(token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_decode_invalid_token(self):
        """[EMOJI] [EMOJI] [EMOJI] - 401 [EMOJI]"""
        # Given: [EMOJI] [EMOJI]
        invalid_token = "invalid.jwt.token"

        # When/Then: HTTPException [EMOJI]
        with pytest.raises(HTTPException) as exc_info:
            JWTManager.decode_token(invalid_token)

        assert exc_info.value.status_code == 401


# ============================================================================
# 2. RBAC Permission Tests (8 tests)
# ============================================================================

class TestRBACPermissions:
    """Role-based access control [EMOJI] [EMOJI] [EMOJI]"""

    def test_role_hierarchy(self):
        """Role [EMOJI] [EMOJI] [EMOJI] - admin > project_owner > developer > viewer"""
        # Role hierarchy [EMOJI]
        assert UserRole.ROLE_HIERARCHY[UserRole.ADMIN] == 4
        assert UserRole.ROLE_HIERARCHY[UserRole.PROJECT_OWNER] == 3
        assert UserRole.ROLE_HIERARCHY[UserRole.DEVELOPER] == 2
        assert UserRole.ROLE_HIERARCHY[UserRole.VIEWER] == 1

    def test_admin_has_all_permissions(self):
        """Admin[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
        # Admin[EMOJI] [EMOJI] role[EMOJI] [EMOJI] [EMOJI]
        assert UserRole.has_permission(UserRole.ADMIN, UserRole.ADMIN) is True
        assert UserRole.has_permission(UserRole.ADMIN, UserRole.PROJECT_OWNER) is True
        assert UserRole.has_permission(UserRole.ADMIN, UserRole.DEVELOPER) is True
        assert UserRole.has_permission(UserRole.ADMIN, UserRole.VIEWER) is True

    def test_project_owner_permissions(self):
        """Project Owner [EMOJI] [EMOJI]"""
        # Project Owner[EMOJI] developer, viewer [EMOJI] [EMOJI], admin[EMOJI] [EMOJI]
        assert UserRole.has_permission(UserRole.PROJECT_OWNER, UserRole.ADMIN) is False
        assert UserRole.has_permission(UserRole.PROJECT_OWNER, UserRole.PROJECT_OWNER) is True
        assert UserRole.has_permission(UserRole.PROJECT_OWNER, UserRole.DEVELOPER) is True
        assert UserRole.has_permission(UserRole.PROJECT_OWNER, UserRole.VIEWER) is True

    def test_developer_permissions(self):
        """Developer [EMOJI] [EMOJI]"""
        # Developer[EMOJI] developer, viewer [EMOJI] [EMOJI]
        assert UserRole.has_permission(UserRole.DEVELOPER, UserRole.ADMIN) is False
        assert UserRole.has_permission(UserRole.DEVELOPER, UserRole.PROJECT_OWNER) is False
        assert UserRole.has_permission(UserRole.DEVELOPER, UserRole.DEVELOPER) is True
        assert UserRole.has_permission(UserRole.DEVELOPER, UserRole.VIEWER) is True

    def test_viewer_permissions(self):
        """Viewer [EMOJI] [EMOJI] - [EMOJI] [EMOJI]"""
        # Viewer[EMOJI] viewer[EMOJI] [EMOJI] [EMOJI]
        assert UserRole.has_permission(UserRole.VIEWER, UserRole.ADMIN) is False
        assert UserRole.has_permission(UserRole.VIEWER, UserRole.PROJECT_OWNER) is False
        assert UserRole.has_permission(UserRole.VIEWER, UserRole.DEVELOPER) is False
        assert UserRole.has_permission(UserRole.VIEWER, UserRole.VIEWER) is True

    def test_get_all_roles(self):
        """[EMOJI] role [EMOJI] [EMOJI]"""
        roles = UserRole.get_all_roles()

        assert len(roles) == 4
        assert UserRole.ADMIN in roles
        assert UserRole.PROJECT_OWNER in roles
        assert UserRole.DEVELOPER in roles
        assert UserRole.VIEWER in roles

    @pytest.mark.asyncio
    async def test_require_role_admin_success(self):
        """require_role: Admin [EMOJI] Admin [EMOJI] [EMOJI] - [EMOJI]"""
        # Given: Admin [EMOJI]
        data = {"sub": "admin@udo.dev", "user_id": 1, "role": UserRole.ADMIN}
        token = JWTManager.create_access_token(data)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # When: Admin [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        role_checker = require_role(UserRole.ADMIN)
        result = await role_checker(credentials)

        # Then: [EMOJI] ([EMOJI] [EMOJI])
        assert result["role"] == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_require_role_insufficient_permission(self):
        """require_role: Developer[EMOJI] Admin [EMOJI] [EMOJI] - 403 [EMOJI]"""
        # Given: Developer [EMOJI]
        data = {"sub": "dev@udo.dev", "user_id": 2, "role": UserRole.DEVELOPER}
        token = JWTManager.create_access_token(data)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # When/Then: Admin [EMOJI] [EMOJI] -> 403 Forbidden
        role_checker = require_role(UserRole.ADMIN)

        with pytest.raises(HTTPException) as exc_info:
            await role_checker(credentials)

        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail


# ============================================================================
# 3. Auth Endpoint Tests (6 tests)
# ============================================================================

class TestAuthEndpoints:
    """[EMOJI] [EMOJI] [EMOJI] (AuthService [EMOJI])"""

    @pytest.mark.asyncio
    async def test_create_user_with_default_role(self):
        """[EMOJI] [EMOJI] - [EMOJI] role[EMOJI] developer"""
        # Given: [EMOJI] [EMOJI] [EMOJI]
        auth_service = AuthService()
        auth_service.clear_all_users()  # Reset for clean test

        # When: [EMOJI] [EMOJI]
        user = await auth_service.create_user(
            email="newuser@test.com",
            password="Test123!@#",
            username="newuser"
        )

        # Then: role[EMOJI] developer[EMOJI] [EMOJI]
        assert user is not None
        assert user["role"] == UserRole.DEVELOPER

    @pytest.mark.asyncio
    async def test_authenticate_user_with_role(self):
        """[EMOJI] [EMOJI] - role [EMOJI] [EMOJI]"""
        # Given: [EMOJI] [EMOJI] (admin@udo.dev)
        auth_service = AuthService()

        # When: [EMOJI]
        user = await auth_service.authenticate_user(
            email="admin@udo.dev",
            password="admin123!@#"
        )

        # Then: role [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        assert user is not None
        assert user["role"] == UserRole.ADMIN
        assert user["email"] == "admin@udo.dev"

    @pytest.mark.asyncio
    async def test_get_user_includes_role(self):
        """[EMOJI] [EMOJI] - role [EMOJI]"""
        # Given: [EMOJI] [EMOJI]
        auth_service = AuthService()

        # When: [EMOJI] [EMOJI]
        user = await auth_service.get_user("dev@udo.dev")

        # Then: role [EMOJI]
        assert user is not None
        assert user["role"] == UserRole.DEVELOPER

    @pytest.mark.asyncio
    async def test_update_user_role(self):
        """[EMOJI] role [EMOJI]"""
        # Given: Developer [EMOJI]
        auth_service = AuthService()
        user = await auth_service.get_user("dev@udo.dev")
        assert user["role"] == UserRole.DEVELOPER

        # When: Project Owner[EMOJI] [EMOJI]
        updated_user = await auth_service.update_user(
            email="dev@udo.dev",
            update_data={"role": UserRole.PROJECT_OWNER}
        )

        # Then: role [EMOJI] [EMOJI]
        assert updated_user["role"] == UserRole.PROJECT_OWNER

    @pytest.mark.asyncio
    async def test_list_users_shows_roles(self):
        """[EMOJI] [EMOJI] [EMOJI] - [EMOJI] role [EMOJI]"""
        # Given: [EMOJI] [EMOJI] 4[EMOJI] (4 roles)
        auth_service = AuthService()

        # When: [EMOJI] [EMOJI] [EMOJI]
        result = await auth_service.list_users(limit=10)

        # Then: 4[EMOJI] role[EMOJI] [EMOJI] [EMOJI]
        users = result["users"]
        assert len(users) == 4

        roles_found = {user["role"] for user in users}
        assert UserRole.ADMIN in roles_found
        assert UserRole.PROJECT_OWNER in roles_found
        assert UserRole.DEVELOPER in roles_found
        assert UserRole.VIEWER in roles_found

    def test_password_hasher(self):
        """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
        # Given: [EMOJI] [EMOJI]
        password = "Test123!@#"

        # When: [EMOJI]
        hashed = PasswordHasher.hash_password(password)

        # Then: [EMOJI] [EMOJI]
        assert PasswordHasher.verify_password(password, hashed) is True
        assert PasswordHasher.verify_password("wrong_password", hashed) is False


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    # Run: pytest backend/tests/test_auth_rbac.py -v
    pytest.main([__file__, "-v", "--tb=short"])
