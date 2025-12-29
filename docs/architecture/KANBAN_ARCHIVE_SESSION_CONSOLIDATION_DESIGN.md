# Obsidian Sync v2 Architecture Design

## Session-Based Summaries with Test/Production Isolation

**Status**: Design Document
**Author**: System Architect (Claude Code)
**Date**: 2025-12-28
**Priority**: P1 - Architecture Improvement

---

## 1. Problem Statement

### Current Issues

1. **Per-Task File Creation**: Each archived task creates an individual `.md` file
   - Location: `kanban_archive_service.py:384-410`
   - Pattern: `{date}/{date}_{time}_{task_title}.md`

2. **Test Data Pollution**: Test runs create 8+ mock files per run
   - Mock tasks: `ideation-task.md`, `design-task.md`, `implementation-task.md`, etc.
   - No distinction between test and production data
   - Files persist in Obsidian vault

3. **File Explosion**:
   - 30+ test runs/day = 240+ files/day
   - 95% of files are noise (mock data)
   - Obsidian vault becomes unsearchable

4. **No Session Context**:
   - Files lack session correlation
   - No way to reconstruct "what was done in a session"
   - Lost productivity context

### Impact Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Files per day | 200+ | 1-5 |
| Noise ratio | 95% | 0% |
| Session traceability | None | Full |
| Test isolation | None | Complete |

---

## 2. Proposed Architecture

### 2.1 Core Design Principles

1. **Session-Based Consolidation**: One summary file per development session
2. **Environment Isolation**: Test mode never writes to production vault
3. **Meaningful Naming**: Files describe actual work, not individual tasks
4. **Daily Rollup**: End-of-day summary consolidates all sessions
5. **Immutable History**: Append-only pattern prevents data loss

### 2.2 Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Obsidian Sync v2 Architecture                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐     ┌──────────────────────────────────┐  │
│  │   Environment    │     │      SessionAwareArchiver        │  │
│  │    Detector      │────▶│  (production/test/ci isolation)  │  │
│  └──────────────────┘     └──────────────────────────────────┘  │
│                                        │                         │
│           ┌────────────────────────────┼─────────────────────┐  │
│           │                            │                     │  │
│           ▼                            ▼                     ▼  │
│  ┌────────────────┐       ┌────────────────┐     ┌───────────┐  │
│  │  Test Buffer   │       │Session Aggregator│   │  Null     │  │
│  │  (in-memory)   │       │  (production)    │   │  Sink     │  │
│  │                │       │                  │   │   (CI)    │  │
│  └────────────────┘       └────────────────┘     └───────────┘  │
│                                    │                             │
│                                    ▼                             │
│                          ┌─────────────────┐                    │
│                          │ Session Summary │                    │
│                          │    Generator    │                    │
│                          └────────┬────────┘                    │
│                                   │                              │
│           ┌───────────────────────┼───────────────────────┐     │
│           │                       │                       │     │
│           ▼                       ▼                       ▼     │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐ │
│  │ Session Note   │    │  Daily Rollup  │    │    MOC/Index   │ │
│  │ (1 per session)│    │ (1 per day)    │    │   (updated)    │ │
│  └────────────────┘    └────────────────┘    └────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 File Structure (Production)

```
Obsidian Vault/
├── 개발일지/
│   ├── 2025-12-28/
│   │   ├── 2025-12-28_Session-Morning-Auth-Implementation.md    # Session note
│   │   ├── 2025-12-28_Session-Afternoon-API-Refactor.md          # Session note
│   │   └── 2025-12-28_Daily-Summary.md                           # Daily rollup
│   └── 2025-12-27/
│       ├── 2025-12-27_Session-Kanban-Feature.md
│       └── 2025-12-27_Daily-Summary.md
└── UDO/
    └── Sessions-MOC.md                                            # Session index
```

### 2.4 Test Mode Behavior

