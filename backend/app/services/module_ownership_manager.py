"""
Module Ownership Manager for Standard Level MDO System

Standard [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
- [EMOJI] [EMOJI] [EMOJI] [EMOJI]
- [EMOJI] [EMOJI] [EMOJI]
- [EMOJI] [EMOJI]
- Standard [EMOJI] [EMOJI] [EMOJI]
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum
from dataclasses import dataclass, asdict, field
import logging

from app.services.redis_client import get_redis_client, RedisKeys
from app.services.session_manager_v2 import get_session_manager

logger = logging.getLogger(__name__)


class ModuleStatus(Enum):
    """[EMOJI] [EMOJI] [EMOJI]"""
    AVAILABLE = "available"        # [EMOJI] [EMOJI]
    PLANNING = "planning"          # [EMOJI] [EMOJI]
    CODING = "coding"             # [EMOJI] [EMOJI]
    TESTING = "testing"           # [EMOJI] [EMOJI]
    REVIEW = "review"             # [EMOJI] [EMOJI]
    COMPLETED = "completed"       # [EMOJI]
    BLOCKED = "blocked"           # [EMOJI]


class CompletionCriteria(Enum):
    """Standard [EMOJI] [EMOJI] [EMOJI]"""
    COMMIT = "commit"             # [EMOJI] [EMOJI]
    PUSH = "push"                 # [EMOJI] [EMOJI]
    TESTS_PASS = "tests_pass"     # [EMOJI] [EMOJI]
    USER_CONFIRM = "user_confirm" # [EMOJI] [EMOJI]


@dataclass
class ModuleDefinition:
    """[EMOJI] [EMOJI]"""
    id: str                           # [EMOJI]: "auth/login"
    name: str                         # [EMOJI]
    description: str                  # [EMOJI]
    type: str                        # feature, bugfix, refactor
    dependencies: List[str]          # [EMOJI] [EMOJI]
    estimated_hours: float           # [EMOJI] [EMOJI]
    priority: str                    # high, medium, low
    files: List[str]                # [EMOJI] [EMOJI]
    test_files: List[str]           # [EMOJI] [EMOJI]


@dataclass
class ModuleOwnership:
    """[EMOJI] [EMOJI] [EMOJI]"""
    module_id: str
    owner_session: str
    developer_name: str
    status: ModuleStatus
    started_at: datetime
    estimated_completion: datetime
    actual_completion: Optional[datetime] = None
    completion_criteria: List[CompletionCriteria] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    progress: int = 0  # 0-100%
    commits: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data['status'] = self.status.value
        data['started_at'] = self.started_at.isoformat()
        data['estimated_completion'] = self.estimated_completion.isoformat()
        if self.actual_completion:
            data['actual_completion'] = self.actual_completion.isoformat()
        data['completion_criteria'] = [c.value for c in self.completion_criteria]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'ModuleOwnership':
        data['status'] = ModuleStatus(data['status'])
        data['started_at'] = datetime.fromisoformat(data['started_at'])
        data['estimated_completion'] = datetime.fromisoformat(data['estimated_completion'])
        if data.get('actual_completion'):
            data['actual_completion'] = datetime.fromisoformat(data['actual_completion'])
        data['completion_criteria'] = [
            CompletionCriteria(c) for c in data.get('completion_criteria', [])
        ]
        return cls(**data)


@dataclass
class ModuleAvailability:
    """[EMOJI] [EMOJI] [EMOJI]"""
    available: bool
    reason: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[ModuleStatus] = None
    estimated_available: Optional[datetime] = None
    alternatives: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    can_override: bool = False


class ModuleOwnershipManager:
    """
    Standard [EMOJI] [EMOJI] [EMOJI] [EMOJI]
    """

    def __init__(self):
        self.redis_client = None
        self.session_manager = None
        self.module_definitions: Dict[str, ModuleDefinition] = {}
        self.active_ownerships: Dict[str, ModuleOwnership] = {}
        self.completion_queue: List[str] = []
        self._initialized = False

    async def initialize(self):
        """[EMOJI]"""
        if self._initialized:
            return

        try:
            self.redis_client = await get_redis_client()
            self.session_manager = await get_session_manager()

            # [EMOJI] [EMOJI] [EMOJI]
            await self._load_module_definitions()

            # [EMOJI] [EMOJI] [EMOJI]
            await self._recover_active_ownerships()

            self._initialized = True
            logger.info("[OK] ModuleOwnershipManager initialized (Standard Level)")

        except Exception as e:
            logger.error(f"Failed to initialize ModuleOwnershipManager: {e}")
            raise

    async def _load_module_definitions(self):
        """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
        # [EMOJI] [EMOJI] [EMOJI] DB[EMOJI] [EMOJI]
        # [EMOJI] [EMOJI] [EMOJI]

        self.module_definitions = {
            "auth/login": ModuleDefinition(
                id="auth/login",
                name="[EMOJI] [EMOJI]",
                description="[EMOJI] [EMOJI] [EMOJI] [EMOJI]",
                type="feature",
                dependencies=[],
                estimated_hours=4,
                priority="high",
                files=["backend/auth/login.py", "backend/auth/validators.py"],
                test_files=["tests/auth/test_login.py"]
            ),
            "auth/register": ModuleDefinition(
                id="auth/register",
                name="[EMOJI] [EMOJI]",
                description="[EMOJI] [EMOJI] [EMOJI]",
                type="feature",
                dependencies=["auth/validators"],
                estimated_hours=6,
                priority="high",
                files=["backend/auth/register.py", "backend/auth/validators.py"],
                test_files=["tests/auth/test_register.py"]
            ),
            "payment/checkout": ModuleDefinition(
                id="payment/checkout",
                name="[EMOJI] [EMOJI]",
                description="[EMOJI] [EMOJI]",
                type="feature",
                dependencies=["auth/login", "cart/calculate"],
                estimated_hours=8,
                priority="medium",
                files=["backend/payment/checkout.py", "backend/payment/gateway.py"],
                test_files=["tests/payment/test_checkout.py"]
            )
        }

        logger.info(f"[EMOJI] Loaded {len(self.module_definitions)} module definitions")

    async def _recover_active_ownerships(self):
        """Redis[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
        if not self.redis_client:
            return

        try:
            # Redis[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
            pattern = "udo:module:ownership:*"
            keys = await self.redis_client._client.keys(pattern)

            for key in keys:
                data = await self.redis_client._client.get(key)
                if data:
                    ownership = ModuleOwnership.from_dict(json.loads(data))
                    self.active_ownerships[ownership.module_id] = ownership

            logger.info(f"[EMOJI] Recovered {len(self.active_ownerships)} active ownerships")

        except Exception as e:
            logger.error(f"Failed to recover ownerships: {e}")

    async def check_module_availability(
        self,
        module_id: str,
        session_id: str,
        developer_name: str
    ) -> ModuleAvailability:
        """
        [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] (Standard [EMOJI])
        """

        # 1. [EMOJI] [EMOJI] [EMOJI]
        if module_id not in self.module_definitions:
            return ModuleAvailability(
                available=False,
                reason=f"[EMOJI] '{module_id}'[EMOJI] [EMOJI] [EMOJI]"
            )

        module_def = self.module_definitions[module_id]

        # 2. [EMOJI] [EMOJI] [EMOJI]
        if module_id in self.active_ownerships:
            ownership = self.active_ownerships[module_id]

            if ownership.owner_session == session_id:
                # [EMOJI] [EMOJI] [EMOJI]
                return ModuleAvailability(
                    available=True,
                    reason="[EMOJI] [EMOJI] [EMOJI] [EMOJI]",
                    warnings=["[EMOJI] [EMOJI] [EMOJI]"]
                )

            # [EMOJI] [EMOJI] [EMOJI] [EMOJI]
            return ModuleAvailability(
                available=False,
                reason=f"{ownership.developer_name}[EMOJI] [EMOJI] [EMOJI]",
                owner=ownership.developer_name,
                status=ownership.status,
                estimated_available=ownership.estimated_completion,
                alternatives=await self._suggest_alternatives(module_id),
                can_override=False  # Standard [EMOJI] override [EMOJI]
            )

        # 3. [EMOJI] [EMOJI]
        blocked_by = []
        for dep_module_id in module_def.dependencies:
            if dep_module_id in self.active_ownerships:
                dep_ownership = self.active_ownerships[dep_module_id]
                if dep_ownership.status not in [ModuleStatus.COMPLETED, ModuleStatus.TESTING]:
                    blocked_by.append(f"{dep_module_id} ({dep_ownership.developer_name})")

        if blocked_by:
            return ModuleAvailability(
                available=False,
                reason="[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]",
                warnings=[f"[EMOJI] [EMOJI]: {', '.join(blocked_by)}"],
                estimated_available=await self._estimate_availability(module_id)
            )

        # 4. [EMOJI] [EMOJI] (Standard [EMOJI] [EMOJI], [EMOJI] [EMOJI])
        warnings = []

        # [EMOJI] [EMOJI] [EMOJI]
        for file_path in module_def.files:
            if await self._is_file_being_edited(file_path):
                warnings.append(f"[EMOJI] '{file_path}'[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]")

        # [EMOJI] [EMOJI]
        if datetime.now().hour >= 22 or datetime.now().hour <= 6:
            warnings.append("[EMOJI] [EMOJI] [EMOJI] - [EMOJI] [EMOJI] [EMOJI]")

        # 5. [EMOJI] [EMOJI]
        return ModuleAvailability(
            available=True,
            warnings=warnings,
            alternatives=await self._suggest_alternatives(module_id)
        )

    async def claim_module(
        self,
        module_id: str,
        session_id: str,
        developer_name: str,
        estimated_hours: Optional[float] = None
    ) -> Tuple[bool, ModuleOwnership]:
        """
        [EMOJI] [EMOJI] (Standard [EMOJI])
        """

        # [EMOJI] [EMOJI]
        availability = await self.check_module_availability(
            module_id, session_id, developer_name
        )

        if not availability.available:
            raise ValueError(f"[EMOJI] [EMOJI] [EMOJI]: {availability.reason}")

        # [EMOJI] [EMOJI] [EMOJI]
        module_def = self.module_definitions[module_id]
        hours = estimated_hours or module_def.estimated_hours

        # [EMOJI] [EMOJI]
        ownership = ModuleOwnership(
            module_id=module_id,
            owner_session=session_id,
            developer_name=developer_name,
            status=ModuleStatus.PLANNING,
            started_at=datetime.now(),
            estimated_completion=datetime.now() + timedelta(hours=hours),
            completion_criteria=[
                CompletionCriteria.COMMIT,
                CompletionCriteria.TESTS_PASS,
                CompletionCriteria.PUSH
            ],
            warnings=availability.warnings
        )

        # Redis[EMOJI] [EMOJI]
        if self.redis_client:
            key = f"udo:module:ownership:{module_id}"
            await self.redis_client._client.set(
                key,
                json.dumps(ownership.to_dict()),
                ex=int(hours * 3600 * 2)  # [EMOJI] [EMOJI] 2[EMOJI] TTL [EMOJI]
            )

            # [EMOJI] [EMOJI]
            await self.redis_client.publish(
                "udo:channel:module",
                {
                    "type": "module_claimed",
                    "module_id": module_id,
                    "developer": developer_name,
                    "estimated_completion": ownership.estimated_completion.isoformat()
                }
            )

        # [EMOJI] [EMOJI]
        self.active_ownerships[module_id] = ownership

        # [EMOJI] [EMOJI] [EMOJI] (Standard [EMOJI] [EMOJI], [EMOJI] [EMOJI] [EMOJI])
        for file_path in module_def.files:
            logger.info(f"[EMOJI] File '{file_path}' associated with module '{module_id}'")

        logger.info(
            f"[OK] Module '{module_id}' claimed by {developer_name} "
            f"(until {ownership.estimated_completion.strftime('%H:%M')})"
        )

        return True, ownership

    async def update_module_status(
        self,
        module_id: str,
        session_id: str,
        new_status: ModuleStatus,
        progress: Optional[int] = None,
        commit_hash: Optional[str] = None
    ) -> bool:
        """
        [EMOJI] [EMOJI] [EMOJI]
        """

        if module_id not in self.active_ownerships:
            return False

        ownership = self.active_ownerships[module_id]

        # [EMOJI] [EMOJI]
        if ownership.owner_session != session_id:
            raise ValueError("[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]")

        # [EMOJI] [EMOJI]
        ownership.status = new_status

        if progress is not None:
            ownership.progress = min(100, max(0, progress))

        if commit_hash:
            ownership.commits.append(commit_hash)

        # [EMOJI] [EMOJI] [EMOJI]
        if not progress:
            status_progress = {
                ModuleStatus.PLANNING: 10,
                ModuleStatus.CODING: 50,
                ModuleStatus.TESTING: 70,
                ModuleStatus.REVIEW: 90,
                ModuleStatus.COMPLETED: 100
            }
            ownership.progress = status_progress.get(new_status, ownership.progress)

        # Redis [EMOJI]
        if self.redis_client:
            key = f"udo:module:ownership:{module_id}"
            await self.redis_client._client.set(
                key,
                json.dumps(ownership.to_dict())
            )

            # [EMOJI] [EMOJI] [EMOJI]
            await self.redis_client.publish(
                "udo:channel:module",
                {
                    "type": "module_status_changed",
                    "module_id": module_id,
                    "new_status": new_status.value,
                    "progress": ownership.progress,
                    "developer": ownership.developer_name
                }
            )

        # [EMOJI] [EMOJI]
        if new_status == ModuleStatus.COMPLETED:
            await self._complete_module(module_id)

        logger.info(
            f"[EMOJI] Module '{module_id}' status: {new_status.value} ({ownership.progress}%)"
        )

        return True

    async def release_module(
        self,
        module_id: str,
        session_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        [EMOJI] [EMOJI] [EMOJI]
        """

        if module_id not in self.active_ownerships:
            return False

        ownership = self.active_ownerships[module_id]

        # [EMOJI] [EMOJI]
        if ownership.owner_session != session_id:
            raise ValueError("[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]")

        # Redis[EMOJI] [EMOJI]
        if self.redis_client:
            key = f"udo:module:ownership:{module_id}"
            await self.redis_client._client.delete(key)

            # [EMOJI] [EMOJI]
            await self.redis_client.publish(
                "udo:channel:module",
                {
                    "type": "module_released",
                    "module_id": module_id,
                    "developer": ownership.developer_name,
                    "reason": reason or "manual release"
                }
            )

        # [EMOJI] [EMOJI]
        del self.active_ownerships[module_id]

        # [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        await self._notify_waiting_developers(module_id)

        logger.info(f"[EMOJI] Module '{module_id}' released by {ownership.developer_name}")

        return True

    async def _complete_module(self, module_id: str):
        """
        [EMOJI] [EMOJI] [EMOJI]
        """

        ownership = self.active_ownerships.get(module_id)
        if not ownership:
            return

        ownership.actual_completion = datetime.now()
        ownership.status = ModuleStatus.COMPLETED
        ownership.progress = 100

        # [EMOJI] [EMOJI] [EMOJI]
        self.completion_queue.append(module_id)

        # [EMOJI] [EMOJI] [EMOJI]
        for other_module_id, other_def in self.module_definitions.items():
            if module_id in other_def.dependencies:
                await self._notify_module_available(other_module_id, module_id)

        logger.info(f"[EMOJI] Module '{module_id}' completed!")

    async def _suggest_alternatives(self, module_id: str) -> List[str]:
        """
        [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        """

        alternatives = []
        module_def = self.module_definitions.get(module_id)

        if not module_def:
            return alternatives

        # [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        for other_id, other_def in self.module_definitions.items():
            if other_id != module_id and other_id not in self.active_ownerships:
                if other_def.type == module_def.type:
                    # [EMOJI] [EMOJI]
                    deps_available = all(
                        dep not in self.active_ownerships or
                        self.active_ownerships[dep].status == ModuleStatus.COMPLETED
                        for dep in other_def.dependencies
                    )

                    if deps_available:
                        alternatives.append(other_id)

        return alternatives[:3]  # [EMOJI] 3[EMOJI] [EMOJI]

    async def _estimate_availability(self, module_id: str) -> Optional[datetime]:
        """
        [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        """

        # [EMOJI] [EMOJI]
        module_def = self.module_definitions.get(module_id)
        if not module_def:
            return None

        latest_completion = datetime.now()

        for dep_module_id in module_def.dependencies:
            if dep_module_id in self.active_ownerships:
                dep_ownership = self.active_ownerships[dep_module_id]
                if dep_ownership.estimated_completion > latest_completion:
                    latest_completion = dep_ownership.estimated_completion

        return latest_completion

    async def _is_file_being_edited(self, file_path: str) -> bool:
        """
        [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        """

        # SessionManager[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        if self.session_manager:
            # [EMOJI] [EMOJI] ([EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI])
            return False

        return False

    async def _notify_waiting_developers(self, module_id: str):
        """
        [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        """

        if self.redis_client:
            await self.redis_client.publish(
                "udo:channel:module",
                {
                    "type": "module_available",
                    "module_id": module_id,
                    "message": f"[EMOJI] '{module_id}'[EMOJI]([EMOJI]) [EMOJI] [EMOJI] [EMOJI] [EMOJI]!"
                }
            )

    async def _notify_module_available(self, module_id: str, completed_dependency: str):
        """
        [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        """

        if self.redis_client:
            await self.redis_client.publish(
                "udo:channel:module",
                {
                    "type": "dependency_completed",
                    "module_id": module_id,
                    "completed": completed_dependency,
                    "message": f"'{completed_dependency}' [EMOJI] '{module_id}' [EMOJI] [EMOJI]"
                }
            )

    async def get_module_status_board(self) -> Dict[str, Any]:
        """
        [EMOJI] [EMOJI] [EMOJI]
        """

        board = {
            "active": [],
            "available": [],
            "blocked": [],
            "completed": []
        }

        for module_id, module_def in self.module_definitions.items():
            if module_id in self.active_ownerships:
                ownership = self.active_ownerships[module_id]
                board["active"].append({
                    "module_id": module_id,
                    "name": module_def.name,
                    "developer": ownership.developer_name,
                    "status": ownership.status.value,
                    "progress": ownership.progress,
                    "estimated_completion": ownership.estimated_completion.isoformat()
                })

            elif module_id in self.completion_queue:
                board["completed"].append({
                    "module_id": module_id,
                    "name": module_def.name
                })

            else:
                # [EMOJI] [EMOJI]
                deps_blocked = any(
                    dep in self.active_ownerships and
                    self.active_ownerships[dep].status != ModuleStatus.COMPLETED
                    for dep in module_def.dependencies
                )

                if deps_blocked:
                    board["blocked"].append({
                        "module_id": module_id,
                        "name": module_def.name,
                        "blocked_by": module_def.dependencies
                    })
                else:
                    board["available"].append({
                        "module_id": module_id,
                        "name": module_def.name,
                        "type": module_def.type,
                        "priority": module_def.priority,
                        "estimated_hours": module_def.estimated_hours
                    })

        return board

    async def check_standard_rules(self, action: str, context: Dict) -> Tuple[bool, List[str]]:
        """
        Standard [EMOJI] [EMOJI] [EMOJI]

        Returns:
            (allowed, warnings)
        """

        warnings = []

        if action == "push_without_test":
            # Standard [EMOJI]: [EMOJI] [EMOJI] [EMOJI] [EMOJI]
            return False, ["Standard [EMOJI]: [EMOJI] [EMOJI] [EMOJI] [EMOJI]"]

        elif action == "claim_without_branch":
            # Standard [EMOJI]: [EMOJI] [EMOJI] [EMOJI] [EMOJI]
            branch_name = context.get("branch")
            module_id = context.get("module_id")

            if branch_name and module_id:
                expected = f"feature/{module_id.replace('/', '-')}"
                if not branch_name.startswith(expected):
                    warnings.append(f"[EMOJI] [EMOJI] [EMOJI]: {expected}[EMOJI] [EMOJI]")

        elif action == "long_hold":
            # Standard [EMOJI]: [EMOJI] [EMOJI] [EMOJI]
            hold_hours = context.get("hours", 0)
            if hold_hours > 8:
                warnings.append(f"[EMOJI] {hold_hours}[EMOJI] [EMOJI] [EMOJI] - [EMOJI] [EMOJI] [EMOJI] [EMOJI]")

        return True, warnings


# Singleton
_module_manager: Optional[ModuleOwnershipManager] = None


async def get_module_manager() -> ModuleOwnershipManager:
    """Get or create ModuleOwnershipManager singleton"""
    global _module_manager

    if _module_manager is None:
        _module_manager = ModuleOwnershipManager()
        await _module_manager.initialize()

    return _module_manager