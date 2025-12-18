"""
Obsidian Service

Integrates with Obsidian vault for knowledge management, auto-sync, and error resolution.
Implements 3-Tier Error Resolution (Tier 1: Obsidian past solutions).
"""

import re
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ObsidianService:
    """
    Service for Obsidian vault integration

    Features:
    - Event-based auto-sync with debouncing (token optimization)
    - Search past solutions for 3-Tier Error Resolution (Tier 1)
    - Save error resolutions for future reuse
    - Track sync history with batching metrics
    """

    def __init__(self, vault_path: Optional[Path] = None, debounce_window: int = 3):
        """
        Initialize Obsidian Service

        Args:
            vault_path: Path to Obsidian vault (auto-detected if not provided)
            debounce_window: Seconds to wait for event batching (default: 3)
        """
        if vault_path:
            self.vault_path = Path(vault_path).resolve()
        else:
            # Auto-detect Obsidian vault
            self.vault_path = self._auto_detect_vault()

        # Validate vault exists
        if not self.vault_path or not self.vault_path.exists():
            logger.warning(f"Obsidian vault not found at: {self.vault_path}")
            self.vault_available = False
        else:
            logger.info(f"Obsidian vault detected at: {self.vault_path}")
            self.vault_available = True

        # Daily notes directory
        self.daily_notes_dir = self.vault_path / "[EMOJI]" if self.vault_available else None

        # In-memory sync history (would be database in production)
        self.sync_history: List[Dict[str, Any]] = []

        # Debouncing state for event-based sync
        self.pending_events: List[Dict[str, Any]] = []
        self.last_sync: Optional[datetime] = None
        self.debounce_window: int = debounce_window
        self._flush_task: Optional[asyncio.Task] = None
        self._flush_lock: asyncio.Lock = asyncio.Lock()
        self.moc_path = None
        if self.vault_available:
            self.moc_path = self.vault_path / "UDO" / "MOC_Uncertainty.md"

    def _auto_detect_vault(self) -> Optional[Path]:
        """
        Auto-detect Obsidian vault location

        Returns:
            Path to Obsidian vault or None
        """
        # Common Obsidian vault locations
        common_paths = [
            Path(r"C:\Users\user\Documents\Obsidian Vault"),
            Path.home() / "Documents" / "Obsidian Vault",
            Path.home() / "Obsidian Vault",
            Path.cwd() / "Obsidian Vault"
        ]

        for path in common_paths:
            if path.exists() and (path / ".obsidian").exists():
                logger.info(f"Auto-detected Obsidian vault: {path}")
                return path

        logger.warning("Could not auto-detect Obsidian vault")
        return None

    async def sync_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Add event to pending queue with debouncing (event-based sync).

        This is the preferred method for event-based synchronization.
        Multiple events within debounce_window (default 3s) are batched into a single note.

        Strategy:
        - If 3s passed since last sync -> flush immediately
        - Otherwise -> queue event and schedule flush after 3s
        - Multiple events within window -> batched into one sync

        Args:
            event_type: Type of event (phase_transition, error_resolution, task_completion, etc.)
            data: Event data dictionary

        Returns:
            True if event queued/flushed successfully, False otherwise
        """
        if not self.vault_available:
            logger.warning("Obsidian vault not available, skipping event sync")
            return False

        try:
            # Add event to pending queue
            event = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now()
            }

            async with self._flush_lock:
                self.pending_events.append(event)

                if self._should_flush_immediately():
                    # Immediate flush if 3s passed since last sync
                    logger.debug(f"Immediate flush triggered for {event_type}")
                    await self._flush_events_internal()
                else:
                    # Schedule delayed flush
                    logger.debug(f"Event queued, scheduling flush for {event_type}")
                    self._schedule_flush()

            return True

        except Exception as e:
            logger.error(f"Failed to queue event: {e}", exc_info=True)
            return False

    def _should_flush_immediately(self) -> bool:
        """Check if we should flush immediately (3s since last sync)"""
        if not self.last_sync:
            return False  # First event should be queued, not flushed immediately

        elapsed = (datetime.now() - self.last_sync).total_seconds()
        return elapsed >= self.debounce_window

    def _schedule_flush(self):
        """Schedule delayed flush after debounce window"""
        # Cancel existing task if still pending
        if self._flush_task and not self._flush_task.done():
            logger.debug("Flush already scheduled, extending window")
            self._flush_task.cancel()

        # Schedule new flush
        self._flush_task = asyncio.create_task(self._delayed_flush())

    async def _delayed_flush(self):
        """Wait for debounce window then flush events"""
        try:
            await asyncio.sleep(self.debounce_window)

            async with self._flush_lock:
                await self._flush_events_internal()

        except asyncio.CancelledError:
            logger.debug("Delayed flush cancelled (new event arrived)")
        except Exception as e:
            logger.error(f"Delayed flush failed: {e}", exc_info=True)

    async def _flush_events_internal(self):
        """
        Internal method to flush all pending events as single note.

        Should only be called while holding _flush_lock.
        """
        if not self.pending_events:
            logger.debug("No pending events to flush")
            return

        try:
            # Copy and clear pending events
            events = self.pending_events.copy()
            self.pending_events.clear()
            self.last_sync = datetime.now()

            logger.info(f"Flushing {len(events)} pending events")

            # Generate batch title and content
            if len(events) == 1:
                # Single event - use regular format
                event = events[0]
                title = self._generate_event_title(event["type"], event["data"])
                content = self._generate_event_content(event["type"], event["data"])
            else:
                # Multiple events - use batch format
                title = self._generate_batch_title(events)
                content = self._generate_batch_content(events)

            # Create daily note
            success = await self.create_daily_note(title, content)

            # Track in history
            self.sync_history.append({
                "event_type": "batch_sync" if len(events) > 1 else events[0]["type"],
                "events_count": len(events),
                "timestamp": datetime.now().isoformat(),
                "title": title,
                "success": success
            })

            if success:
                logger.info(
                    f"Successfully flushed {len(events)} event(s) to Obsidian: {title}"
                )
            else:
                logger.warning(f"Failed to flush {len(events)} event(s)")

        except Exception as e:
            logger.error(f"Error flushing events: {e}", exc_info=True)

    def _generate_batch_title(self, events: List[Dict[str, Any]]) -> str:
        """Generate title for batched events"""
        event_types = [e["type"] for e in events]
        unique_types = list(dict.fromkeys(event_types))  # Preserve order, remove dupes

        if len(unique_types) == 1:
            # All same type
            return f"Batch: {len(events)} {unique_types[0]} Events"
        else:
            # Mixed types
            return f"Batch: {len(events)} Development Events"

    def _generate_batch_content(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate structured content for batched events

        Returns:
            Dict with 'frontmatter' and 'content' keys
        """
        now = datetime.now()

        # Aggregate tags from all events
        all_tags = set(["development", "udo", "batch"])
        for event in events:
            event_tags = event["data"].get("tags", [])
            all_tags.update(event_tags)

        # YAML frontmatter
        frontmatter = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "project": events[0]["data"].get("project", "UDO-Development-Platform"),
            "event_type": "batch_sync",
            "events_count": len(events),
            "tags": list(all_tags),
        }

        # Markdown content - one section per event
        content_parts = []

        for i, event in enumerate(events, 1):
            event_time = event["timestamp"].strftime("%H:%M")
            event_title = self._generate_event_title(event["type"], event["data"])

            content_parts.append(f"## Event {i}: {event_title} ({event_time})")
            content_parts.append("")

            # Add event-specific content
            event_content = self._generate_event_content(event["type"], event["data"])
            content_parts.append(event_content.get("content", ""))
            content_parts.append("")

        return {
            "frontmatter": frontmatter,
            "content": "\n".join(content_parts)
        }

    async def force_flush(self) -> int:
        """
        Force immediate flush of pending events (manual trigger).

        Returns:
            Number of events flushed
        """
        async with self._flush_lock:
            events_count = len(self.pending_events)

            if events_count > 0:
                await self._flush_events_internal()
                logger.info(f"Force flushed {events_count} events")

            return events_count

    async def auto_sync(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Auto-sync development event to Obsidian (triggered within 3 seconds)

        Args:
            event_type: Type of event (phase_transition, error_resolution, task_completion, etc.)
            data: Event data dictionary

        Returns:
            True if sync successful, False otherwise
        """
        if not self.vault_available:
            logger.warning("Obsidian vault not available, skipping auto-sync")
            return False

        try:
            # Generate daily note content
            title = self._generate_event_title(event_type, data)
            content = self._generate_event_content(event_type, data)

            # Create or append to daily note
            success = await self.create_daily_note(title, content)

            if success:
                # Track sync history
                self.sync_history.append({
                    "event_type": event_type,
                    "timestamp": datetime.now().isoformat(),
                    "title": title,
                    "success": True
                })
                logger.info(f"Auto-synced {event_type} to Obsidian: {title}")

            return success

        except Exception as e:
            logger.error(f"Auto-sync failed: {e}", exc_info=True)
            self.sync_history.append({
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "success": False
            })
            return False

    def _generate_event_title(self, event_type: str, data: Dict[str, Any]) -> str:
        """Generate title for event"""
        event_titles = {
            "phase_transition": f"Phase Transition: {data.get('from_phase', 'Unknown')} -> {data.get('to_phase', 'Unknown')}",
            "error_resolution": f"Error Resolved: {data.get('error_type', 'Unknown Error')}",
            "task_completion": f"Task Completed: {data.get('task_title', 'Unknown Task')}",
            "architecture_decision": f"ADR: {data.get('decision_title', 'Architecture Decision')}",
            "time_milestone": f"Time Milestone: {data.get('milestone_name', 'Unknown')}",
        }
        return event_titles.get(event_type, f"Event: {event_type}")

    def _generate_event_content(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured content for event

        Returns:
            Dict with 'frontmatter' and 'content' keys
        """
        now = datetime.now()

        # YAML frontmatter
        frontmatter = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "project": data.get("project", "UDO-Development-Platform"),
            "event_type": event_type,
            "tags": data.get("tags", ["development", "udo"]),
        }

        # Add phase if available
        if "phase" in data or "to_phase" in data:
            frontmatter["phase"] = data.get("to_phase", data.get("phase"))

        # Markdown content
        content_parts = []

        # Context section
        if "context" in data:
            content_parts.append("## Context")
            for key, value in data["context"].items():
                content_parts.append(f"- {key}: {value}")
            content_parts.append("")

        # Changes section
        if "changes" in data:
            content_parts.append("## Changes")
            for change in data["changes"]:
                content_parts.append(f"- {change}")
            content_parts.append("")

        # Decisions section
        if "decisions" in data:
            content_parts.append("## Decisions Made")
            for decision in data["decisions"]:
                content_parts.append(f"- {decision}")
            content_parts.append("")

        # Solution section (for error resolutions)
        if "solution" in data:
            content_parts.append("## Solution")
            content_parts.append(f"```")
            content_parts.append(data["solution"])
            content_parts.append("```")
            content_parts.append("")

        # Time metrics section
        if "duration" in data:
            content_parts.append("## Time Metrics")
            content_parts.append(f"- Duration: {data['duration']}")
            if "productivity" in data:
                content_parts.append(f"- Productivity: {data['productivity']}")
            content_parts.append("")

        # Additional data
        if "additional" in data:
            content_parts.append("## Additional Information")
            for key, value in data["additional"].items():
                content_parts.append(f"- {key}: {value}")
            content_parts.append("")

        return {
            "frontmatter": frontmatter,
            "content": "\n".join(content_parts)
        }

    async def create_daily_note(self, title: str, content: Dict[str, Any]) -> bool:
        """
        Create structured daily note in Obsidian vault

        Args:
            title: Note title
            content: Dict with 'frontmatter' and 'content' keys

        Returns:
            True if successful, False otherwise
        """
        if not self.vault_available:
            logger.warning("Obsidian vault not available")
            return False

        try:
            # Ensure daily notes directory exists
            date_str = datetime.now().strftime("%Y-%m-%d")
            date_dir = self.daily_notes_dir / date_str
            date_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename (sanitize title)
            safe_title = re.sub(r'[<>:"/\\|?*]', '-', title)
            filename = f"{safe_title}.md"
            filepath = date_dir / filename

            # Build markdown with frontmatter
            markdown_lines = ["---"]

            frontmatter = content.get("frontmatter", {})
            for key, value in frontmatter.items():
                if isinstance(value, list):
                    # Format list as YAML array
                    markdown_lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
                else:
                    markdown_lines.append(f"{key}: {value}")

            markdown_lines.append("---")
            markdown_lines.append("")
            markdown_lines.append(f"# {title}")
            markdown_lines.append("")
            markdown_lines.append(content.get("content", ""))

            # Write to file
            filepath.write_text("\n".join(markdown_lines), encoding="utf-8")

            logger.info(f"Created daily note: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to create daily note: {e}", exc_info=True)
            return False

    async def append_log(self, content: str) -> bool:
        """
        Append raw markdown content to today's daily note (lightweight helper).
        """
        if not self.vault_available or not self.daily_notes_dir:
            logger.warning("Obsidian vault not available for append_log")
            return False

        try:
            self.daily_notes_dir.mkdir(parents=True, exist_ok=True)
            today = datetime.now().strftime("%Y-%m-%d")
            note_path = self.daily_notes_dir / f"{today}.md"

            if not note_path.exists():
                note_path.write_text(f"# Daily Log {today}\n\n", encoding="utf-8")

            with open(note_path, "a", encoding="utf-8") as f:
                f.write(f"\n{content}\n")

            return True
        except Exception as e:
            logger.error(f"Failed to append to Obsidian log: {e}", exc_info=True)
            return False

    async def update_moc(self):
        """
        Update Map of Contents for recent sessions (lightweight index).

        This avoids complex parsing; it simply lists daily notes for the last 30 days.
        """
        if not self.vault_available or not self.moc_path:
            return False

        try:
            thirty_days_ago = datetime.now() - timedelta(days=30)
            lines = [
                "# Uncertainty Management MOC",
                "",
                "## Recent Daily Logs (30 days)",
            ]

            for path in sorted(self.daily_notes_dir.glob("*.md")):
                # Filter by date in filename yyyy-mm-dd.md
                try:
                    date_str = path.stem
                    note_date = datetime.strptime(date_str.split("_")[0], "%Y-%m-%d")
                except Exception:
                    continue

                if note_date < thirty_days_ago:
                    continue

                lines.append(f"- [[{path.name}|{date_str}]]")

            if len(lines) == 3:
                lines.append("- (no recent logs)")

            self.moc_path.parent.mkdir(parents=True, exist_ok=True)
            self.moc_path.write_text("\n".join(lines), encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Failed to update MOC: {e}", exc_info=True)
            return False

    async def search_knowledge(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search Obsidian vault for past solutions (3-Tier Resolution Tier 1)

        Args:
            query: Search query (error message, keywords, etc.)
            max_results: Maximum number of results to return

        Returns:
            List of matching notes with excerpts
        """
        if not self.vault_available:
            logger.warning("Obsidian vault not available for search")
            return []

        try:
            results = []
            query_lower = query.lower()

            # Search in daily notes directory
            if self.daily_notes_dir and self.daily_notes_dir.exists():
                for date_dir in sorted(self.daily_notes_dir.iterdir(), reverse=True):
                    if not date_dir.is_dir():
                        continue

                    for note_file in date_dir.glob("*.md"):
                        try:
                            content = note_file.read_text(encoding="utf-8")
                            content_lower = content.lower()

                            # Check if query matches
                            if query_lower in content_lower:
                                # Extract relevant excerpt (200 chars around match)
                                match_pos = content_lower.find(query_lower)
                                start = max(0, match_pos - 100)
                                end = min(len(content), match_pos + 100)
                                excerpt = content[start:end]

                                # Parse frontmatter
                                frontmatter = self._parse_frontmatter(content)

                                results.append({
                                    "filepath": str(note_file.relative_to(self.vault_path)),
                                    "title": note_file.stem,
                                    "date": frontmatter.get("date", ""),
                                    "event_type": frontmatter.get("event_type", ""),
                                    "excerpt": excerpt,
                                    "relevance_score": content_lower.count(query_lower)
                                })

                                if len(results) >= max_results:
                                    break

                        except Exception as e:
                            logger.debug(f"Error reading note {note_file}: {e}")
                            continue

                    if len(results) >= max_results:
                        break

            # Sort by relevance score
            results.sort(key=lambda x: x["relevance_score"], reverse=True)

            logger.info(f"Search for '{query}' returned {len(results)} results")
            return results[:max_results]

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return []

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """
        Parse YAML frontmatter from markdown content

        Args:
            content: Markdown content with frontmatter

        Returns:
            Dict of frontmatter fields
        """
        frontmatter = {}

        # Match frontmatter between --- markers
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if match:
            yaml_content = match.group(1)

            # Simple YAML parsing (key: value)
            for line in yaml_content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()

        return frontmatter

    async def save_error_resolution(
        self,
        error: str,
        solution: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save error resolution for future 3-Tier Resolution reuse

        Args:
            error: Error message or description
            solution: Solution that worked
            context: Additional context (tool, file, command, etc.)

        Returns:
            True if successful, False otherwise
        """
        if not self.vault_available:
            logger.warning("Obsidian vault not available")
            return False

        try:
            # Extract error type for better categorization
            error_type = self._extract_error_type(error)

            # Create resolution note
            data = {
                "project": "UDO-Development-Platform",
                "tags": ["error-resolution", "debugging", error_type],
                "context": context or {},
                "solution": solution,
            }

            data["context"]["error_message"] = error
            data["context"]["resolved_at"] = datetime.now().isoformat()

            # Auto-sync as error_resolution event
            return await self.auto_sync("error_resolution", data)

        except Exception as e:
            logger.error(f"Failed to save error resolution: {e}", exc_info=True)
            return False

    def _extract_error_type(self, error: str) -> str:
        """
        Extract error type from error message

        Args:
            error: Error message

        Returns:
            Error type (e.g., 'ModuleNotFoundError', 'PermissionError', etc.)
        """
        # Common error patterns
        patterns = [
            (r'ModuleNotFoundError', 'ModuleNotFoundError'),
            (r'ImportError', 'ImportError'),
            (r'PermissionError|Permission denied', 'PermissionError'),
            (r'FileNotFoundError|No such file', 'FileNotFoundError'),
            (r'401|Unauthorized', '401-Unauthorized'),
            (r'403|Forbidden', '403-Forbidden'),
            (r'404|Not Found', '404-NotFound'),
            (r'500|Internal Server Error', '500-ServerError'),
            (r'TypeError', 'TypeError'),
            (r'ValueError', 'ValueError'),
            (r'AttributeError', 'AttributeError'),
            (r'KeyError', 'KeyError'),
        ]

        for pattern, error_type in patterns:
            if re.search(pattern, error, re.IGNORECASE):
                return error_type

        return 'UnknownError'

    async def get_recent_notes(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get recent development notes from Obsidian vault

        Args:
            days: Number of days to look back

        Returns:
            List of recent notes with metadata
        """
        if not self.vault_available:
            logger.warning("Obsidian vault not available")
            return []

        try:
            recent_notes = []
            cutoff_date = datetime.now() - timedelta(days=days)

            if self.daily_notes_dir and self.daily_notes_dir.exists():
                for date_dir in sorted(self.daily_notes_dir.iterdir(), reverse=True):
                    if not date_dir.is_dir():
                        continue

                    # Check if directory is within date range
                    try:
                        dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                        if dir_date < cutoff_date:
                            break
                    except ValueError:
                        continue

                    for note_file in date_dir.glob("*.md"):
                        try:
                            content = note_file.read_text(encoding="utf-8")
                            frontmatter = self._parse_frontmatter(content)

                            recent_notes.append({
                                "filepath": str(note_file.relative_to(self.vault_path)),
                                "title": note_file.stem,
                                "date": frontmatter.get("date", ""),
                                "time": frontmatter.get("time", ""),
                                "event_type": frontmatter.get("event_type", ""),
                                "project": frontmatter.get("project", ""),
                                "tags": frontmatter.get("tags", ""),
                            })

                        except Exception as e:
                            logger.debug(f"Error reading note {note_file}: {e}")
                            continue

            logger.info(f"Retrieved {len(recent_notes)} notes from last {days} days")
            return recent_notes

        except Exception as e:
            logger.error(f"Failed to get recent notes: {e}", exc_info=True)
            return []

    async def resolve_error_tier1(self, error_msg: str) -> Optional[str]:
        """
        Tier 1 error resolution: Search Obsidian for past solutions

        This is the first tier of 3-Tier Error Resolution system.
        Target: <10ms response time, 70% hit rate for recurring errors.

        Args:
            error_msg: Error message to resolve

        Returns:
            Solution string if found, None otherwise
        """
        if not self.vault_available:
            return None

        start_time = datetime.now()

        try:
            # Search for similar errors
            results = await self.search_knowledge(error_msg, max_results=3)

            if results:
                # Extract solution from first matching note
                best_match = results[0]
                filepath = self.vault_path / best_match["filepath"]

                if filepath.exists():
                    content = filepath.read_text(encoding="utf-8")

                    # Extract solution section
                    solution_match = re.search(
                        r'## Solution\s*```(.*?)```',
                        content,
                        re.DOTALL
                    )

                    if solution_match:
                        solution = solution_match.group(1).strip()

                        elapsed = (datetime.now() - start_time).total_seconds() * 1000
                        logger.info(
                            f"Tier 1 resolution found in {elapsed:.1f}ms: "
                            f"{best_match['title']}"
                        )

                        return solution

            return None

        except Exception as e:
            logger.error(f"Tier 1 resolution failed: {e}", exc_info=True)
            return None

    def get_sync_statistics(self) -> Dict[str, Any]:
        """
        Get sync statistics including batching efficiency

        Returns:
            Dict with sync statistics and batching metrics
        """
        total = len(self.sync_history)
        successful = sum(1 for s in self.sync_history if s.get("success", False))
        failed = total - successful

        # Group by event type
        by_type = {}
        for sync in self.sync_history:
            event_type = sync.get("event_type", "unknown")
            by_type[event_type] = by_type.get(event_type, 0) + 1

        # Calculate batching efficiency
        total_events = sum(s.get("events_count", 1) for s in self.sync_history)
        avg_events_per_sync = total_events / total if total > 0 else 0

        # Token optimization estimate (assumes 100 tokens per sync saved per batched event)
        batching_syncs = sum(1 for s in self.sync_history if s.get("events_count", 1) > 1)
        tokens_saved_estimate = sum(
            (s.get("events_count", 1) - 1) * 100
            for s in self.sync_history
            if s.get("events_count", 1) > 1
        )

        return {
            "total_syncs": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round(successful / total * 100, 2) if total > 0 else 0,
            "by_event_type": by_type,
            "vault_available": self.vault_available,
            "vault_path": str(self.vault_path) if self.vault_path else None,
            # Batching metrics
            "total_events": total_events,
            "avg_events_per_sync": round(avg_events_per_sync, 2),
            "batching_syncs": batching_syncs,
            "batching_rate": round(batching_syncs / total * 100, 2) if total > 0 else 0,
            "tokens_saved_estimate": tokens_saved_estimate,
            "pending_events": len(self.pending_events),
        }


# Create singleton instance
obsidian_service = ObsidianService()

# Export
__all__ = ['ObsidianService', 'obsidian_service']
