# Phase 9.1: Git Integration - Completion Criteria

**Phase:** 9.1
**Name:** Git Integration
**Dependencies:** Phase 2.3 (Execution Tools), Phase 2.1 (Tool System)

---

## Completion Checklist

### 1. Data Types (repository.py)

- [ ] `GitRemote` dataclass implemented
  - [ ] `name: str`
  - [ ] `url: str`
  - [ ] `fetch_url: str | None`
  - [ ] `push_url: str | None`

- [ ] `GitBranch` dataclass implemented
  - [ ] `name: str`
  - [ ] `is_current: bool`
  - [ ] `tracking: str | None`
  - [ ] `ahead: int`
  - [ ] `behind: int`
  - [ ] `commit: str | None`

- [ ] `GitCommit` dataclass implemented
  - [ ] `hash: str`
  - [ ] `short_hash: str`
  - [ ] `author: str`
  - [ ] `author_email: str`
  - [ ] `date: str`
  - [ ] `message: str`
  - [ ] `parent_hashes: list[str]`

- [ ] `RepositoryInfo` dataclass implemented
  - [ ] `root: Path`
  - [ ] `is_git_repo: bool`
  - [ ] `current_branch: str | None`
  - [ ] `head_commit: GitCommit | None`
  - [ ] `is_dirty: bool`
  - [ ] `remotes: list[GitRemote]`

### 2. GitRepository Class (repository.py)

- [ ] `GitRepository` class implemented
  - [ ] `__init__(path: Path | None)` initializer
  - [ ] `is_git_repo` property (cached)
  - [ ] `root` property (finds repo root)
  - [ ] `current_branch` property
  - [ ] `is_dirty` property
  - [ ] `get_info()` method
  - [ ] `get_remotes()` method
  - [ ] `get_branches(all)` method
  - [ ] `run_git(*args)` async method

- [ ] Repository detection features
  - [ ] Detect git repository from any subdirectory
  - [ ] Find repository root correctly
  - [ ] Handle non-git directories gracefully
  - [ ] Cache detection results

### 3. Git Status (status.py)

- [ ] `FileStatus` dataclass implemented
  - [ ] `path: str`
  - [ ] `status: str` (M, A, D, R, C, U, ?)
  - [ ] `staged: bool`
  - [ ] `original_path: str | None`

- [ ] `GitStatus` dataclass implemented
  - [ ] `branch: str | None`
  - [ ] `tracking: str | None`
  - [ ] `ahead: int`
  - [ ] `behind: int`
  - [ ] `staged: list[FileStatus]`
  - [ ] `unstaged: list[FileStatus]`
  - [ ] `untracked: list[FileStatus]`
  - [ ] `conflicts: list[FileStatus]`
  - [ ] `is_clean` property
  - [ ] `to_string()` method

- [ ] `GitStatusTool` class implemented
  - [ ] `get_status()` async method
  - [ ] `get_staged_diff()` async method
  - [ ] `get_unstaged_diff()` async method
  - [ ] Parses porcelain v2 format correctly

### 4. Git History (history.py)

- [ ] `LogEntry` dataclass implemented
  - [ ] `commit: GitCommit`
  - [ ] `files_changed: int | None`
  - [ ] `insertions: int | None`
  - [ ] `deletions: int | None`

- [ ] `GitHistory` class implemented
  - [ ] `get_log(count, path, author, since, until, branch)` async method
  - [ ] `get_commit(ref)` async method
  - [ ] `get_commit_files(ref)` async method
  - [ ] `get_commit_diff(ref)` async method

- [ ] Log filtering features
  - [ ] Filter by file path
  - [ ] Filter by author
  - [ ] Filter by date range
  - [ ] Filter by branch

### 5. Git Diff (diff.py)

- [ ] `DiffFile` dataclass implemented
  - [ ] `path: str`
  - [ ] `old_path: str | None`
  - [ ] `status: str` (A, M, D, R)
  - [ ] `additions: int`
  - [ ] `deletions: int`
  - [ ] `content: str | None`

- [ ] `GitDiff` dataclass implemented
  - [ ] `files: list[DiffFile]`
  - [ ] `total_additions: int`
  - [ ] `total_deletions: int`
  - [ ] `stat: str`
  - [ ] `to_string(include_content)` method

- [ ] `GitDiffTool` class implemented
  - [ ] `diff_working(path, staged)` async method
  - [ ] `diff_commits(from_ref, to_ref, path)` async method
  - [ ] `diff_branches(from_branch, to_branch)` async method

### 6. Git Operations (operations.py)

- [ ] `GitOperations` class implemented
  - [ ] Constructor takes `GitRepository` and `GitSafety`

