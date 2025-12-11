# Phase 5.1: Session Management - Implementation Plan

**Phase:** 5.1
**Name:** Session Management
**Dependencies:** Phase 3.2 (LangChain Integration), Phase 4.2 (Hooks System)

---

## Overview

This plan details the implementation of session management for Code-Forge, enabling conversation persistence, session resume, and history tracking.

---

## Implementation Order

1. **models.py** - Session and ToolInvocation dataclasses
2. **storage.py** - File-based session persistence
3. **index.py** - Session index for fast listing
4. **manager.py** - Session lifecycle management

---

## File 1: src/forge/sessions/models.py

```python
"""Session data models."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid
import json


@dataclass
class ToolInvocation:
    """Record of a tool invocation within a session.

    Tracks tool execution history including arguments, results,
    timing, and success/failure status.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration: float = 0.0
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "success": self.success,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolInvocation":
        """Deserialize from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            tool_name=data.get("tool_name", ""),
            arguments=data.get("arguments", {}),
            result=data.get("result"),
            timestamp=timestamp,
            duration=data.get("duration", 0.0),
            success=data.get("success", True),
            error=data.get("error"),
        )


@dataclass
class SessionMessage:
    """A message within a session.

    Wraps the core Message type with session-specific metadata.
    Provides conversion to/from LangChain and OpenAI message formats.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: str = "user"  # "system", "user", "assistant", "tool"
    content: str = ""
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        data: dict[str, Any] = {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.tool_calls is not None:
            data["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            data["tool_call_id"] = self.tool_call_id
        if self.name is not None:
            data["name"] = self.name
        return data

    def to_llm_message(self) -> dict[str, Any]:
        """Convert to LLM-compatible message format (OpenAI/Anthropic style).

        Returns:
            Dictionary suitable for LLM API calls and ContextManager.
            Does NOT include session-specific fields like id/timestamp.
        """
        msg: dict[str, Any] = {
            "role": self.role,
            "content": self.content,
        }
        if self.tool_calls is not None:
            msg["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            msg["tool_call_id"] = self.tool_call_id
        if self.name is not None:
            msg["name"] = self.name
        return msg

    @classmethod
    def from_llm_message(cls, msg: dict[str, Any]) -> "SessionMessage":
        """Create SessionMessage from an LLM message dict.

        Args:
            msg: Message dict with role, content, and optional tool fields.

        Returns:
            SessionMessage instance with new id and timestamp.
        """
        return cls(
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
            tool_calls=msg.get("tool_calls"),
            tool_call_id=msg.get("tool_call_id"),
            name=msg.get("name"),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionMessage":
        """Deserialize from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            role=data.get("role", "user"),
            content=data.get("content", ""),
            tool_calls=data.get("tool_calls"),
            tool_call_id=data.get("tool_call_id"),
            name=data.get("name"),
            timestamp=timestamp,
        )


@dataclass
class Session:
    """A conversation session.

    Contains all messages, tool invocations, and metadata for a
    single conversation session. Sessions can be persisted to disk
    and resumed later.

    Attributes:
        id: Unique session identifier (UUID).
        title: Human-readable session title.
        created_at: When the session was created.
        updated_at: When the session was last modified.
        working_dir: Working directory for the session.
        model: LLM model used for this session.
        messages: List of conversation messages.
        tool_history: List of tool invocations.
        total_prompt_tokens: Cumulative prompt tokens used.
        total_completion_tokens: Cumulative completion tokens used.
        tags: Tags for organization.
        metadata: Additional custom key-value data.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    working_dir: str = ""
    model: str = ""

    messages: list[SessionMessage] = field(default_factory=list)
    tool_history: list[ToolInvocation] = field(default_factory=list)

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0

    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: SessionMessage) -> None:
        """Add a message to the session.

        Args:
            message: The message to add.
        """
        self.messages.append(message)
        self._mark_updated()

    def add_message_from_dict(
        self,
        role: str,
        content: str,
        **kwargs: Any,
    ) -> SessionMessage:
        """Create and add a message from components.

        Args:
            role: Message role (system, user, assistant, tool).
            content: Message content.
            **kwargs: Additional message fields.

        Returns:
            The created SessionMessage.
        """
        message = SessionMessage(
            role=role,
            content=content,
            **kwargs,
        )
        self.add_message(message)
        return message

    def add_tool_invocation(self, invocation: ToolInvocation) -> None:
        """Add a tool invocation to history.

        Args:
            invocation: The tool invocation record.
        """
        self.tool_history.append(invocation)
        self._mark_updated()

    def record_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any] | None = None,
        duration: float = 0.0,
        success: bool = True,
        error: str | None = None,
    ) -> ToolInvocation:
        """Record a tool invocation from components.

        Args:
            tool_name: Name of the tool.
            arguments: Arguments passed to the tool.
            result: Tool execution result.
            duration: Execution duration in seconds.
            success: Whether execution succeeded.
            error: Error message if failed.

        Returns:
            The created ToolInvocation.
        """
        invocation = ToolInvocation(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            duration=duration,
            success=success,
            error=error,
        )
        self.add_tool_invocation(invocation)
        return invocation

    def update_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Update token usage statistics.

        Args:
            prompt_tokens: Number of prompt tokens used.
            completion_tokens: Number of completion tokens used.
        """
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self._mark_updated()

    @property
    def total_tokens(self) -> int:
        """Total tokens used in this session."""
        return self.total_prompt_tokens + self.total_completion_tokens

    @property
    def message_count(self) -> int:
        """Number of messages in the session."""
        return len(self.messages)

    def _mark_updated(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Serialize session to dictionary for JSON storage.

        Returns:
            Dictionary representation of the session.
        """
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "working_dir": self.working_dir,
            "model": self.model,
            "messages": [m.to_dict() for m in self.messages],
            "tool_history": [t.to_dict() for t in self.tool_history],
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize session to JSON string.

        Args:
            indent: JSON indentation level.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """Deserialize session from dictionary.

        Args:
            data: Dictionary containing session data.

        Returns:
            Session instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.now(timezone.utc)

        messages = [
            SessionMessage.from_dict(m)
            for m in data.get("messages", [])
        ]

        tool_history = [
            ToolInvocation.from_dict(t)
            for t in data.get("tool_history", [])
        ]

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            created_at=created_at,
            updated_at=updated_at,
            working_dir=data.get("working_dir", ""),
            model=data.get("model", ""),
            messages=messages,
            tool_history=tool_history,
            total_prompt_tokens=data.get("total_prompt_tokens", 0),
            total_completion_tokens=data.get("total_completion_tokens", 0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Session":
        """Deserialize session from JSON string.

        Args:
            json_str: JSON string containing session data.

        Returns:
            Session instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
```