```python
# Test mode: NO files written to Obsidian
# All archive operations buffered in memory

TEST_BUFFER = []  # In-memory only

# After test completes:
# - Buffer is cleared
# - No files touched
# - Full functionality tested via buffer inspection
```

---

## 3. Implementation Details

### 3.1 Environment Detector

```python
# backend/app/core/environment.py

from enum import Enum
import os

class ExecutionEnvironment(Enum):
    """Execution environment classification."""
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TEST = "test"
    CI = "ci"


class EnvironmentDetector:
    """
    Detects current execution environment for sync routing.

    Priority order:
    1. Explicit ENVIRONMENT variable
    2. CI detection (GITHUB_ACTIONS, GITLAB_CI, etc.)
    3. Pytest detection (PYTEST_CURRENT_TEST)
    4. Default to development
    """

    CI_INDICATORS = [
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "CIRCLECI",
        "JENKINS_URL",
        "TRAVIS",
        "CI"
    ]

    @classmethod
    def detect(cls) -> ExecutionEnvironment:
        """Detect current execution environment."""

        # 1. Explicit override
        explicit = os.getenv("ENVIRONMENT", "").lower()
        if explicit in ("production", "prod"):
            return ExecutionEnvironment.PRODUCTION
        if explicit in ("test", "testing"):
            return ExecutionEnvironment.TEST
        if explicit == "ci":
            return ExecutionEnvironment.CI

        # 2. CI detection
        for indicator in cls.CI_INDICATORS:
            if os.getenv(indicator):
                return ExecutionEnvironment.CI

        # 3. Pytest detection
        if os.getenv("PYTEST_CURRENT_TEST"):
            return ExecutionEnvironment.TEST

        # 4. Default
        return ExecutionEnvironment.DEVELOPMENT

    @classmethod
    def is_test_mode(cls) -> bool:
        """Check if running in test or CI mode."""
        env = cls.detect()
        return env in (ExecutionEnvironment.TEST, ExecutionEnvironment.CI)

    @classmethod
    def should_write_obsidian(cls) -> bool:
        """Check if Obsidian writes should occur."""
        return cls.detect() == ExecutionEnvironment.PRODUCTION
```

### 3.2 Session-Aware Archive Service