- [ ] Staging operations
  - [ ] `stage(paths)` async method
  - [ ] `unstage(paths)` async method
  - [ ] `stage_all()` async method

- [ ] Commit operations
  - [ ] `commit(message, amend)` async method
  - [ ] Amend checks safety before proceeding
  - [ ] Returns `GitCommit` on success

- [ ] Branch operations
  - [ ] `create_branch(name, start_point)` async method
  - [ ] `switch_branch(name)` async method
  - [ ] `delete_branch(name, force)` async method
  - [ ] Delete checks safety before proceeding

- [ ] Remote operations
  - [ ] `fetch(remote)` async method
  - [ ] `pull(remote)` async method
  - [ ] `push(remote, branch, set_upstream)` async method

### 7. Safety Guards (safety.py)

- [ ] `SafetyCheck` dataclass implemented
  - [ ] `safe: bool`
  - [ ] `reason: str | None`
  - [ ] `warnings: list[str]`

- [ ] `GitSafety` class implemented
  - [ ] `check_amend()` async method
  - [ ] `check_force_push()` async method
  - [ ] `check_branch_delete(branch)` async method
  - [ ] `check_hard_reset()` async method
  - [ ] `get_head_authorship()` async method
  - [ ] `is_pushed(ref)` async method

- [ ] Safety features
  - [ ] Prevents amend of pushed commits
  - [ ] Prevents amend of other author's commits
  - [ ] Warns about force push consequences
  - [ ] Warns about uncommitted changes on reset
  - [ ] Verifies branch merge status before delete

### 8. Git Context (context.py)

- [ ] `GitContext` class implemented
  - [ ] `get_context_summary()` method
  - [ ] `get_status_summary()` method
  - [ ] `format_for_commit(staged_diff)` method

- [ ] Context integration
  - [ ] Provides branch info to system prompt
  - [ ] Includes dirty state indication
  - [ ] Formats staged changes for commit message generation

### 9. Package Exports (__init__.py)

- [ ] All data types exported
- [ ] `GitRepository` exported
- [ ] `GitStatusTool` exported
- [ ] `GitHistory` exported
- [ ] `GitDiffTool` exported
- [ ] `GitOperations` exported
- [ ] `GitSafety` exported
- [ ] `GitContext` exported
- [ ] `__all__` list complete

### 10. Integration

- [ ] Git context provided in session system prompt
- [ ] Git commands registered as slash commands
- [ ] `/git` command shows status
- [ ] `/git status` shows detailed status
- [ ] `/git log` shows recent commits
- [ ] `/git diff` shows working tree diff
- [ ] `/git branches` lists branches
- [ ] `/git commit` commits staged changes

### 11. Testing

- [ ] Unit tests for GitRepository
- [ ] Unit tests for GitStatus parsing
- [ ] Unit tests for GitHistory
- [ ] Unit tests for GitDiff parsing
- [ ] Unit tests for GitOperations (mocked)
- [ ] Unit tests for GitSafety
- [ ] Unit tests for GitContext
- [ ] Integration tests with real git repo
- [ ] Test coverage >= 90%

### 12. Code Quality

- [ ] McCabe complexity <= 10 for all functions
- [ ] Type hints on all public methods
- [ ] Docstrings on all public classes/methods
- [ ] No circular imports
- [ ] Follows project code style

---

## Verification Commands

```bash
# Run unit tests
pytest tests/git/ -v

# Run with coverage
pytest tests/git/ --cov=src/forge/git --cov-report=term-missing

# Check coverage threshold
pytest tests/git/ --cov=src/forge/git --cov-fail-under=90

# Type checking
mypy src/forge/git/

# Complexity check
flake8 src/forge/git/ --max-complexity=10
```

---

## Test Scenarios

### Repository Detection Tests

```python
def test_detect_git_repo(tmp_path):
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=tmp_path)

    repo = GitRepository(tmp_path)
    assert repo.is_git_repo is True
    assert repo.root == tmp_path


def test_detect_non_git_directory(tmp_path):
    repo = GitRepository(tmp_path)
    assert repo.is_git_repo is False


def test_find_root_from_subdirectory(tmp_path):
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=tmp_path)

    # Create subdirectory
    subdir = tmp_path / "src" / "components"
    subdir.mkdir(parents=True)

    repo = GitRepository(subdir)
    assert repo.root == tmp_path
```

### Status Parsing Tests