---

## File 2: src/forge/sessions/storage.py

```python
"""Session persistence layer."""

import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Session

logger = logging.getLogger(__name__)


class SessionStorageError(Exception):
    """Error during session storage operations."""
    pass


class SessionNotFoundError(SessionStorageError):
    """Session not found in storage."""
    pass


class SessionCorruptedError(SessionStorageError):
    """Session file is corrupted."""
    pass


class SessionStorage:
    """Handles session persistence to disk.

    Sessions are stored as JSON files in a configurable directory.
    Supports atomic writes and backup before overwrite.
    Includes automatic backup rotation to prevent unbounded disk usage.

    Attributes:
        storage_dir: Directory where sessions are stored.
    """

    DEFAULT_DIR_NAME = "sessions"
    SESSION_EXTENSION = ".json"
    BACKUP_EXTENSION = ".backup"
    MAX_BACKUPS = 100  # Maximum number of backup files to keep
    BACKUP_MAX_AGE_DAYS = 7  # Maximum age of backup files in days

    def __init__(self, storage_dir: Path | str | None = None) -> None:
        """Initialize session storage.

        Args:
            storage_dir: Directory for session files. Uses default if None.
        """
        if storage_dir is None:
            storage_dir = self.get_default_dir()
        elif isinstance(storage_dir, str):
            storage_dir = Path(storage_dir)

        self.storage_dir = storage_dir
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Create storage directory if it doesn't exist."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        # Set secure permissions (owner only)
        try:
            os.chmod(self.storage_dir, 0o700)
        except OSError:
            pass  # May fail on some systems

    @classmethod
    def get_default_dir(cls) -> Path:
        """Get the default session storage directory.

        Returns:
            Path to default storage directory.
        """
        # Use XDG_DATA_HOME if available, else ~/.local/share
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            base = Path(xdg_data)
        else:
            base = Path.home() / ".local" / "share"

        return base / "forge" / cls.DEFAULT_DIR_NAME

    @classmethod
    def get_project_dir(cls, project_root: Path | str) -> Path:
        """Get the project-local session storage directory.

        Args:
            project_root: Root directory of the project.

        Returns:
            Path to project session directory.
        """
        if isinstance(project_root, str):
            project_root = Path(project_root)
        return project_root / ".forge" / cls.DEFAULT_DIR_NAME

    def get_path(self, session_id: str) -> Path:
        """Get the file path for a session.

        Args:
            session_id: The session ID.

        Returns:
            Path to the session file.
        """
        return self.storage_dir / f"{session_id}{self.SESSION_EXTENSION}"

    def get_backup_path(self, session_id: str) -> Path:
        """Get the backup file path for a session.

        Args:
            session_id: The session ID.

        Returns:
            Path to the backup file.
        """
        return self.storage_dir / f"{session_id}{self.BACKUP_EXTENSION}"

    def exists(self, session_id: str) -> bool:
        """Check if a session exists in storage.

        Args:
            session_id: The session ID to check.

        Returns:
            True if the session exists.
        """
        return self.get_path(session_id).exists()

    def save(self, session: "Session") -> None:
        """Save a session to storage.

        Uses atomic write (write to temp file, then rename) for safety.
        Creates a backup of the existing file before overwrite.

        Args:
            session: The session to save.

        Raises:
            SessionStorageError: If save fails.
        """
        from .models import Session

        session_path = self.get_path(session.id)
        backup_path = self.get_backup_path(session.id)

        # Create backup if file exists
        if session_path.exists():
            try:
                shutil.copy2(session_path, backup_path)
            except OSError as e:
                logger.warning(f"Failed to create backup: {e}")

        # Serialize session
        try:
            json_data = session.to_json()
        except Exception as e:
            raise SessionStorageError(f"Failed to serialize session: {e}") from e

        # Atomic write: write to temp file, then rename
        try:
            fd, temp_path = tempfile.mkstemp(
                suffix=self.SESSION_EXTENSION,
                dir=self.storage_dir,
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(json_data)

                # Rename temp file to target (atomic on POSIX)
                os.replace(temp_path, session_path)

                # Set secure permissions
                try:
                    os.chmod(session_path, 0o600)
                except OSError:
                    pass

            except Exception:
                # Clean up temp file on failure
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise

        except OSError as e:
            raise SessionStorageError(f"Failed to save session: {e}") from e

        logger.debug(f"Saved session {session.id}")

    def load(self, session_id: str) -> "Session":
        """Load a session from storage.

        Args:
            session_id: The session ID to load.

        Returns:
            The loaded Session.

        Raises:
            SessionNotFoundError: If session doesn't exist.
            SessionCorruptedError: If session file is corrupted.
        """
        from .models import Session

        session_path = self.get_path(session_id)

        if not session_path.exists():
            raise SessionNotFoundError(f"Session not found: {session_id}")

        try:
            with open(session_path, "r", encoding="utf-8") as f:
                json_data = f.read()

            session = Session.from_json(json_data)
            logger.debug(f"Loaded session {session_id}")
            return session

        except json.JSONDecodeError as e:
            raise SessionCorruptedError(
                f"Session file corrupted: {session_id}"
            ) from e
        except Exception as e:
            raise SessionStorageError(
                f"Failed to load session: {e}"
            ) from e

    def load_or_none(self, session_id: str) -> "Session | None":
        """Load a session, returning None if not found or corrupted.

        Args:
            session_id: The session ID to load.

        Returns:
            The loaded Session, or None if unavailable.
        """
        try:
            return self.load(session_id)
        except SessionStorageError as e:
            logger.warning(f"Failed to load session {session_id}: {e}")
            return None

    def delete(self, session_id: str) -> bool:
        """Delete a session from storage.

        Also removes any backup file.

        Args:
            session_id: The session ID to delete.

        Returns:
            True if session was deleted, False if it didn't exist.
        """
        session_path = self.get_path(session_id)
        backup_path = self.get_backup_path(session_id)

        deleted = False

        if session_path.exists():
            try:
                session_path.unlink()
                deleted = True
                logger.debug(f"Deleted session {session_id}")
            except OSError as e:
                logger.error(f"Failed to delete session: {e}")

        if backup_path.exists():
            try:
                backup_path.unlink()
            except OSError:
                pass

        return deleted

    def list_session_ids(self) -> list[str]:
        """List all session IDs in storage.

        Returns:
            List of session IDs.
        """
        session_ids = []

        for path in self.storage_dir.glob(f"*{self.SESSION_EXTENSION}"):
            session_id = path.stem
            session_ids.append(session_id)

        return session_ids

    def recover_from_backup(self, session_id: str) -> bool:
        """Recover a session from its backup file.

        Args:
            session_id: The session ID to recover.

        Returns:
            True if recovery succeeded.
        """
        session_path = self.get_path(session_id)
        backup_path = self.get_backup_path(session_id)

        if not backup_path.exists():
            return False

        try:
            shutil.copy2(backup_path, session_path)
            logger.info(f"Recovered session {session_id} from backup")
            return True
        except OSError as e:
            logger.error(f"Failed to recover session: {e}")
            return False

    def get_storage_size(self) -> int:
        """Get total size of all session files in bytes.

        Returns:
            Total size in bytes.
        """
        total = 0
        for path in self.storage_dir.glob(f"*{self.SESSION_EXTENSION}"):
            try:
                total += path.stat().st_size
            except OSError:
                pass
        return total

    def cleanup_old_sessions(
        self,
        max_age_days: int = 30,
        keep_minimum: int = 10,
    ) -> list[str]:
        """Delete sessions older than a certain age.

        Args:
            max_age_days: Maximum age in days.
            keep_minimum: Minimum number of sessions to keep.

        Returns:
            List of deleted session IDs.
        """
        from datetime import timedelta
        from .models import Session

        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)

        # Load all sessions with their dates
        sessions_with_dates: list[tuple[str, datetime]] = []

        for session_id in self.list_session_ids():
            session = self.load_or_none(session_id)
            if session:
                sessions_with_dates.append((session_id, session.updated_at))

        # Sort by date (newest first)
        sessions_with_dates.sort(key=lambda x: x[1], reverse=True)

        # Delete old sessions, keeping minimum
        deleted = []
        for i, (session_id, updated_at) in enumerate(sessions_with_dates):
            if i < keep_minimum:
                continue  # Keep minimum sessions

            if updated_at < cutoff:
                if self.delete(session_id):
                    deleted.append(session_id)

        if deleted:
            logger.info(f"Cleaned up {len(deleted)} old sessions")

        return deleted

    def cleanup_old_backups(self) -> int:
        """Remove old backup files to prevent unbounded disk usage.

        Removes backups that:
        - Are older than BACKUP_MAX_AGE_DAYS
        - Exceed MAX_BACKUPS count (oldest first)

        Returns:
            Number of backup files deleted.
        """
        from datetime import timedelta

        deleted_count = 0
        cutoff_time = time.time() - (self.BACKUP_MAX_AGE_DAYS * 24 * 3600)

        # Get all backup files with modification times
        backups: list[tuple[Path, float]] = []
        for path in self.storage_dir.glob(f"*{self.BACKUP_EXTENSION}"):
            try:
                mtime = path.stat().st_mtime
                backups.append((path, mtime))
            except OSError:
                continue

        # Sort by modification time (oldest first)
        backups.sort(key=lambda x: x[1])

        # Delete old backups (by age)
        for path, mtime in backups:
            if mtime < cutoff_time:
                try:
                    path.unlink()
                    deleted_count += 1
                except OSError:
                    pass

        # Re-fetch remaining backups
        remaining = [
            (p, m) for p, m in backups
            if p.exists()
        ]

        # Delete excess backups (by count, oldest first)
        excess_count = len(remaining) - self.MAX_BACKUPS
        if excess_count > 0:
            for path, _ in remaining[:excess_count]:
                try:
                    path.unlink()
                    deleted_count += 1
                except OSError:
                    pass

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old backup files")

        return deleted_count


# Import datetime and time for cleanup methods
from datetime import datetime, timezone
import time
```