```python
# backend/app/services/session_aware_archiver.py

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, List, Optional
from pathlib import Path

from app.core.environment import EnvironmentDetector, ExecutionEnvironment
from app.models.kanban_archive import ArchivedTaskWithMetrics, AISummary, ROIMetrics
from app.services.obsidian_service import ObsidianService

logger = logging.getLogger(__name__)


@dataclass
class SessionContext:
    """Context for a development session."""
    session_id: str
    started_at: datetime
    session_name: Optional[str] = None
    description: Optional[str] = None
    archived_tasks: List[ArchivedTaskWithMetrics] = field(default_factory=list)
    total_time_saved: float = 0.0
    total_estimated: float = 0.0
    total_actual: float = 0.0
    phases_touched: set = field(default_factory=set)

    def add_task(self, task: ArchivedTaskWithMetrics) -> None:
        """Add archived task to session context."""
        self.archived_tasks.append(task)
        self.phases_touched.add(task.phase_name)

        if task.roi_metrics:
            self.total_time_saved += task.roi_metrics.time_saved_hours
            self.total_estimated += task.roi_metrics.estimated_hours
            self.total_actual += task.roi_metrics.actual_hours

    def generate_session_name(self) -> str:
        """Generate descriptive session name from tasks."""
        if self.session_name:
            return self.session_name

        if not self.archived_tasks:
            return "Empty-Session"

        # Build name from phases and primary task
        phases_str = "-".join(sorted(self.phases_touched)[:2])
        primary_task = self.archived_tasks[0].title[:30]
        # Sanitize for filename
        primary_task = "".join(c if c.isalnum() or c in "-_ " else "" for c in primary_task)
        primary_task = primary_task.replace(" ", "-")

        return f"{phases_str}-{primary_task}"


class SessionAwareArchiver:
    """
    Session-aware archive service with environment isolation.

    Features:
    - Buffers tasks within a session
    - Generates consolidated session summaries
    - Complete test isolation (no file I/O in test mode)
    - Daily rollup generation
    - MOC/Index maintenance
    """

    def __init__(self, obsidian_service: Optional[ObsidianService] = None):
        self.environment = EnvironmentDetector.detect()
        self.obsidian_service = obsidian_service or ObsidianService()

        # Session management
        self._current_session: Optional[SessionContext] = None
        self._sessions_today: List[SessionContext] = []

        # Test mode buffer (never persisted)
        self._test_buffer: List[ArchivedTaskWithMetrics] = []

        logger.info(
            f"SessionAwareArchiver initialized in {self.environment.value} mode"
        )

    # =========================================================================
    # Session Lifecycle
    # =========================================================================

    def start_session(
        self,
        session_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Start a new development session.

        Returns:
            Session ID for tracking
        """
        session_id = str(uuid.uuid4())[:8]

        self._current_session = SessionContext(
            session_id=session_id,
            started_at=datetime.now(UTC),
            session_name=session_name,
            description=description
        )

        logger.info(f"Started session {session_id}: {session_name or 'unnamed'}")
        return session_id

    def end_session(self) -> Optional[str]:
        """
        End current session and generate summary.

        Returns:
            Path to session summary file (production) or None (test)
        """
        if not self._current_session:
            logger.warning("No active session to end")
            return None

        session = self._current_session
        self._current_session = None

        if not session.archived_tasks:
            logger.info(f"Session {session.session_id} ended with no tasks")
            return None

        # Store for daily rollup
        self._sessions_today.append(session)

        # Generate summary only in production
        if self.environment == ExecutionEnvironment.PRODUCTION:
            return self._write_session_summary(session)
        else:
            logger.debug(
                f"Session {session.session_id} buffered ({len(session.archived_tasks)} tasks)"
            )
            return None

    # =========================================================================
    # Task Archiving
    # =========================================================================

    def archive_task(self, task: ArchivedTaskWithMetrics) -> None:
        """
        Add archived task to current session.

        In test mode: buffers to memory only
        In production: adds to session for later summary
        """
        # Test mode: buffer only
        if EnvironmentDetector.is_test_mode():
            self._test_buffer.append(task)
            logger.debug(f"Test mode: buffered task {task.task_id}")
            return

        # Auto-start session if needed
        if not self._current_session:
            self.start_session(session_name="Auto-Session")

        self._current_session.add_task(task)
        logger.info(
            f"Added task '{task.title}' to session {self._current_session.session_id}"
        )

    # =========================================================================
    # Summary Generation
    # =========================================================================

    def _write_session_summary(self, session: SessionContext) -> str:
        """
        Write session summary to Obsidian vault.

        File pattern: YYYY-MM-DD_Session-{name}.md
        """
        if not self.obsidian_service.vault_available:
            logger.warning("Obsidian vault not available")
            return ""

        date_str = session.started_at.strftime("%Y-%m-%d")
        time_str = session.started_at.strftime("%H%M")
        session_name = session.generate_session_name()

        # Ensure date directory exists
        date_dir = self.obsidian_service.daily_notes_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"{date_str}_{time_str}_Session-{session_name}.md"
        filepath = date_dir / filename

        # Generate content
        content = self._generate_session_content(session)

        # Write file
        filepath.write_text(content, encoding="utf-8")

        logger.info(f"Wrote session summary: {filepath}")
        return str(filepath)

    def _generate_session_content(self, session: SessionContext) -> str:
        """Generate markdown content for session summary."""

        # Calculate metrics
        efficiency = (
            (session.total_estimated / session.total_actual * 100)
            if session.total_actual > 0 else 100.0
        )

        phases_list = sorted(session.phases_touched)

        # Build task table
        task_rows = []
        for task in session.archived_tasks:
            roi = task.roi_metrics
            eff = f"{roi.efficiency_percentage:.0f}%" if roi else "N/A"
            time_saved = f"{roi.time_saved_hours:+.1f}h" if roi else "N/A"
            task_rows.append(
                f"| {task.title[:40]} | {task.phase_name} | {eff} | {time_saved} |"
            )
        tasks_table = "\n".join(task_rows)

        # Key learnings aggregation
        all_learnings = []
        for task in session.archived_tasks:
            if task.ai_summary:
                all_learnings.extend(task.ai_summary.key_learnings)

        learnings_section = "\n".join(f"- {l}" for l in all_learnings[:5])

        content = f"""---
aliases:
  - Session {session.session_id}
tags:
  - type/session-summary
  - status/completed
  - kanban-archived
{chr(10).join(f"  - phase/{p}" for p in phases_list)}
created: {session.started_at.strftime("%Y-%m-%dT%H:%M:%S")}
session_id: {session.session_id}
task_count: {len(session.archived_tasks)}
total_estimated_hours: {session.total_estimated:.1f}
total_actual_hours: {session.total_actual:.1f}
time_saved_hours: {session.total_time_saved:.1f}
efficiency: {efficiency:.0f}
---

# Development Session: {session.generate_session_name()}

## Session Overview

**Session ID**: `{session.session_id}`
**Started**: {session.started_at.strftime("%Y-%m-%d %H:%M")}
**Tasks Completed**: {len(session.archived_tasks)}
**Phases**: {", ".join(phases_list)}

{session.description or ""}

## Metrics Summary

| Metric | Value |
|--------|-------|
| Tasks Completed | {len(session.archived_tasks)} |
| Total Estimated | {session.total_estimated:.1f}h |
| Total Actual | {session.total_actual:.1f}h |
| Time Saved | {session.total_time_saved:+.1f}h |
| Efficiency | {efficiency:.1f}% |

## Tasks Completed

| Task | Phase | Efficiency | Time Saved |
|------|-------|------------|------------|
{tasks_table}

## Key Learnings

{learnings_section if learnings_section else "No learnings extracted."}

## Related

- [[{session.started_at.strftime("%Y-%m-%d")}_Daily-Summary|Daily Summary]]
- [[Sessions-MOC|All Sessions]]

---

*Generated by UDO Platform - Session-Aware Archiver*
"""
        return content

    # =========================================================================
    # Daily Rollup
    # =========================================================================

    def generate_daily_rollup(self, date: Optional[str] = None) -> Optional[str]:
        """
        Generate consolidated daily summary from all sessions.

        Args:
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            Path to daily summary file
        """
        if EnvironmentDetector.is_test_mode():
            logger.debug("Skipping daily rollup in test mode")
            return None

        if not self.obsidian_service.vault_available:
            return None

        date_str = date or datetime.now(UTC).strftime("%Y-%m-%d")

        # Collect all sessions for the date
        sessions = [
            s for s in self._sessions_today
            if s.started_at.strftime("%Y-%m-%d") == date_str
        ]

        if not sessions:
            logger.info(f"No sessions for daily rollup on {date_str}")
            return None

        # Generate summary
        date_dir = self.obsidian_service.daily_notes_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)

        filepath = date_dir / f"{date_str}_Daily-Summary.md"
        content = self._generate_daily_content(date_str, sessions)

        filepath.write_text(content, encoding="utf-8")

        logger.info(f"Wrote daily rollup: {filepath}")
        return str(filepath)

    def _generate_daily_content(
        self,
        date_str: str,
        sessions: List[SessionContext]
    ) -> str:
        """Generate daily rollup content."""

        # Aggregate metrics
        total_tasks = sum(len(s.archived_tasks) for s in sessions)
        total_estimated = sum(s.total_estimated for s in sessions)
        total_actual = sum(s.total_actual for s in sessions)
        total_saved = sum(s.total_time_saved for s in sessions)

        efficiency = (total_estimated / total_actual * 100) if total_actual > 0 else 100.0

        # All phases touched
        all_phases = set()
        for s in sessions:
            all_phases.update(s.phases_touched)

        # Session links
        session_links = []
        for s in sessions:
            time_str = s.started_at.strftime("%H:%M")
            name = s.generate_session_name()
            session_links.append(
                f"- **{time_str}** - [[{date_str}_{s.started_at.strftime('%H%M')}_Session-{name}|{name}]] ({len(s.archived_tasks)} tasks)"
            )

        content = f"""---
aliases:
  - Daily Summary {date_str}
tags:
  - type/daily-summary
  - status/completed
{chr(10).join(f"  - phase/{p}" for p in sorted(all_phases))}
date: {date_str}
session_count: {len(sessions)}
task_count: {total_tasks}
total_hours: {total_actual:.1f}
efficiency: {efficiency:.0f}
---

# Daily Development Summary - {date_str}

## Overview

| Metric | Value |
|--------|-------|
| Sessions | {len(sessions)} |
| Tasks Completed | {total_tasks} |
| Total Estimated | {total_estimated:.1f}h |
| Total Actual | {total_actual:.1f}h |
| Time Saved | {total_saved:+.1f}h |
| Efficiency | {efficiency:.1f}% |

## Sessions

{chr(10).join(session_links)}

## Phase Breakdown

{chr(10).join(f"- **{p}**: {sum(1 for s in sessions for t in s.archived_tasks if t.phase_name == p)} tasks" for p in sorted(all_phases))}

## Productivity Insights

- Most productive phase: **{max(all_phases, key=lambda p: sum(1 for s in sessions for t in s.archived_tasks if t.phase_name == p))}**
- Average efficiency: **{efficiency:.1f}%**
- Total time saved: **{total_saved:+.1f}h**

---

*Generated by UDO Platform - Daily Rollup*
"""
        return content

    # =========================================================================
    # Test Mode Utilities
    # =========================================================================

    def get_test_buffer(self) -> List[ArchivedTaskWithMetrics]:
        """Get buffered tasks (test mode only)."""
        return self._test_buffer.copy()

    def clear_test_buffer(self) -> int:
        """Clear test buffer and return count of cleared items."""
        count = len(self._test_buffer)
        self._test_buffer.clear()
        return count

    def reset_for_testing(self) -> None:
        """Reset all state for test isolation."""
        self._test_buffer.clear()
        self._current_session = None
        self._sessions_today.clear()


# Singleton instance
session_aware_archiver = SessionAwareArchiver()
```