```python
async def test_parse_clean_status():
    tool = GitStatusTool(mock_repo)
    status = await tool.get_status()

    assert status.is_clean is True
    assert status.staged == []
    assert status.unstaged == []


async def test_parse_staged_files():
    tool = GitStatusTool(mock_repo)
    status = await tool.get_status()

    assert len(status.staged) == 2
    assert status.staged[0].path == "new_file.py"
    assert status.staged[0].status == "A"
    assert status.staged[0].staged is True


async def test_parse_renamed_file():
    tool = GitStatusTool(mock_repo)
    status = await tool.get_status()

    renamed = status.staged[0]
    assert renamed.status == "R"
    assert renamed.original_path == "old_name.py"
    assert renamed.path == "new_name.py"
```

### Safety Guard Tests

```python
async def test_amend_safe_when_not_pushed():
    safety = GitSafety(mock_repo)
    # Mock is_pushed to return False
    result = await safety.check_amend()

    assert result.safe is True


async def test_amend_unsafe_when_pushed():
    safety = GitSafety(mock_repo)
    # Mock is_pushed to return True
    result = await safety.check_amend()

    assert result.safe is False
    assert "pushed" in result.reason.lower()


async def test_amend_unsafe_different_author():
    safety = GitSafety(mock_repo)
    # Mock get_head_authorship to return different author
    result = await safety.check_amend()

    assert result.safe is False
    assert "author" in result.reason.lower()
```

### Diff Parsing Tests

```python
async def test_diff_working_tree():
    tool = GitDiffTool(mock_repo)
    diff = await tool.diff_working()

    assert len(diff.files) == 2
    assert diff.total_additions > 0
    assert diff.total_deletions >= 0


async def test_diff_between_commits():
    tool = GitDiffTool(mock_repo)
    diff = await tool.diff_commits("abc123", "def456")

    assert diff.stat is not None
    for file in diff.files:
        assert file.additions >= 0
        assert file.deletions >= 0
```

### Git Operations Tests

```python
async def test_stage_files(mock_repo):
    ops = GitOperations(mock_repo, mock_safety)
    await ops.stage(["file1.py", "file2.py"])

    # Verify git add was called
    mock_repo.run_git.assert_called_with("add", "file1.py", "file2.py")


async def test_commit_creates_commit(mock_repo):
    ops = GitOperations(mock_repo, mock_safety)
    commit = await ops.commit("Test message")

    assert commit.message == "Test message"
    mock_repo.run_git.assert_called()


async def test_commit_amend_checks_safety(mock_repo, mock_safety):
    mock_safety.check_amend.return_value = SafetyCheck(
        safe=False, reason="Commit is pushed"
    )

    ops = GitOperations(mock_repo, mock_safety)

    with pytest.raises(GitError) as exc:
        await ops.commit("Amend", amend=True)

    assert "pushed" in str(exc.value).lower()
```

---

## Definition of Done

Phase 9.1 is complete when:

1. All checklist items are checked off
2. All unit tests pass
3. Test coverage is >= 90%
4. Code complexity is <= 10
5. Type checking passes with no errors
6. Repository detection works correctly
7. Status parsing handles all file states
8. Log retrieval works with filters
9. Diff generation works for all modes
10. Staging operations work correctly
11. Commit operations include safety checks
12. Branch operations work safely
13. Remote operations work correctly
14. Safety guards prevent destructive operations
15. Git context is provided to LLM
16. Slash commands work correctly
17. Error handling is graceful
18. Documentation is complete
19. Code review approved

---

## Dependencies Verification

Before starting Phase 9.1, verify:

- [ ] Phase 2.1 (Tool System) is complete
  - [ ] Tool interface available
  - [ ] Tool registration works

- [ ] Phase 2.3 (Execution Tools) is complete
  - [ ] Bash tool can run git commands
  - [ ] Async subprocess execution works

- [ ] Phase 6.1 (Slash Commands) is complete
  - [ ] Slash command registration works
  - [ ] Commands can be added

---

## Git Version Compatibility

Tested with:
- Git 2.20+
- Git 2.30+
- Git 2.40+

Required git features:
- `git status --porcelain=v2` (Git 2.11+)
- `git branch --show-current` (Git 2.22+)
- Standard git operations

---

## Performance Requirements

| Operation | Max Time |
|-----------|----------|
| Repository detection | 100ms |
| Status (typical repo) | 1s |
| Log query (10 commits) | 500ms |
| Diff (working tree) | 2s |
| Commit | 2s |
| Branch operations | 500ms |

---

## Notes

- All git operations use async subprocess execution
- Porcelain format used for reliable parsing
- Safety checks run before destructive operations
- Never modify git config automatically
- Respect user's git hooks and signing settings
- Cache repository state where appropriate
- Handle large repositories gracefully
