"""
Authentication Service

사용자 인증 및 관리 서비스입니다.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging
from ..core.security import PasswordHasher
from ..core.log_sanitizer import sanitize_exception

logger = logging.getLogger(__name__)


class AuthService:
    """
    인증 서비스

    실제 환경에서는 데이터베이스와 연동하지만,
    현재는 메모리 기반 Mock 구현을 사용합니다.
    """

    def __init__(self):
        """AuthService 초기화"""
        # Mock user storage (실제 환경에서는 데이터베이스 사용)
        self.users: Dict[str, Dict[str, Any]] = {}
        self.user_id_counter = 1

        # 테스트용 기본 사용자 추가
        self._create_default_users()

    def _create_default_users(self):
        """테스트용 기본 사용자 생성 (4 roles)"""
        from ..core.security import UserRole

        # 1. Admin user (full access)
        admin_password = PasswordHasher.hash_password("admin123!@#")
        self.users["admin@udo.dev"] = {
            "id": self.user_id_counter,
            "email": "admin@udo.dev",
            "username": "admin",
            "password_hash": admin_password,
            "full_name": "System Administrator",
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
            "role": UserRole.ADMIN
        }
        self.user_id_counter += 1

        # 2. Project Owner (project management)
        owner_password = PasswordHasher.hash_password("owner123!@#")
        self.users["owner@udo.dev"] = {
            "id": self.user_id_counter,
            "email": "owner@udo.dev",
            "username": "projectowner",
            "password_hash": owner_password,
            "full_name": "Project Owner",
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
            "role": UserRole.PROJECT_OWNER
        }
        self.user_id_counter += 1

        # 3. Developer (task management)
        dev_password = PasswordHasher.hash_password("dev123!@#")
        self.users["dev@udo.dev"] = {
            "id": self.user_id_counter,
            "email": "dev@udo.dev",
            "username": "developer",
            "password_hash": dev_password,
            "full_name": "Developer User",
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
            "role": UserRole.DEVELOPER
        }
        self.user_id_counter += 1

        # 4. Viewer (read-only)
        viewer_password = PasswordHasher.hash_password("viewer123!@#")
        self.users["viewer@udo.dev"] = {
            "id": self.user_id_counter,
            "email": "viewer@udo.dev",
            "username": "viewer",
            "password_hash": viewer_password,
            "full_name": "Viewer User",
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
            "role": UserRole.VIEWER
        }
        self.user_id_counter += 1

        logger.info("Default users created for testing (4 roles: admin, project_owner, developer, viewer)")

    async def create_user(
        self,
        email: str,
        password: str,
        username: str,
        full_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        새로운 사용자 생성

        Args:
            email: 사용자 이메일
            password: 비밀번호 (평문)
            username: 사용자명
            full_name: 전체 이름 (선택)

        Returns:
            생성된 사용자 정보 또는 None (중복인 경우)
        """
        try:
            # 이메일 중복 확인
            if email.lower() in self.users:
                logger.warning(f"User already exists: {email}")
                return None

            # 사용자명 중복 확인
            for user in self.users.values():
                if user["username"].lower() == username.lower():
                    logger.warning(f"Username already taken: {username}")
                    return None

            # 비밀번호 해싱
            password_hash = PasswordHasher.hash_password(password)

            # 새 사용자 생성 (기본 role: developer)
            from ..core.security import UserRole

            new_user = {
                "id": self.user_id_counter,
                "email": email.lower(),
                "username": username,
                "password_hash": password_hash,
                "full_name": full_name,
                "created_at": datetime.utcnow().isoformat(),
                "is_active": True,
                "role": UserRole.DEVELOPER  # Default role for new users
            }

            # 저장
            self.users[email.lower()] = new_user
            self.user_id_counter += 1

            logger.info(f"New user created: {email}")

            # 비밀번호 해시 제거 후 반환
            user_data = new_user.copy()
            del user_data["password_hash"]
            return user_data

        except Exception as e:
            # MED-04: Sanitize exception before logging
            logger.error(f"Failed to create user: {sanitize_exception(e)}")
            return None

    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """
        사용자 인증

        Args:
            email: 사용자 이메일
            password: 비밀번호 (평문)

        Returns:
            인증된 사용자 정보 또는 None
        """
        try:
            # 사용자 조회
            user = self.users.get(email.lower())
            if not user:
                logger.warning(f"User not found: {email}")
                return None

            # 비활성 사용자 체크
            if not user.get("is_active", True):
                logger.warning(f"Inactive user attempted login: {email}")
                return None

            # 비밀번호 검증
            if not PasswordHasher.verify_password(password, user["password_hash"]):
                logger.warning(f"Invalid password for user: {email}")
                return None

            logger.info(f"User authenticated: {email}")

            # 비밀번호 해시 제거 후 반환
            user_data = user.copy()
            del user_data["password_hash"]
            return user_data

        except Exception as e:
            # MED-04: Sanitize exception before logging
            logger.error(f"Authentication error: {sanitize_exception(e)}")
            return None

    async def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """
        사용자 정보 조회

        Args:
            email: 사용자 이메일

        Returns:
            사용자 정보 또는 None
        """
        try:
            user = self.users.get(email.lower())
            if not user:
                return None

            # 비밀번호 해시 제거 후 반환
            user_data = user.copy()
            del user_data["password_hash"]
            return user_data

        except Exception as e:
            # MED-04: Sanitize exception before logging
            logger.error(f"Failed to get user: {sanitize_exception(e)}")
            return None

    async def update_user(
        self,
        email: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        사용자 정보 업데이트

        Args:
            email: 사용자 이메일
            update_data: 업데이트할 데이터

        Returns:
            업데이트된 사용자 정보 또는 None
        """
        try:
            user = self.users.get(email.lower())
            if not user:
                return None

            # 업데이트 가능한 필드만 처리
            allowed_fields = ["full_name", "is_active", "role"]
            for field in allowed_fields:
                if field in update_data:
                    user[field] = update_data[field]

            # 비밀번호 변경 처리
            if "password" in update_data:
                user["password_hash"] = PasswordHasher.hash_password(
                    update_data["password"]
                )

            # 업데이트 시간 기록
            user["updated_at"] = datetime.utcnow().isoformat()

            logger.info(f"User updated: {email}")

            # 비밀번호 해시 제거 후 반환
            user_data = user.copy()
            del user_data["password_hash"]
            return user_data

        except Exception as e:
            # MED-04: Sanitize exception before logging
            logger.error(f"Failed to update user: {sanitize_exception(e)}")
            return None

    async def delete_user(self, email: str) -> bool:
        """
        사용자 삭제

        Args:
            email: 사용자 이메일

        Returns:
            삭제 성공 여부
        """
        try:
            if email.lower() in self.users:
                del self.users[email.lower()]
                logger.info(f"User deleted: {email}")
                return True
            return False

        except Exception as e:
            # MED-04: Sanitize exception before logging
            logger.error(f"Failed to delete user: {sanitize_exception(e)}")
            return False

    async def list_users(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        사용자 목록 조회

        Args:
            limit: 조회할 개수
            offset: 시작 위치

        Returns:
            사용자 목록과 메타데이터
        """
        try:
            # 전체 사용자 목록 (비밀번호 해시 제외)
            all_users = []
            for user in self.users.values():
                user_data = user.copy()
                del user_data["password_hash"]
                all_users.append(user_data)

            # 정렬 (생성일 기준 내림차순)
            all_users.sort(
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )

            # 페이지네이션
            total = len(all_users)
            users = all_users[offset:offset + limit]

            return {
                "users": users,
                "total": total,
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            # MED-04: Sanitize exception before logging
            logger.error(f"Failed to list users: {sanitize_exception(e)}")
            return {
                "users": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }

    def get_user_count(self) -> int:
        """전체 사용자 수 반환"""
        return len(self.users)

    def clear_all_users(self):
        """모든 사용자 삭제 (테스트용)"""
        self.users.clear()
        self.user_id_counter = 1
        logger.warning("All users cleared!")


# Create singleton instance
auth_service = AuthService()

# Export
__all__ = ['AuthService', 'auth_service']