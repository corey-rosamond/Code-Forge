# Phase 9.1: Git Integration - Requirements

**Phase:** 9.1
**Name:** Git Integration
**Dependencies:** Phase 2.3 (Execution Tools), Phase 2.1 (Tool System)

---

## Overview

Phase 9.1 implements Git integration for OpenCode, enabling the assistant to work with Git repositories, understand version control context, and perform common Git operations safely. This provides awareness of the codebase state and enables collaborative workflows.

---

## Goals

1. Detect and understand Git repository context
2. Provide Git status and history information
3. Enable safe Git operations (commit, branch, etc.)
4. Support diff analysis and change review
5. Implement safety guards for destructive operations
6. Enable Git-aware code exploration

---

## Non-Goals (This Phase)

- Full Git GUI replacement
- Complex merge conflict resolution
- Git submodule management
- Git LFS support
- Custom Git hooks management
- Git server operations

---

## Functional Requirements

### FR-1: Repository Detection

**FR-1.1:** Repository awareness
- Detect if working directory is Git repo
- Find repository root directory
- Handle nested repositories
- Support bare repositories (limited)

**FR-1.2:** Repository information
- Current branch name
- Remote configuration
- Repository status (clean/dirty)
- HEAD commit info

**FR-1.3:** Context integration
- Provide Git context to LLM
- Include branch in system prompt
- Track dirty state

### FR-2: Git Status

**FR-2.1:** Working tree status
- Staged changes
- Unstaged changes
- Untracked files
- Ignored files (optional)

**FR-2.2:** Branch status
- Ahead/behind remote
- Tracking branch info
- Diverged status

**FR-2.3:** Status formatting
- Human-readable output
- Structured data for tools
- Diff statistics

### FR-3: Git History

**FR-3.1:** Commit log
- Recent commits
- Commit messages
- Author and date
- Commit hashes

**FR-3.2:** Log filtering
- By file path
- By author
- By date range
- By branch

**FR-3.3:** Commit details
- Full commit message
- Changed files
- Diff content
- Parent commits

### FR-4: Git Diff

**FR-4.1:** Diff types
- Working tree vs HEAD
- Staged vs HEAD
- Between commits
- Between branches

**FR-4.2:** Diff options
- Context lines
- Ignore whitespace
- File filtering
- Stat summary

**FR-4.3:** Diff presentation
- Unified format
- Side-by-side (optional)
- File list only

### FR-5: Git Operations

**FR-5.1:** Staging operations
- Stage files (add)
- Unstage files
- Stage hunks (interactive)

**FR-5.2:** Commit operations
- Create commits
- Amend commits (with guards)
- Commit message formatting

**FR-5.3:** Branch operations
- List branches
- Create branches
- Switch branches
- Delete branches (with guards)

**FR-5.4:** Remote operations
- Fetch from remote
- Pull changes
- Push changes (with guards)

### FR-6: Safety Guards

**FR-6.1:** Dangerous operation protection
- No force push without explicit request
- No hard reset without confirmation
- No branch deletion without confirmation

**FR-6.2:** Commit safety
- Verify commit authorship before amend
- Check if commits are pushed
- Warn about amending public commits

**FR-6.3:** Configuration protection
- Never modify git config automatically
- Don't skip hooks without explicit request
- Preserve user's commit signing settings

---

## Non-Functional Requirements

### NFR-1: Performance
- Git status < 1s for typical repos
- Log queries < 500ms
- Diff generation < 2s

### NFR-2: Safety
- Never lose uncommitted work
- Confirm destructive operations
- Clear error messages

### NFR-3: Compatibility
- Git version 2.20+
- Standard Git workflows
- Common Git configurations

---

## Technical Specifications

### Package Structure

```
src/opencode/git/
├── __init__.py           # Package exports
├── repository.py         # Git repository interface
├── status.py             # Status operations
├── history.py            # Log and history
├── diff.py               # Diff operations
├── operations.py         # Git operations (commit, branch, etc.)
├── safety.py             # Safety guards
└── context.py            # Git context for LLM
```

### Class Signatures

