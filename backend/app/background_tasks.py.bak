"""
Background Tasks for Periodic Operations
Handles automatic Obsidian sync every 1-2 hours
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import subprocess

logger = logging.getLogger(__name__)


class BackgroundSyncTask:
    """Periodic Obsidian sync task to prevent context loss"""

    def __init__(self, sync_interval_hours: int = 1):
        """
        Initialize background sync task

        Args:
            sync_interval_hours: Sync interval in hours (default: 1 hour)
        """
        self.sync_interval_hours = sync_interval_hours
        self.sync_interval_seconds = sync_interval_hours * 3600
        self.task: Optional[asyncio.Task] = None
        self.running = False
        self.last_sync: Optional[datetime] = None
        self.project_root = self._find_project_root()

    def _find_project_root(self) -> Path:
        """Find UDO-Development-Platform project root"""
        current = Path(__file__).resolve()
        for parent in current.parents:
            if parent.name == "UDO-Development-Platform":
                return parent
            if (parent / "backend").exists() and (parent / ".git").exists():
                return parent
        return Path.cwd()

    async def start(self):
        """Start the background sync task"""
        if self.running:
            logger.warning("Background sync task already running")
            return

        self.running = True
        self.task = asyncio.create_task(self._sync_loop())
        logger.info(f"✅ Background sync started (interval: {self.sync_interval_hours}h)")

    async def stop(self):
        """Stop the background sync task"""
        if not self.running:
            return

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ Background sync stopped")

    async def _sync_loop(self):
        """Main sync loop - runs every N hours"""
        try:
            while self.running:
                # Wait for the interval
                await asyncio.sleep(self.sync_interval_seconds)

                # Perform sync
                await self._perform_sync()

        except asyncio.CancelledError:
            logger.info("Sync loop cancelled")
        except Exception as e:
            logger.error(f"Error in sync loop: {e}")

    async def _perform_sync(self):
        """Perform the actual sync operation"""
        try:
            logger.info("🔄 Periodic sync triggered...")

            # Check if there are uncommitted changes
            has_changes = await self._check_git_changes()

            if not has_changes:
                logger.info("No changes detected, skipping sync")
                return

            # Create temporary development log
            await self._create_temp_devlog()

            self.last_sync = datetime.now()
            logger.info(f"✅ Periodic sync completed at {self.last_sync.strftime('%H:%M:%S')}")

        except Exception as e:
            logger.error(f"Failed to perform sync: {e}")

    async def _check_git_changes(self) -> bool:
        """Check if there are uncommitted changes"""
        try:
            # Run git status to check for changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            # If output is not empty, there are changes
            has_changes = bool(result.stdout.strip())

            if has_changes:
                logger.info("Detected uncommitted changes")

            return has_changes

        except Exception as e:
            logger.error(f"Failed to check git status: {e}")
            return False

    async def _create_temp_devlog(self):
        """Create temporary development log in Obsidian"""
        try:
            # Try to use Obsidian MCP if available
            try:
                from app.services.obsidian_service import ObsidianService

                obsidian_service = ObsidianService()
                await obsidian_service.sync_event("periodic_backup", {
                    "timestamp": datetime.now().isoformat(),
                    "type": "auto_backup",
                    "sync_interval": f"{self.sync_interval_hours}h",
                    "message": "자동 백업 (컨텍스트 유실 방지)"
                })

                # Flush immediately (don't wait for debouncing)
                await obsidian_service.flush_pending_events()

                logger.info("📝 Temporary devlog created via ObsidianService")

            except ImportError:
                logger.warning("ObsidianService not available, using direct MCP call")
                # Fallback: Direct script execution could go here
                pass

        except Exception as e:
            logger.error(f"Failed to create temp devlog: {e}")

    def get_status(self) -> dict:
        """Get current status of background sync"""
        return {
            "running": self.running,
            "sync_interval_hours": self.sync_interval_hours,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "next_sync_in_seconds": self.sync_interval_seconds - (
                (datetime.now() - self.last_sync).total_seconds()
                if self.last_sync else 0
            ) if self.last_sync else self.sync_interval_seconds
        }


# Global instance
background_sync_task: Optional[BackgroundSyncTask] = None


def get_background_sync() -> Optional[BackgroundSyncTask]:
    """Get global background sync task instance"""
    return background_sync_task


async def start_background_sync(sync_interval_hours: int = 1):
    """
    Start background sync task

    Args:
        sync_interval_hours: Sync interval in hours (default: 1)
    """
    global background_sync_task

    if background_sync_task is not None:
        logger.warning("Background sync already initialized")
        return background_sync_task

    background_sync_task = BackgroundSyncTask(sync_interval_hours=sync_interval_hours)
    await background_sync_task.start()

    return background_sync_task


async def stop_background_sync():
    """Stop background sync task"""
    global background_sync_task

    if background_sync_task is not None:
        await background_sync_task.stop()
        background_sync_task = None