---

## File 3: src/forge/sessions/index.py

```python
"""Session index for fast listing and search."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import Session
    from .storage import SessionStorage

logger = logging.getLogger(__name__)


@dataclass
class SessionSummary:
    """Summary of a session for listing.

    Contains key metadata without full message history.
    """

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    total_tokens: int
    tags: list[str] = field(default_factory=list)
    working_dir: str = ""
    model: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "tags": self.tags,
            "working_dir": self.working_dir,
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionSummary":
        """Deserialize from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.now(timezone.utc)

        return cls(
            id=data["id"],
            title=data.get("title", ""),
            created_at=created_at,
            updated_at=updated_at,
            message_count=data.get("message_count", 0),
            total_tokens=data.get("total_tokens", 0),
            tags=data.get("tags", []),
            working_dir=data.get("working_dir", ""),
            model=data.get("model", ""),
        )

    @classmethod
    def from_session(cls, session: "Session") -> "SessionSummary":
        """Create summary from a full Session.

        Args:
            session: The session to summarize.

        Returns:
            SessionSummary instance.
        """
        return cls(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=session.message_count,
            total_tokens=session.total_tokens,
            tags=list(session.tags),
            working_dir=session.working_dir,
            model=session.model,
        )


class SessionIndex:
    """Index of sessions for fast lookup and filtering.

    Maintains an in-memory index backed by a JSON file for
    fast session listing without loading full session files.

    Attributes:
        storage: The SessionStorage instance.
        _index: In-memory index data.
        _dirty: Whether index needs to be saved.
    """

    INDEX_FILE = "index.json"
    INDEX_VERSION = 1

    def __init__(self, storage: "SessionStorage") -> None:
        """Initialize session index.

        Args:
            storage: SessionStorage instance to use.
        """
        self.storage = storage
        self._index: dict[str, SessionSummary] = {}
        self._dirty = False
        self._load_index()

    @property
    def index_path(self) -> Path:
        """Path to the index file."""
        return self.storage.storage_dir / self.INDEX_FILE

    def _load_index(self) -> None:
        """Load index from disk."""
        if not self.index_path.exists():
            logger.debug("No index file, starting fresh")
            return

        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            version = data.get("version", 0)
            if version != self.INDEX_VERSION:
                logger.info(f"Index version mismatch, rebuilding")
                self.rebuild()
                return

            sessions = data.get("sessions", {})
            for session_id, summary_data in sessions.items():
                summary_data["id"] = session_id
                self._index[session_id] = SessionSummary.from_dict(summary_data)

            logger.debug(f"Loaded index with {len(self._index)} sessions")

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to load index, rebuilding: {e}")
            self.rebuild()

    def _save_index(self) -> None:
        """Save index to disk."""
        data = {
            "version": self.INDEX_VERSION,
            "sessions": {
                sid: summary.to_dict()
                for sid, summary in self._index.items()
            },
        }

        try:
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._dirty = False
            logger.debug(f"Saved index with {len(self._index)} sessions")
        except OSError as e:
            logger.error(f"Failed to save index: {e}")

    def rebuild(self) -> None:
        """Rebuild the index from session files.

        Reads all session files to create fresh index data.
        """
        self._index.clear()

        for session_id in self.storage.list_session_ids():
            session = self.storage.load_or_none(session_id)
            if session:
                self._index[session_id] = SessionSummary.from_session(session)

        self._dirty = True
        self._save_index()
        logger.info(f"Rebuilt index with {len(self._index)} sessions")

    def add(self, session: "Session") -> None:
        """Add or update a session in the index.

        Args:
            session: The session to add.
        """
        self._index[session.id] = SessionSummary.from_session(session)
        self._dirty = True

    def update(self, session: "Session") -> None:
        """Update a session in the index.

        Args:
            session: The session to update.
        """
        self.add(session)  # Same operation

    def remove(self, session_id: str) -> bool:
        """Remove a session from the index.

        Args:
            session_id: The session ID to remove.

        Returns:
            True if session was in index.
        """
        if session_id in self._index:
            del self._index[session_id]
            self._dirty = True
            return True
        return False

    def get(self, session_id: str) -> SessionSummary | None:
        """Get a session summary by ID.

        Args:
            session_id: The session ID.

        Returns:
            SessionSummary or None if not found.
        """
        return self._index.get(session_id)

    def count(self) -> int:
        """Get the number of indexed sessions.

        Returns:
            Number of sessions.
        """
        return len(self._index)

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "updated_at",
        descending: bool = True,
        tags: list[str] | None = None,
        search: str | None = None,
        working_dir: str | None = None,
    ) -> list[SessionSummary]:
        """List sessions with filtering and pagination.

        Args:
            limit: Maximum number of sessions to return.
            offset: Number of sessions to skip.
            sort_by: Field to sort by (updated_at, created_at, title).
            descending: Sort in descending order.
            tags: Filter to sessions with all these tags.
            search: Search string for title matching.
            working_dir: Filter to sessions in this directory.

        Returns:
            List of SessionSummary objects.
        """
        # Filter sessions
        summaries = list(self._index.values())

        if tags:
            summaries = [
                s for s in summaries
                if all(tag in s.tags for tag in tags)
            ]

        if search:
            search_lower = search.lower()
            summaries = [
                s for s in summaries
                if search_lower in s.title.lower()
            ]

        if working_dir:
            summaries = [
                s for s in summaries
                if s.working_dir == working_dir
            ]

        # Sort
        sort_key = {
            "updated_at": lambda s: s.updated_at,
            "created_at": lambda s: s.created_at,
            "title": lambda s: s.title.lower(),
            "message_count": lambda s: s.message_count,
            "total_tokens": lambda s: s.total_tokens,
        }.get(sort_by, lambda s: s.updated_at)

        summaries.sort(key=sort_key, reverse=descending)

        # Paginate
        return summaries[offset : offset + limit]

    def get_recent(self, count: int = 10) -> list[SessionSummary]:
        """Get the most recently updated sessions.

        Args:
            count: Number of sessions to return.

        Returns:
            List of SessionSummary objects.
        """
        return self.list(limit=count, sort_by="updated_at", descending=True)

    def get_by_working_dir(self, working_dir: str) -> list[SessionSummary]:
        """Get sessions for a specific working directory.

        Args:
            working_dir: The working directory path.

        Returns:
            List of SessionSummary objects.
        """
        return self.list(working_dir=working_dir, limit=1000)

    def save_if_dirty(self) -> None:
        """Save the index if it has been modified."""
        if self._dirty:
            self._save_index()

    def __len__(self) -> int:
        """Number of indexed sessions."""
        return len(self._index)

    def __contains__(self, session_id: str) -> bool:
        """Check if session is in index."""
        return session_id in self._index
```