### 3.3 Configuration

```python
# backend/app/core/obsidian_config.py

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class ObsidianSyncConfig(BaseSettings):
    """Configuration for Obsidian sync behavior."""

    # Environment control
    environment: str = "development"
    enable_obsidian_sync: bool = True

    # Session settings
    auto_start_session: bool = True
    session_timeout_minutes: int = 120

    # File settings
    generate_daily_rollup: bool = True
    max_tasks_per_session: int = 50

    # Path overrides
    vault_path: Optional[Path] = None
    daily_notes_subdir: str = "개발일지"

    # Feature flags integration
    respect_feature_flags: bool = True

    class Config:
        env_prefix = "OBSIDIAN_"
        env_file = ".env"


obsidian_config = ObsidianSyncConfig()
```

### 3.4 Environment Variables

Add to `.env.example`:

```bash
# Obsidian Sync v2 Configuration
ENVIRONMENT=development  # development | test | ci | production

# Obsidian Settings
OBSIDIAN_ENABLE_OBSIDIAN_SYNC=true
OBSIDIAN_AUTO_START_SESSION=true
OBSIDIAN_SESSION_TIMEOUT_MINUTES=120
OBSIDIAN_GENERATE_DAILY_ROLLUP=true
OBSIDIAN_VAULT_PATH=  # Auto-detected if empty

# Feature Flags for Obsidian
FEATURE_KANBAN_OBSIDIAN_SYNC=false  # Explicit enable required
```

