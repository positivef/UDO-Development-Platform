"""
Authentication Service

[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
"""

from typing import Optional, Dict, Any
from datetime import datetime, UTC
import logging
from ..core.security import PasswordHasher
from ..core.log_sanitizer import sanitize_exception

logger = logging.getLogger(__name__)


class AuthService:
    """
    [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] [EMOJI] [EMOJI],
    [EMOJI] [EMOJI] [EMOJI] Mock [EMOJI] [EMOJI].
    """

    def __init__(self):
        """AuthService [EMOJI]"""
        # Mock user storage ([EMOJI] [EMOJI] [EMOJI] [EMOJI])
        self.users: Dict[str, Dict[str, Any]] = {}
        self.user_id_counter = 1

        # [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        self._create_default_users()

    def _create_default_users(self):
        """[EMOJI] [EMOJI] [EMOJI] [EMOJI] (4 roles)"""
        from ..core.security import UserRole

        # 1. Admin user (full access)
        admin_password = PasswordHasher.hash_password("admin123!@#")
        self.users["admin@udo.dev"] = {
            "id": self.user_id_counter,
            "email": "admin@udo.dev",
            "username": "admin",
            "password_hash": admin_password,
            "full_name": "System Administrator",
            "created_at": datetime.now(UTC).isoformat(),
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
            "created_at": datetime.now(UTC).isoformat(),
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
            "created_at": datetime.now(UTC).isoformat(),
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
            "created_at": datetime.now(UTC).isoformat(),
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
        [EMOJI] [EMOJI] [EMOJI]

        Args:
            email: [EMOJI] [EMOJI]
            password: [EMOJI] ([EMOJI])
            username: [EMOJI]
            full_name: [EMOJI] [EMOJI] ([EMOJI])

        Returns:
            [EMOJI] [EMOJI] [EMOJI] [EMOJI] None ([EMOJI] [EMOJI])
        """
        try:
            # [EMOJI] [EMOJI] [EMOJI]
            if email.lower() in self.users:
                logger.warning(f"User already exists: {email}")
                return None

            # [EMOJI] [EMOJI] [EMOJI]
            for user in self.users.values():
                if user["username"].lower() == username.lower():
                    logger.warning(f"Username already taken: {username}")
                    return None

            # [EMOJI] [EMOJI]
            password_hash = PasswordHasher.hash_password(password)

            # [EMOJI] [EMOJI] [EMOJI] ([EMOJI] role: developer)
            from ..core.security import UserRole

            new_user = {
                "id": self.user_id_counter,
                "email": email.lower(),
                "username": username,
                "password_hash": password_hash,
                "full_name": full_name,
                "created_at": datetime.now(UTC).isoformat(),
                "is_active": True,
                "role": UserRole.DEVELOPER  # Default role for new users
            }

            # [EMOJI]
            self.users[email.lower()] = new_user
            self.user_id_counter += 1

            logger.info(f"New user created: {email}")

            # [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
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
        [EMOJI] [EMOJI]

        Args:
            email: [EMOJI] [EMOJI]
            password: [EMOJI] ([EMOJI])

        Returns:
            [EMOJI] [EMOJI] [EMOJI] [EMOJI] None
        """
        try:
            # [EMOJI] [EMOJI]
            user = self.users.get(email.lower())
            if not user:
                logger.warning(f"User not found: {email}")
                return None

            # [EMOJI] [EMOJI] [EMOJI]
            if not user.get("is_active", True):
                logger.warning(f"Inactive user attempted login: {email}")
                return None

            # [EMOJI] [EMOJI]
            if not PasswordHasher.verify_password(password, user["password_hash"]):
                logger.warning(f"Invalid password for user: {email}")
                return None

            logger.info(f"User authenticated: {email}")

            # [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
            user_data = user.copy()
            del user_data["password_hash"]
            return user_data

        except Exception as e:
            # MED-04: Sanitize exception before logging
            logger.error(f"Authentication error: {sanitize_exception(e)}")
            return None

    async def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """
        [EMOJI] [EMOJI] [EMOJI]

        Args:
            email: [EMOJI] [EMOJI]

        Returns:
            [EMOJI] [EMOJI] [EMOJI] None
        """
        try:
            user = self.users.get(email.lower())
            if not user:
                return None

            # [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
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
        [EMOJI] [EMOJI] [EMOJI]

        Args:
            email: [EMOJI] [EMOJI]
            update_data: [EMOJI] [EMOJI]

        Returns:
            [EMOJI] [EMOJI] [EMOJI] [EMOJI] None
        """
        try:
            user = self.users.get(email.lower())
            if not user:
                return None

            # [EMOJI] [EMOJI] [EMOJI] [EMOJI]
            allowed_fields = ["full_name", "is_active", "role"]
            for field in allowed_fields:
                if field in update_data:
                    user[field] = update_data[field]

            # [EMOJI] [EMOJI] [EMOJI]
            if "password" in update_data:
                user["password_hash"] = PasswordHasher.hash_password(
                    update_data["password"]
                )

            # [EMOJI] [EMOJI] [EMOJI]
            user["updated_at"] = datetime.now(UTC).isoformat()

            logger.info(f"User updated: {email}")

            # [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
            user_data = user.copy()
            del user_data["password_hash"]
            return user_data

        except Exception as e:
            # MED-04: Sanitize exception before logging
            logger.error(f"Failed to update user: {sanitize_exception(e)}")
            return None

    async def delete_user(self, email: str) -> bool:
        """
        [EMOJI] [EMOJI]

        Args:
            email: [EMOJI] [EMOJI]

        Returns:
            [EMOJI] [EMOJI] [EMOJI]
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
        [EMOJI] [EMOJI] [EMOJI]

        Args:
            limit: [EMOJI] [EMOJI]
            offset: [EMOJI] [EMOJI]

        Returns:
            [EMOJI] [EMOJI] [EMOJI]
        """
        try:
            # [EMOJI] [EMOJI] [EMOJI] ([EMOJI] [EMOJI] [EMOJI])
            all_users = []
            for user in self.users.values():
                user_data = user.copy()
                del user_data["password_hash"]
                all_users.append(user_data)

            # [EMOJI] ([EMOJI] [EMOJI] [EMOJI])
            all_users.sort(
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )

            # [EMOJI]
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
        """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
        return len(self.users)

    def clear_all_users(self):
        """[EMOJI] [EMOJI] [EMOJI] ([EMOJI])"""
        self.users.clear()
        self.user_id_counter = 1
        logger.warning("All users cleared!")


# Create singleton instance
auth_service = AuthService()

# Export
__all__ = ['AuthService', 'auth_service']