---

## File 4: src/forge/sessions/manager.py

```python
"""Session lifecycle management."""

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .index import SessionIndex, SessionSummary
from .models import Session, SessionMessage, ToolInvocation
from .storage import SessionStorage, SessionNotFoundError

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages session lifecycle.

    Central manager for creating, resuming, saving, and listing
    sessions. Provides auto-save functionality and session hooks.

    Attributes:
        storage: SessionStorage instance.
        index: SessionIndex instance.
        current_session: Currently active session, if any.
    """

    _instance: "SessionManager | None" = None

    def __init__(
        self,
        storage: SessionStorage | None = None,
        auto_save_interval: float = 60.0,
    ) -> None:
        """Initialize session manager.

        Args:
            storage: SessionStorage instance. Creates default if None.
            auto_save_interval: Auto-save interval in seconds. 0 to disable.
        """
        self.storage = storage or SessionStorage()
        self.index = SessionIndex(self.storage)
        self.current_session: Session | None = None

        self._auto_save_interval = auto_save_interval
        self._auto_save_task: asyncio.Task | None = None
        self._hooks: dict[str, list[Callable]] = {
            "session:start": [],
            "session:end": [],
            "session:message": [],
            "session:save": [],
        }

    @classmethod
    def get_instance(cls) -> "SessionManager":
        """Get the singleton SessionManager instance.

        Returns:
            The SessionManager singleton.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        if cls._instance is not None:
            cls._instance.close()
        cls._instance = None

    def create(
        self,
        *,
        title: str = "",
        working_dir: str | None = None,
        model: str = "",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        """Create a new session.

        Args:
            title: Session title. Auto-generated if empty.
            working_dir: Working directory. Uses cwd if None.
            model: LLM model to use.
            tags: Initial tags.
            metadata: Initial metadata.

        Returns:
            The new Session.
        """
        if working_dir is None:
            working_dir = os.getcwd()

        session = Session(
            title=title,
            working_dir=working_dir,
            model=model,
            tags=tags or [],
            metadata=metadata or {},
        )

        # Save immediately
        self.storage.save(session)
        self.index.add(session)
        self.index.save_if_dirty()

        # Set as current and start auto-save
        self.current_session = session
        self._start_auto_save()

        # Fire hooks
        self._fire_hook("session:start", session)

        logger.info(f"Created session {session.id}")
        return session

    def resume(self, session_id: str) -> Session:
        """Resume an existing session.

        Args:
            session_id: The session ID to resume.

        Returns:
            The resumed Session.

        Raises:
            SessionNotFoundError: If session doesn't exist.
        """
        session = self.storage.load(session_id)

        # Update access time
        session._mark_updated()
        self.storage.save(session)
        self.index.update(session)
        self.index.save_if_dirty()

        # Set as current and start auto-save
        self.current_session = session
        self._start_auto_save()

        # Fire hooks
        self._fire_hook("session:start", session)

        logger.info(f"Resumed session {session.id}")
        return session

    def resume_latest(self) -> Session | None:
        """Resume the most recently updated session.

        Returns:
            The resumed Session, or None if no sessions exist.
        """
        recent = self.index.get_recent(count=1)
        if not recent:
            return None

        try:
            return self.resume(recent[0].id)
        except SessionNotFoundError:
            # Index was stale, rebuild and try again
            self.index.rebuild()
            recent = self.index.get_recent(count=1)
            if recent:
                return self.resume(recent[0].id)
            return None

    def resume_or_create(
        self,
        *,
        working_dir: str | None = None,
        model: str = "",
    ) -> Session:
        """Resume the latest session or create a new one.

        Args:
            working_dir: Working directory for new session.
            model: Model for new session.

        Returns:
            A Session (existing or new).
        """
        session = self.resume_latest()
        if session is None:
            session = self.create(working_dir=working_dir, model=model)
        return session

    def save(self, session: Session | None = None) -> None:
        """Save a session.

        Args:
            session: The session to save. Uses current if None.
        """
        if session is None:
            session = self.current_session

        if session is None:
            logger.warning("No session to save")
            return

        self.storage.save(session)
        self.index.update(session)
        self.index.save_if_dirty()

        self._fire_hook("session:save", session)
        logger.debug(f"Saved session {session.id}")

    def close(self, session: Session | None = None) -> None:
        """Close a session.

        Saves the session and stops auto-save if it's the current session.

        Args:
            session: The session to close. Uses current if None.
        """
        if session is None:
            session = self.current_session

        if session is None:
            return

        # Save final state
        self.save(session)

        # Fire hooks
        self._fire_hook("session:end", session)

        # Stop auto-save if closing current session
        if session is self.current_session:
            self._stop_auto_save()
            self.current_session = None

        logger.info(f"Closed session {session.id}")

    def delete(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: The session ID to delete.

        Returns:
            True if session was deleted.
        """
        # Close if it's the current session
        if self.current_session and self.current_session.id == session_id:
            self._stop_auto_save()
            self.current_session = None

        # Remove from storage and index
        deleted = self.storage.delete(session_id)
        self.index.remove(session_id)
        self.index.save_if_dirty()

        if deleted:
            logger.info(f"Deleted session {session_id}")

        return deleted

    def list_sessions(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "updated_at",
        descending: bool = True,
        tags: list[str] | None = None,
        search: str | None = None,
    ) -> list[SessionSummary]:
        """List sessions with filtering and pagination.

        Args:
            limit: Maximum number of sessions.
            offset: Number to skip.
            sort_by: Sort field.
            descending: Sort direction.
            tags: Filter by tags.
            search: Search string.

        Returns:
            List of SessionSummary objects.
        """
        return self.index.list(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            descending=descending,
            tags=tags,
            search=search,
        )

    def get_session(self, session_id: str) -> Session | None:
        """Get a full session by ID.

        Args:
            session_id: The session ID.

        Returns:
            The Session, or None if not found.
        """
        return self.storage.load_or_none(session_id)

    def add_message(
        self,
        role: str,
        content: str,
        session: Session | None = None,
        **kwargs: Any,
    ) -> SessionMessage:
        """Add a message to a session.

        Args:
            role: Message role.
            content: Message content.
            session: Target session. Uses current if None.
            **kwargs: Additional message fields.

        Returns:
            The created SessionMessage.

        Raises:
            ValueError: If no session is available.
        """
        if session is None:
            session = self.current_session

        if session is None:
            raise ValueError("No session available")

        message = session.add_message_from_dict(role, content, **kwargs)

        self._fire_hook("session:message", session, message)

        return message

    def record_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any] | None = None,
        duration: float = 0.0,
        success: bool = True,
        error: str | None = None,
        session: Session | None = None,
    ) -> ToolInvocation:
        """Record a tool invocation.

        Args:
            tool_name: Name of the tool.
            arguments: Tool arguments.
            result: Tool result.
            duration: Execution duration.
            success: Whether successful.
            error: Error message if failed.
            session: Target session. Uses current if None.

        Returns:
            The created ToolInvocation.

        Raises:
            ValueError: If no session is available.
        """
        if session is None:
            session = self.current_session

        if session is None:
            raise ValueError("No session available")

        return session.record_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            duration=duration,
            success=success,
            error=error,
        )

    def update_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        session: Session | None = None,
    ) -> None:
        """Update token usage.

        Args:
            prompt_tokens: Prompt tokens used.
            completion_tokens: Completion tokens used.
            session: Target session. Uses current if None.
        """
        if session is None:
            session = self.current_session

        if session:
            session.update_usage(prompt_tokens, completion_tokens)

    def generate_title(self, session: Session) -> str:
        """Generate a title for a session.

        Uses the first user message to generate a title.
        Falls back to timestamp-based title.

        Args:
            session: The session to title.

        Returns:
            The generated title.
        """
        # Find first user message
        for msg in session.messages:
            if msg.role == "user" and msg.content:
                # Use first line, truncated
                title = msg.content.split("\n")[0]
                if len(title) > 50:
                    title = title[:47] + "..."
                return title

        # Fallback to timestamp
        return f"Session {session.created_at.strftime('%Y-%m-%d %H:%M')}"

    def set_title(self, title: str, session: Session | None = None) -> None:
        """Set session title.

        Args:
            title: The new title.
            session: Target session. Uses current if None.
        """
        if session is None:
            session = self.current_session

        if session:
            session.title = title
            session._mark_updated()

    def add_tag(self, tag: str, session: Session | None = None) -> None:
        """Add a tag to a session.

        Args:
            tag: The tag to add.
            session: Target session. Uses current if None.
        """
        if session is None:
            session = self.current_session

        if session and tag not in session.tags:
            session.tags.append(tag)
            session._mark_updated()

    def remove_tag(self, tag: str, session: Session | None = None) -> bool:
        """Remove a tag from a session.

        Args:
            tag: The tag to remove.
            session: Target session. Uses current if None.

        Returns:
            True if tag was removed.
        """
        if session is None:
            session = self.current_session

        if session and tag in session.tags:
            session.tags.remove(tag)
            session._mark_updated()
            return True
        return False

    @property
    def has_current(self) -> bool:
        """Check if there's a current session."""
        return self.current_session is not None

    def register_hook(self, event: str, callback: Callable) -> None:
        """Register a session lifecycle hook.

        Args:
            event: Event name (session:start, session:end, etc.)
            callback: Callback function.
        """
        if event in self._hooks:
            self._hooks[event].append(callback)

    def unregister_hook(self, event: str, callback: Callable) -> bool:
        """Unregister a session lifecycle hook.

        Args:
            event: Event name.
            callback: Callback to remove.

        Returns:
            True if callback was removed.
        """
        if event in self._hooks and callback in self._hooks[event]:
            self._hooks[event].remove(callback)
            return True
        return False

    def _fire_hook(self, event: str, *args: Any) -> None:
        """Fire registered hooks for an event.

        Args:
            event: Event name.
            *args: Arguments to pass to callbacks.
        """
        for callback in self._hooks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logger.error(f"Hook error for {event}: {e}")

    def _start_auto_save(self) -> None:
        """Start the auto-save task."""
        if self._auto_save_interval <= 0:
            return

        self._stop_auto_save()

        async def auto_save_loop():
            try:
                while True:
                    await asyncio.sleep(self._auto_save_interval)
                    if self.current_session:
                        try:
                            self.save(self.current_session)
                        except Exception as e:
                            # Log but don't crash auto-save loop
                            logger.warning(f"Auto-save failed: {e}")
            except asyncio.CancelledError:
                # Clean cancellation is expected
                pass

        try:
            loop = asyncio.get_running_loop()
            self._auto_save_task = loop.create_task(auto_save_loop())
        except RuntimeError:
            # No running loop, skip auto-save
            pass

    def _stop_auto_save(self) -> None:
        """Stop the auto-save task."""
        if self._auto_save_task:
            self._auto_save_task.cancel()
            # Don't await - could block, and cancellation is fire-and-forget
            self._auto_save_task = None

    def __del__(self) -> None:
        """Cleanup: ensure auto-save is stopped and session is saved."""
        self._stop_auto_save()
        # Note: can't do async save in __del__, but that's ok - we trust
        # close() was called properly before destruction
```