---

## 4. Migration Strategy

### 4.1 Phase 1: Side-by-Side (Week 1)

1. Deploy `SessionAwareArchiver` alongside existing service
2. Feature flag controls routing: `FEATURE_KANBAN_OBSIDIAN_SYNC`
3. Old service remains default, new service opt-in
4. Monitor for issues

### 4.2 Phase 2: Parallel Write (Week 2)

1. Enable parallel writing to both systems
2. Compare outputs for consistency
3. Validate session consolidation works correctly
4. User testing of new format

### 4.3 Phase 3: Cutover (Week 3)

1. Make `SessionAwareArchiver` default
2. Old service becomes fallback
3. Archive cleanup script for legacy files

### 4.4 Phase 4: Cleanup (Week 4)

1. Remove old per-task file generation
2. Optional: migrate existing files to session format
3. Document new structure

### 4.5 Cleanup Script for Existing Files

```python
# scripts/cleanup_obsidian_archive_files.py

"""
Cleanup script for legacy per-task Obsidian files.

Identifies and optionally archives mock/test files from Obsidian vault.
"""

import re
from pathlib import Path
from datetime import datetime
import shutil

MOCK_PATTERNS = [
    r"ideation-task",
    r"design-task",
    r"mvp-task",
    r"implementation-task",
    r"testing-task",
    r"Task\s*\d+",  # "Task 0", "Task 1", etc.
    r"Pending\s*task",
    r"Overestimated\s*task",
]


def identify_mock_files(vault_path: Path) -> list[Path]:
    """Find files that appear to be from test runs."""
    mock_files = []

    daily_notes = vault_path / "개발일지"
    if not daily_notes.exists():
        return mock_files

    for md_file in daily_notes.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")

        for pattern in MOCK_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                mock_files.append(md_file)
                break

    return mock_files


def archive_mock_files(files: list[Path], archive_dir: Path) -> int:
    """Move mock files to archive directory."""
    archive_dir.mkdir(parents=True, exist_ok=True)

    for f in files:
        dest = archive_dir / f.name
        shutil.move(str(f), str(dest))

    return len(files)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("vault_path", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--archive-dir", type=Path, default=Path(".obsidian-archive"))

    args = parser.parse_args()

    mock_files = identify_mock_files(args.vault_path)

    print(f"Found {len(mock_files)} mock/test files")

    if args.dry_run:
        for f in mock_files[:10]:
            print(f"  Would archive: {f}")
        if len(mock_files) > 10:
            print(f"  ... and {len(mock_files) - 10} more")
    else:
        archived = archive_mock_files(mock_files, args.archive_dir)
        print(f"Archived {archived} files to {args.archive_dir}")
```

