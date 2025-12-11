"""Git integration for Code-Forge."""

from .context import GitContext
from .diff import DiffFile, GitDiff, GitDiffTool
from .history import GitHistory, LogEntry
from .operations import GitOperations, UnsafeOperationError
from .repository import (
    GitBranch,
    GitCommit,
    GitError,
    GitRemote,
    GitRepository,
    RepositoryInfo,
)
from .safety import GitSafety, SafetyCheck
from .status import FileStatus, GitStatus, GitStatusTool

__all__ = [
    "DiffFile",
    "FileStatus",
    "GitBranch",
    "GitCommit",
    "GitContext",
    "GitDiff",
    "GitDiffTool",
    "GitError",
    "GitHistory",
    "GitOperations",
    "GitRemote",
    "GitRepository",
    "GitSafety",
    "GitStatus",
    "GitStatusTool",
    "LogEntry",
    "RepositoryInfo",
    "SafetyCheck",
    "UnsafeOperationError",
]