---

## File 5: src/forge/sessions/__init__.py

```python
"""Session management package.

This package provides session persistence and management for Code-Forge.
Sessions store conversation history, tool invocations, and metadata.

Example:
    from forge.sessions import SessionManager

    manager = SessionManager.get_instance()

    # Create new session
    session = manager.create(title="My session", model="anthropic/claude-3-opus")

    # Add messages
    manager.add_message("user", "Hello!")
    manager.add_message("assistant", "Hi there!")

    # Save and close
    manager.close()

    # Later, resume
    session = manager.resume(session.id)
"""

from .models import Session, SessionMessage, ToolInvocation
from .storage import (
    SessionStorage,
    SessionStorageError,
    SessionNotFoundError,
    SessionCorruptedError,
)
from .index import SessionIndex, SessionSummary
from .manager import SessionManager

__all__ = [
    # Models
    "Session",
    "SessionMessage",
    "ToolInvocation",
    # Storage
    "SessionStorage",
    "SessionStorageError",
    "SessionNotFoundError",
    "SessionCorruptedError",
    # Index
    "SessionIndex",
    "SessionSummary",
    # Manager
    "SessionManager",
]
```

---

## Integration Notes

### With LangChain Integration (Phase 3.2)

```python
# Memory backed by session
from forge.sessions import SessionManager
from forge.langchain.memory import ConversationMemory

manager = SessionManager.get_instance()
session = manager.create()

# Sync session messages with memory
memory = ConversationMemory()
for msg in session.messages:
    if msg.role == "user":
        memory.add_user_message(msg.content)
    elif msg.role == "assistant":
        memory.add_ai_message(msg.content)
```

### With Hooks System (Phase 4.2)

```python
# Fire session events
from forge.hooks import fire_event, HookEvent

async def on_session_start(session):
    event = HookEvent.session_start(session.id)
    await fire_event(event)

manager = SessionManager.get_instance()
manager.register_hook("session:start", on_session_start)
```

---

## Testing Strategy

1. **Unit Tests** - Test each class in isolation
2. **Integration Tests** - Test storage + index + manager together
3. **Persistence Tests** - Test save/load round-trips
4. **Concurrency Tests** - Test auto-save behavior

---

## Next Steps

After implementing Phase 5.1:
1. Verify all tests pass
2. Run type checking with mypy
3. Proceed to Phase 5.2 (Context Management)
