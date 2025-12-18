"""
Module Ownership Manager for Standard Level MDO System

Standard 레벨 모듈 개발 조정 시스템
- 모듈 단위 점유 관리
- 개발 상태 추적
- 의존성 체크
- Standard 레벨 규칙 강제
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
    """모듈 개발 상태"""
    AVAILABLE = "available"        # 개발 가능
    PLANNING = "planning"          # 계획 중
    CODING = "coding"             # 코딩 중
    TESTING = "testing"           # 테스트 중
    REVIEW = "review"             # 리뷰 중
    COMPLETED = "completed"       # 완료
    BLOCKED = "blocked"           # 차단됨


class CompletionCriteria(Enum):
    """Standard 레벨 완료 기준"""
    COMMIT = "commit"             # 커밋 완료
    PUSH = "push"                 # 푸시 완료
    TESTS_PASS = "tests_pass"     # 테스트 통과
    USER_CONFIRM = "user_confirm" # 사용자 확인


@dataclass
class ModuleDefinition:
    """모듈 정의"""
    id: str                           # 예: "auth/login"
    name: str                         # 표시명
    description: str                  # 설명
    type: str                        # feature, bugfix, refactor
    dependencies: List[str]          # 의존 모듈들
    estimated_hours: float           # 예상 시간
    priority: str                    # high, medium, low
    files: List[str]                # 관련 파일들
    test_files: List[str]           # 테스트 파일들


@dataclass
class ModuleOwnership:
    """모듈 점유 정보"""
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
    """모듈 가용성 정보"""
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
    Standard 레벨 모듈 점유 관리자
    """

    def __init__(self):
        self.redis_client = None
        self.session_manager = None
        self.module_definitions: Dict[str, ModuleDefinition] = {}
        self.active_ownerships: Dict[str, ModuleOwnership] = {}
        self.completion_queue: List[str] = []
        self._initialized = False

    async def initialize(self):
        """초기화"""
        if self._initialized:
            return

        try:
            self.redis_client = await get_redis_client()
            self.session_manager = await get_session_manager()

            # 모듈 정의 로드
            await self._load_module_definitions()

            # 활성 점유 복구
            await self._recover_active_ownerships()

            self._initialized = True
            logger.info("✅ ModuleOwnershipManager initialized (Standard Level)")

        except Exception as e:
            logger.error(f"Failed to initialize ModuleOwnershipManager: {e}")
            raise

    async def _load_module_definitions(self):
        """프로젝트 모듈 정의 로드"""
        # 실제로는 설정 파일이나 DB에서 로드
        # 여기서는 예시로 하드코딩

        self.module_definitions = {
            "auth/login": ModuleDefinition(
                id="auth/login",
                name="로그인 기능",
                description="사용자 인증 및 로그인",
                type="feature",
                dependencies=[],
                estimated_hours=4,
                priority="high",
                files=["backend/auth/login.py", "backend/auth/validators.py"],
                test_files=["tests/auth/test_login.py"]
            ),
            "auth/register": ModuleDefinition(
                id="auth/register",
                name="회원가입 기능",
                description="신규 사용자 등록",
                type="feature",
                dependencies=["auth/validators"],
                estimated_hours=6,
                priority="high",
                files=["backend/auth/register.py", "backend/auth/validators.py"],
                test_files=["tests/auth/test_register.py"]
            ),
            "payment/checkout": ModuleDefinition(
                id="payment/checkout",
                name="결제 처리",
                description="결제 프로세스",
                type="feature",
                dependencies=["auth/login", "cart/calculate"],
                estimated_hours=8,
                priority="medium",
                files=["backend/payment/checkout.py", "backend/payment/gateway.py"],
                test_files=["tests/payment/test_checkout.py"]
            )
        }

        logger.info(f"📚 Loaded {len(self.module_definitions)} module definitions")

    async def _recover_active_ownerships(self):
        """Redis에서 활성 점유 복구"""
        if not self.redis_client:
            return

        try:
            # Redis에서 모든 점유 정보 가져오기
            pattern = "udo:module:ownership:*"
            keys = await self.redis_client._client.keys(pattern)

            for key in keys:
                data = await self.redis_client._client.get(key)
                if data:
                    ownership = ModuleOwnership.from_dict(json.loads(data))
                    self.active_ownerships[ownership.module_id] = ownership

            logger.info(f"🔄 Recovered {len(self.active_ownerships)} active ownerships")

        except Exception as e:
            logger.error(f"Failed to recover ownerships: {e}")

    async def check_module_availability(
        self,
        module_id: str,
        session_id: str,
        developer_name: str
    ) -> ModuleAvailability:
        """
        모듈 개발 가능 여부 체크 (Standard 레벨)
        """

        # 1. 모듈 정의 확인
        if module_id not in self.module_definitions:
            return ModuleAvailability(
                available=False,
                reason=f"모듈 '{module_id}'이 정의되지 않음"
            )

        module_def = self.module_definitions[module_id]

        # 2. 현재 점유 확인
        if module_id in self.active_ownerships:
            ownership = self.active_ownerships[module_id]

            if ownership.owner_session == session_id:
                # 이미 본인이 점유
                return ModuleAvailability(
                    available=True,
                    reason="이미 점유 중인 모듈",
                    warnings=["중복 점유 요청"]
                )

            # 다른 사람이 점유 중
            return ModuleAvailability(
                available=False,
                reason=f"{ownership.developer_name}님이 개발 중",
                owner=ownership.developer_name,
                status=ownership.status,
                estimated_available=ownership.estimated_completion,
                alternatives=await self._suggest_alternatives(module_id),
                can_override=False  # Standard 레벨은 override 불가
            )

        # 3. 의존성 체크
        blocked_by = []
        for dep_module_id in module_def.dependencies:
            if dep_module_id in self.active_ownerships:
                dep_ownership = self.active_ownerships[dep_module_id]
                if dep_ownership.status not in [ModuleStatus.COMPLETED, ModuleStatus.TESTING]:
                    blocked_by.append(f"{dep_module_id} ({dep_ownership.developer_name})")

        if blocked_by:
            return ModuleAvailability(
                available=False,
                reason="의존 모듈이 아직 개발 중",
                warnings=[f"대기 중: {', '.join(blocked_by)}"],
                estimated_available=await self._estimate_availability(module_id)
            )

        # 4. 경고 체크 (Standard 레벨은 경고만, 차단 안함)
        warnings = []

        # 관련 파일 체크
        for file_path in module_def.files:
            if await self._is_file_being_edited(file_path):
                warnings.append(f"파일 '{file_path}'이 수정 중일 수 있음")

        # 시간대 체크
        if datetime.now().hour >= 22 or datetime.now().hour <= 6:
            warnings.append("늦은 시간 작업 - 충분한 테스트 권장")

        # 5. 개발 가능
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
        모듈 점유 (Standard 레벨)
        """

        # 가용성 체크
        availability = await self.check_module_availability(
            module_id, session_id, developer_name
        )

        if not availability.available:
            raise ValueError(f"모듈 점유 불가: {availability.reason}")

        # 예상 시간 설정
        module_def = self.module_definitions[module_id]
        hours = estimated_hours or module_def.estimated_hours

        # 점유 생성
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

        # Redis에 저장
        if self.redis_client:
            key = f"udo:module:ownership:{module_id}"
            await self.redis_client._client.set(
                key,
                json.dumps(ownership.to_dict()),
                ex=int(hours * 3600 * 2)  # 예상 시간의 2배로 TTL 설정
            )

            # 이벤트 브로드캐스트
            await self.redis_client.publish(
                "udo:channel:module",
                {
                    "type": "module_claimed",
                    "module_id": module_id,
                    "developer": developer_name,
                    "estimated_completion": ownership.estimated_completion.isoformat()
                }
            )

        # 로컬 저장
        self.active_ownerships[module_id] = ownership

        # 파일 락 획득 (Standard 레벨은 경고만, 강제 락은 안함)
        for file_path in module_def.files:
            logger.info(f"📝 File '{file_path}' associated with module '{module_id}'")

        logger.info(
            f"✅ Module '{module_id}' claimed by {developer_name} "
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
        모듈 상태 업데이트
        """

        if module_id not in self.active_ownerships:
            return False

        ownership = self.active_ownerships[module_id]

        # 권한 체크
        if ownership.owner_session != session_id:
            raise ValueError("다른 사람의 모듈은 수정할 수 없습니다")

        # 상태 업데이트
        ownership.status = new_status

        if progress is not None:
            ownership.progress = min(100, max(0, progress))

        if commit_hash:
            ownership.commits.append(commit_hash)

        # 자동 진행률 계산
        if not progress:
            status_progress = {
                ModuleStatus.PLANNING: 10,
                ModuleStatus.CODING: 50,
                ModuleStatus.TESTING: 70,
                ModuleStatus.REVIEW: 90,
                ModuleStatus.COMPLETED: 100
            }
            ownership.progress = status_progress.get(new_status, ownership.progress)

        # Redis 업데이트
        if self.redis_client:
            key = f"udo:module:ownership:{module_id}"
            await self.redis_client._client.set(
                key,
                json.dumps(ownership.to_dict())
            )

            # 상태 변경 이벤트
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

        # 완료 처리
        if new_status == ModuleStatus.COMPLETED:
            await self._complete_module(module_id)

        logger.info(
            f"📊 Module '{module_id}' status: {new_status.value} ({ownership.progress}%)"
        )

        return True

    async def release_module(
        self,
        module_id: str,
        session_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        모듈 점유 해제
        """

        if module_id not in self.active_ownerships:
            return False

        ownership = self.active_ownerships[module_id]

        # 권한 체크
        if ownership.owner_session != session_id:
            raise ValueError("다른 사람의 모듈은 해제할 수 없습니다")

        # Redis에서 삭제
        if self.redis_client:
            key = f"udo:module:ownership:{module_id}"
            await self.redis_client._client.delete(key)

            # 해제 이벤트
            await self.redis_client.publish(
                "udo:channel:module",
                {
                    "type": "module_released",
                    "module_id": module_id,
                    "developer": ownership.developer_name,
                    "reason": reason or "manual release"
                }
            )

        # 로컬에서 삭제
        del self.active_ownerships[module_id]

        # 대기 중인 개발자에게 알림
        await self._notify_waiting_developers(module_id)

        logger.info(f"🔓 Module '{module_id}' released by {ownership.developer_name}")

        return True

    async def _complete_module(self, module_id: str):
        """
        모듈 완료 처리
        """

        ownership = self.active_ownerships.get(module_id)
        if not ownership:
            return

        ownership.actual_completion = datetime.now()
        ownership.status = ModuleStatus.COMPLETED
        ownership.progress = 100

        # 완료 큐에 추가
        self.completion_queue.append(module_id)

        # 의존하는 모듈들 알림
        for other_module_id, other_def in self.module_definitions.items():
            if module_id in other_def.dependencies:
                await self._notify_module_available(other_module_id, module_id)

        logger.info(f"🎉 Module '{module_id}' completed!")

    async def _suggest_alternatives(self, module_id: str) -> List[str]:
        """
        대체 가능한 모듈 추천
        """

        alternatives = []
        module_def = self.module_definitions.get(module_id)

        if not module_def:
            return alternatives

        # 같은 타입의 다른 모듈들
        for other_id, other_def in self.module_definitions.items():
            if other_id != module_id and other_id not in self.active_ownerships:
                if other_def.type == module_def.type:
                    # 의존성 체크
                    deps_available = all(
                        dep not in self.active_ownerships or
                        self.active_ownerships[dep].status == ModuleStatus.COMPLETED
                        for dep in other_def.dependencies
                    )

                    if deps_available:
                        alternatives.append(other_id)

        return alternatives[:3]  # 최대 3개 추천

    async def _estimate_availability(self, module_id: str) -> Optional[datetime]:
        """
        모듈 가용 시간 예측
        """

        # 의존성 체크
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
        파일이 수정 중인지 체크
        """

        # SessionManager와 연동하여 파일 락 체크
        if self.session_manager:
            # 간단히 구현 (실제로는 더 복잡할 수 있음)
            return False

        return False

    async def _notify_waiting_developers(self, module_id: str):
        """
        대기 중인 개발자들에게 알림
        """

        if self.redis_client:
            await self.redis_client.publish(
                "udo:channel:module",
                {
                    "type": "module_available",
                    "module_id": module_id,
                    "message": f"모듈 '{module_id}'을(를) 이제 개발할 수 있습니다!"
                }
            )

    async def _notify_module_available(self, module_id: str, completed_dependency: str):
        """
        의존성 완료로 인한 모듈 가용 알림
        """

        if self.redis_client:
            await self.redis_client.publish(
                "udo:channel:module",
                {
                    "type": "dependency_completed",
                    "module_id": module_id,
                    "completed": completed_dependency,
                    "message": f"'{completed_dependency}' 완료로 '{module_id}' 개발 가능"
                }
            )

    async def get_module_status_board(self) -> Dict[str, Any]:
        """
        모듈 현황판 데이터
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
                # 가용성 체크
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
        Standard 레벨 규칙 체크

        Returns:
            (allowed, warnings)
        """

        warnings = []

        if action == "push_without_test":
            # Standard 레벨: 테스트 없이 푸시 차단
            return False, ["Standard 레벨: 테스트 없이 푸시 불가"]

        elif action == "claim_without_branch":
            # Standard 레벨: 브랜치 규칙 위반 경고만
            branch_name = context.get("branch")
            module_id = context.get("module_id")

            if branch_name and module_id:
                expected = f"feature/{module_id.replace('/', '-')}"
                if not branch_name.startswith(expected):
                    warnings.append(f"브랜치 명명 규칙: {expected}를 권장")

        elif action == "long_hold":
            # Standard 레벨: 장시간 점유 경고
            hold_hours = context.get("hours", 0)
            if hold_hours > 8:
                warnings.append(f"모듈을 {hold_hours}시간 점유 중 - 진행 상황 공유 권장")

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