---

## 5. Integration Points

### 5.1 KanbanArchiveService Integration

```python
# Modify backend/app/services/kanban_archive_service.py

from app.services.session_aware_archiver import session_aware_archiver
from app.core.environment import EnvironmentDetector

class KanbanArchiveService:

    async def _sync_to_obsidian(
        self, task: Task, ai_summary: AISummary, roi_metrics: ROIMetrics
    ) -> ObsidianSyncStatus:
        """
        Sync archived task to Obsidian vault (Q6).

        NEW: Uses SessionAwareArchiver for consolidated session summaries.
        """
        # Create archived task object
        archived_task = ArchivedTaskWithMetrics(
            task_id=task.task_id,
            title=task.title,
            description=task.description,
            phase_name=task.phase_name,
            archived_at=datetime.now(UTC),
            archived_by="system",
            ai_summary=ai_summary,
            roi_metrics=roi_metrics,
            obsidian_synced=False,
            obsidian_note_path=None,
        )

        # Route to session-aware archiver
        session_aware_archiver.archive_task(archived_task)

        # Return status
        return ObsidianSyncStatus(
            task_id=task.task_id,
            synced=not EnvironmentDetector.is_test_mode(),
            obsidian_note_path="Session-based (consolidated)",
            sync_timestamp=datetime.now(UTC),
        )
```