```python
# repository.py
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitRemote:
    """Git remote information."""
    name: str
    url: str
    fetch_url: str | None = None
    push_url: str | None = None


@dataclass
class GitBranch:
    """Git branch information."""
    name: str
    is_current: bool
    tracking: str | None = None
    ahead: int = 0
    behind: int = 0
    commit: str | None = None


@dataclass
class GitCommit:
    """Git commit information."""
    hash: str
    short_hash: str
    author: str
    author_email: str
    date: str
    message: str
    parent_hashes: list[str]


@dataclass
class RepositoryInfo:
    """Git repository information."""
    root: Path
    is_git_repo: bool
    current_branch: str | None
    head_commit: GitCommit | None
    is_dirty: bool
    remotes: list[GitRemote]


class GitRepository:
    """Interface to a Git repository."""

    def __init__(self, path: Path | None = None):
        """Initialize repository at path or current directory."""
        ...

    @property
    def is_git_repo(self) -> bool:
        """Check if path is a Git repository."""
        ...

    @property
    def root(self) -> Path:
        """Get repository root directory."""
        ...

    @property
    def current_branch(self) -> str | None:
        """Get current branch name."""
        ...

    @property
    def is_dirty(self) -> bool:
        """Check if working tree has uncommitted changes."""
        ...

    def get_info(self) -> RepositoryInfo:
        """Get repository information."""
        ...

    def get_remotes(self) -> list[GitRemote]:
        """Get list of remotes."""
        ...

    def get_branches(self, all: bool = False) -> list[GitBranch]:
        """Get list of branches."""
        ...

    async def run_git(
        self,
        *args: str,
        check: bool = True
    ) -> tuple[str, str, int]:
        """Run git command and return (stdout, stderr, returncode)."""
        ...


# status.py
@dataclass
class FileStatus:
    """Status of a single file."""
    path: str
    status: str  # M, A, D, R, C, U, ?
    staged: bool
    original_path: str | None = None  # For renames


@dataclass
class GitStatus:
    """Complete git status."""
    branch: str | None
    tracking: str | None
    ahead: int
    behind: int
    staged: list[FileStatus]
    unstaged: list[FileStatus]
    untracked: list[FileStatus]
    conflicts: list[FileStatus]

    @property
    def is_clean(self) -> bool:
        """Check if working tree is clean."""
        ...

    def to_string(self) -> str:
        """Format as human-readable string."""
        ...


class GitStatusTool:
    """Git status operations."""

    def __init__(self, repo: GitRepository):
        self.repo = repo

    async def get_status(self) -> GitStatus:
        """Get current git status."""
        ...

    async def get_staged_diff(self) -> str:
        """Get diff of staged changes."""
        ...

    async def get_unstaged_diff(self) -> str:
        """Get diff of unstaged changes."""
        ...


# history.py
@dataclass
class LogEntry:
    """Single log entry."""
    commit: GitCommit
    files_changed: int | None = None
    insertions: int | None = None
    deletions: int | None = None


class GitHistory:
    """Git history operations."""

    def __init__(self, repo: GitRepository):
        self.repo = repo

    async def get_log(
        self,
        count: int = 10,
        path: str | None = None,
        author: str | None = None,
        since: str | None = None,
        until: str | None = None,
        branch: str | None = None
    ) -> list[LogEntry]:
        """Get commit log."""
        ...

    async def get_commit(self, ref: str) -> GitCommit:
        """Get single commit details."""
        ...

    async def get_commit_files(self, ref: str) -> list[str]:
        """Get files changed in commit."""
        ...

    async def get_commit_diff(self, ref: str) -> str:
        """Get diff for commit."""
        ...


# diff.py
@dataclass
class DiffFile:
    """Diff for a single file."""
    path: str
    old_path: str | None  # For renames
    status: str  # A, M, D, R
    additions: int
    deletions: int
    content: str | None = None


@dataclass
class GitDiff:
    """Complete diff result."""
    files: list[DiffFile]
    total_additions: int
    total_deletions: int
    stat: str

    def to_string(self, include_content: bool = True) -> str:
        """Format as string."""
        ...


class GitDiffTool:
    """Git diff operations."""

    def __init__(self, repo: GitRepository):
        self.repo = repo

    async def diff_working(
        self,
        path: str | None = None,
        staged: bool = False
    ) -> GitDiff:
        """Diff working tree vs HEAD."""
        ...

    async def diff_commits(
        self,
        from_ref: str,
        to_ref: str,
        path: str | None = None
    ) -> GitDiff:
        """Diff between commits."""
        ...

    async def diff_branches(
        self,
        from_branch: str,
        to_branch: str
    ) -> GitDiff:
        """Diff between branches."""
        ...


# operations.py
class GitOperations:
    """Git operations with safety guards."""

    def __init__(self, repo: GitRepository, safety: "GitSafety"):
        self.repo = repo
        self.safety = safety

    # Staging
    async def stage(self, paths: list[str]) -> None:
        """Stage files for commit."""
        ...

    async def unstage(self, paths: list[str]) -> None:
        """Unstage files."""
        ...

    async def stage_all(self) -> None:
        """Stage all changes."""
        ...

    # Commits
    async def commit(
        self,
        message: str,
        amend: bool = False
    ) -> GitCommit:
        """Create a commit."""
        ...

    # Branches
    async def create_branch(
        self,
        name: str,
        start_point: str | None = None
    ) -> GitBranch:
        """Create a branch."""
        ...

    async def switch_branch(self, name: str) -> None:
        """Switch to a branch."""
        ...

    async def delete_branch(
        self,
        name: str,
        force: bool = False
    ) -> None:
        """Delete a branch."""
        ...

    # Remote
    async def fetch(self, remote: str = "origin") -> None:
        """Fetch from remote."""
        ...

    async def pull(self, remote: str = "origin") -> None:
        """Pull from remote."""
        ...

    async def push(
        self,
        remote: str = "origin",
        branch: str | None = None,
        set_upstream: bool = False
    ) -> None:
        """Push to remote."""
        ...


# safety.py
@dataclass
class SafetyCheck:
    """Result of safety check."""
    safe: bool
    reason: str | None = None
    warnings: list[str] = None


class GitSafety:
    """Safety guards for Git operations."""

    def __init__(self, repo: GitRepository):
        self.repo = repo

    async def check_amend(self) -> SafetyCheck:
        """Check if amend is safe."""
        ...

    async def check_force_push(self) -> SafetyCheck:
        """Check if force push is safe."""
        ...

    async def check_branch_delete(self, branch: str) -> SafetyCheck:
        """Check if branch delete is safe."""
        ...

    async def check_hard_reset(self) -> SafetyCheck:
        """Check if hard reset is safe."""
        ...

    async def get_head_authorship(self) -> tuple[str, str]:
        """Get author name and email of HEAD commit."""
        ...

    async def is_pushed(self, ref: str = "HEAD") -> bool:
        """Check if commit is pushed to remote."""
        ...


# context.py
class GitContext:
    """Git context for LLM."""

    def __init__(self, repo: GitRepository):
        self.repo = repo

    def get_context_summary(self) -> str:
        """Get Git context summary for system prompt."""
        ...

    def get_status_summary(self) -> str:
        """Get brief status summary."""
        ...

    def format_for_commit(self, staged_diff: str) -> str:
        """Format staged changes for commit message generation."""
        ...
```

---

## Git Commands

| Command | Description |
|---------|-------------|
| `/git` | Show git status |
| `/git status` | Detailed status |
| `/git log` | Recent commits |
| `/git diff` | Show working diff |
| `/git branches` | List branches |
| `/git commit` | Commit staged changes |

---

## Integration Points

### With Tool System (Phase 2.1)
- Git tools registered
- Tool schemas for LLM

### With Execution Tools (Phase 2.3)
- Git commands via Bash
- Process management

### With Session (Phase 5.1)
- Repository state in session
- Branch tracking

### With Permission System (Phase 4.1)
- Git operations permissions
- Dangerous operation confirmation

---

## Testing Requirements

1. Unit tests for GitRepository
2. Unit tests for status parsing
3. Unit tests for log parsing
4. Unit tests for diff parsing
5. Unit tests for operations
6. Unit tests for safety guards
7. Integration tests with real repo
8. Test coverage ≥ 90%

---

## Acceptance Criteria

1. Detects Git repository correctly
2. Shows accurate status
3. Log displays correctly
4. Diff works for all modes
5. Commit creates valid commits
6. Branch operations work
7. Safety guards prevent mistakes
8. Context provided to LLM
9. Error handling is graceful
10. Performance is acceptable