### 5.2 Test Fixture Updates

```python
# backend/tests/conftest.py

import pytest
from app.services.session_aware_archiver import session_aware_archiver


@pytest.fixture(autouse=True)
def reset_session_archiver():
    """Reset session archiver state before each test."""
    session_aware_archiver.reset_for_testing()
    yield
    session_aware_archiver.reset_for_testing()


@pytest.fixture
def session_buffer():
    """Access to test buffer for assertions."""
    return session_aware_archiver.get_test_buffer
```

### 5.3 Feature Flag Integration

```python
# Check before Obsidian operations
from app.core.feature_flags import is_feature_enabled, FeatureFlag

if is_feature_enabled(FeatureFlag.KANBAN_OBSIDIAN_SYNC):
    session_aware_archiver.archive_task(task)
else:
    logger.debug("Obsidian sync disabled by feature flag")
```

---

## 6. API Endpoints (Optional)

```python
# backend/app/routers/session.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/session", tags=["session"])


class StartSessionRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    status: str
    task_count: int


@router.post("/start", response_model=SessionResponse)
async def start_session(request: StartSessionRequest):
    """Start a new development session."""
    session_id = session_aware_archiver.start_session(
        session_name=request.name,
        description=request.description
    )
    return SessionResponse(
        session_id=session_id,
        status="active",
        task_count=0
    )


@router.post("/end", response_model=SessionResponse)
async def end_session():
    """End current session and generate summary."""
    result = session_aware_archiver.end_session()
    return SessionResponse(
        session_id=result or "none",
        status="completed",
        task_count=len(session_aware_archiver.get_test_buffer())
    )


@router.post("/daily-rollup")
async def generate_daily_rollup(date: Optional[str] = None):
    """Generate daily rollup summary."""
    result = session_aware_archiver.generate_daily_rollup(date)
    if result:
        return {"status": "success", "path": result}
    return {"status": "no_sessions", "path": None}
```

---

## 7. Verification Checklist

### 7.1 Test Mode Verification

- [ ] No files created during `pytest` runs
- [ ] Test buffer accessible for assertions
- [ ] Service fully functional in memory
- [ ] `PYTEST_CURRENT_TEST` environment detected

### 7.2 Production Mode Verification

- [ ] Session notes created with correct naming
- [ ] Daily rollup generated at day end
- [ ] Tasks consolidated within sessions
- [ ] MOC/Index updated

### 7.3 Migration Verification

- [ ] Feature flag controls routing
- [ ] Fallback to old behavior works
- [ ] Cleanup script identifies mock files
- [ ] No data loss during transition

---

## 8. Trade-offs and Considerations

### 8.1 Trade-offs Made

| Decision | Trade-off | Rationale |
|----------|-----------|-----------|
| Session-based | Less granular than per-task | Reduces noise by 95%, maintains meaningful context |
| Test isolation | Tests can't verify file I/O | Prevents vault pollution, tests can verify via buffer |
| Auto-session | Implicit session boundaries | Reduces cognitive load, still allows explicit control |
| Daily rollup | Extra file creation | Provides daily overview without manual aggregation |

### 8.2 Future Enhancements

1. **Session Detection**: Auto-detect session boundaries from git commits
2. **Smart Naming**: Use LLM to generate descriptive session names
3. **Cross-Session Linking**: Link related sessions across days
4. **Analytics Dashboard**: Session productivity trends

---

## 9. Summary

This architecture addresses the file explosion problem by:

1. **Consolidating** tasks into session summaries (1 file per session, not per task)
2. **Isolating** test mode (zero file I/O during tests)
3. **Providing** meaningful names based on actual work
4. **Generating** daily rollups for overview
5. **Maintaining** backward compatibility via feature flags

Expected outcomes:
- 95% reduction in file count
- Zero test data pollution
- Full session traceability
- Clean migration path

---

*Document Version: 1.0*
*Last Updated: 2025-12-28*
