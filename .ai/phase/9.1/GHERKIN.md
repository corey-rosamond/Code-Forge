# Phase 9.1: Git Integration - Gherkin Specifications

**Phase:** 9.1
**Name:** Git Integration
**Dependencies:** Phase 2.3 (Execution Tools), Phase 2.1 (Tool System)

---

## Feature: Repository Detection

### Scenario: Detect Git repository
```gherkin
Given a directory that is a Git repository
When I create GitRepository with that path
Then is_git_repo should return True
And root should return the repository root path
```

### Scenario: Detect non-Git directory
```gherkin
Given a directory that is not a Git repository
When I create GitRepository with that path
Then is_git_repo should return False
```

### Scenario: Find repository root from subdirectory
```gherkin
Given a Git repository at /project
And current directory is /project/src/components
When I create GitRepository with current directory
Then root should return /project
```

### Scenario: Get current branch
```gherkin
Given a Git repository on branch "feature-x"
When I access current_branch property
Then it should return "feature-x"
```

### Scenario: Detached HEAD state
```gherkin
Given a Git repository in detached HEAD state
When I access current_branch property
Then it should return None
```

### Scenario: Get repository information
```gherkin
Given a Git repository with changes
When I call get_info()
Then it should return RepositoryInfo
And info should contain root path
And info should contain current branch
And info should contain is_dirty status
And info should contain remotes
```

---

## Feature: Git Status

### Scenario: Get status of clean repository
```gherkin
Given a Git repository with no changes
When I call get_status()
Then status.is_clean should be True
And status.staged should be empty
And status.unstaged should be empty
And status.untracked should be empty
```

### Scenario: Get status with staged files
```gherkin
Given a Git repository
And file "new.txt" is staged
When I call get_status()
Then status.staged should contain FileStatus for "new.txt"
And FileStatus.staged should be True
```

### Scenario: Get status with unstaged changes
```gherkin
Given a Git repository
And file "existing.txt" has unstaged changes
When I call get_status()
Then status.unstaged should contain FileStatus for "existing.txt"
And FileStatus.status should be "M"
```

### Scenario: Get status with untracked files
```gherkin
Given a Git repository
And file "new-file.txt" is not tracked
When I call get_status()
Then status.untracked should contain FileStatus for "new-file.txt"
And FileStatus.status should be "?"
```

### Scenario: Get status with renamed file
```gherkin
Given a Git repository
And file "old.txt" is renamed to "new.txt" and staged
When I call get_status()
Then status.staged should contain FileStatus for "new.txt"
And FileStatus.original_path should be "old.txt"
And FileStatus.status should be "R"
```

### Scenario: Get status with conflict
```gherkin
Given a Git repository with merge conflict
When I call get_status()
Then status.conflicts should not be empty
And conflict FileStatus.status should be "U"
```

### Scenario: Get branch tracking info
```gherkin
Given a Git repository on branch "main"
And main tracks origin/main
And local is 2 commits ahead
When I call get_status()
Then status.tracking should be "origin/main"
And status.ahead should be 2
And status.behind should be 0
```

### Scenario: Format status as string
```gherkin
Given a GitStatus with staged and unstaged files
When I call to_string()
Then output should include "On branch" line
And output should include "Changes to be committed"
And output should include "Changes not staged"
```

---

## Feature: Git History

### Scenario: Get recent commits
```gherkin
Given a Git repository with 20 commits
When I call get_log(count=10)
Then result should contain 10 LogEntry items
And entries should be in reverse chronological order
```

### Scenario: Get log for specific file
```gherkin
Given a Git repository
And file "app.py" has 5 commits
When I call get_log(path="app.py")
Then result should contain commits affecting "app.py"
```

### Scenario: Get log by author
```gherkin
Given a Git repository with commits from multiple authors
When I call get_log(author="alice@example.com")
Then all results should have author_email "alice@example.com"
```

### Scenario: Get log by date range
```gherkin
Given a Git repository with commits spanning months
When I call get_log(since="2024-01-01", until="2024-01-31")
Then all commits should be within January 2024
```

### Scenario: Get log for branch
```gherkin
Given a Git repository with branches "main" and "feature"
When I call get_log(branch="feature")
Then result should show commits from feature branch
```

### Scenario: Get single commit details
```gherkin
Given a Git repository
And commit "abc123" exists
When I call get_commit("abc123")
Then result should be GitCommit
And commit.hash should start with "abc123"
And commit should have message, author, date
```

### Scenario: Get files changed in commit
```gherkin
Given a Git repository
And commit "abc123" changed 3 files
When I call get_commit_files("abc123")
Then result should contain 3 file paths
```

### Scenario: Get diff for commit
```gherkin
Given a Git repository
And commit "abc123" has changes
When I call get_commit_diff("abc123")
Then result should contain unified diff
And diff should show additions and deletions
```

---

## Feature: Git Diff

### Scenario: Diff working tree
```gherkin
Given a Git repository
And file "app.py" has unstaged changes
When I call diff_working()
Then result should be GitDiff
And diff.files should contain DiffFile for "app.py"
```

### Scenario: Diff staged changes
```gherkin
Given a Git repository
And file "app.py" has staged changes
When I call diff_working(staged=True)
Then diff should show staged changes only
```

### Scenario: Diff specific file
```gherkin
Given a Git repository with multiple changed files
When I call diff_working(path="app.py")
Then diff should only include "app.py"
```

### Scenario: Diff between commits
```gherkin
Given commits "abc123" and "def456"
When I call diff_commits("abc123", "def456")
Then result should show changes between commits
And diff.files should list changed files
```

### Scenario: Diff between branches
```gherkin
Given branches "main" and "feature"
When I call diff_branches("main", "feature")
Then result should show changes in feature vs main
```

### Scenario: Diff statistics
```gherkin
Given a GitDiff result
Then diff.total_additions should be sum of all additions
And diff.total_deletions should be sum of all deletions
And diff.stat should be formatted stat summary
```

### Scenario: Format diff as string
```gherkin
Given a GitDiff with file changes
When I call to_string(include_content=True)
Then output should include file headers
And output should include diff content
And output should include +/- statistics
```

---

## Feature: Git Staging

### Scenario: Stage single file
```gherkin
Given a Git repository
And "app.py" has unstaged changes
When I call stage(["app.py"])
Then "app.py" should be staged
And status.staged should include "app.py"
```

### Scenario: Stage multiple files
```gherkin
Given a Git repository
And files "a.py", "b.py", "c.py" have changes
When I call stage(["a.py", "b.py", "c.py"])
Then all three files should be staged
```

### Scenario: Stage all changes
```gherkin
Given a Git repository with multiple changed files
When I call stage_all()
Then all changes should be staged
And status.unstaged should be empty
```

### Scenario: Unstage file
```gherkin
Given a Git repository
And "app.py" is staged
When I call unstage(["app.py"])
Then "app.py" should no longer be staged
And changes should still exist in working tree
```

### Scenario: Stage non-existent file fails
```gherkin
Given a Git repository
When I call stage(["nonexistent.py"])
Then GitError should be raised
And error should indicate file not found
```

---

## Feature: Git Commit

### Scenario: Create commit
```gherkin
Given a Git repository
And files are staged
When I call commit("Add new feature")
Then new commit should be created
And result should be GitCommit
And commit.message should be "Add new feature"
```

### Scenario: Commit with empty message fails
```gherkin
Given a Git repository with staged files
When I call commit("")
Then error should be raised
And error should mention empty message
```

### Scenario: Commit with nothing staged fails
```gherkin
Given a Git repository with no staged changes
When I call commit("Test")
Then error should be raised
And error should indicate nothing to commit
```

### Scenario: Amend commit safely
```gherkin
Given a Git repository
And HEAD commit is not pushed
And HEAD commit is by current user
And files are staged
When I call commit("Updated message", amend=True)
Then HEAD commit should be amended
And commit message should be updated
```

### Scenario: Amend pushed commit requires confirmation
```gherkin
Given a Git repository
And HEAD commit is pushed to remote
When I call commit("Fix", amend=True)
Then SafetyCheck should fail
And error should mention pushed commit
```

### Scenario: Amend other author's commit fails
```gherkin
Given a Git repository
And HEAD commit is by different author
When I call commit("Fix", amend=True)
Then SafetyCheck should fail
And error should mention authorship
```

---

## Feature: Branch Operations

### Scenario: List branches
```gherkin
Given a Git repository with branches "main", "develop", "feature"
When I call get_branches()
Then result should contain 3 branches
And current branch should have is_current=True
```

### Scenario: List all branches including remote
```gherkin
Given a Git repository with remote branches
When I call get_branches(all=True)
Then result should include remote tracking branches
```

### Scenario: Create branch
```gherkin
Given a Git repository on main branch
When I call create_branch("feature-new")
Then new branch "feature-new" should be created
And result should be GitBranch
```

### Scenario: Create branch from specific commit
```gherkin
Given a Git repository
And commit "abc123" exists
When I call create_branch("hotfix", start_point="abc123")
Then new branch should start from "abc123"
```

### Scenario: Switch branch
```gherkin
Given a Git repository
And branch "develop" exists
When I call switch_branch("develop")
Then current branch should be "develop"
```

### Scenario: Switch to non-existent branch fails
```gherkin
Given a Git repository
When I call switch_branch("nonexistent")
Then error should be raised
And error should indicate branch not found
```

### Scenario: Delete merged branch
```gherkin
Given a Git repository
And branch "feature" is merged into main
When I call delete_branch("feature")
Then branch should be deleted
```

### Scenario: Delete unmerged branch requires force
```gherkin
Given a Git repository
And branch "feature" has unmerged commits
When I call delete_branch("feature", force=False)
Then error should be raised
And error should mention unmerged changes
```

### Scenario: Force delete unmerged branch
```gherkin
Given a Git repository
And branch "feature" has unmerged commits
When I call delete_branch("feature", force=True)
Then branch should be deleted
```

### Scenario: Delete current branch fails
```gherkin
Given a Git repository on branch "feature"
When I call delete_branch("feature")
Then error should be raised
And error should indicate cannot delete current branch
```

---

## Feature: Remote Operations

### Scenario: Fetch from remote
```gherkin
Given a Git repository with remote "origin"
When I call fetch()
Then remote refs should be updated
```

### Scenario: Fetch from specific remote
```gherkin
Given a Git repository with remotes "origin" and "upstream"
When I call fetch(remote="upstream")
Then only upstream refs should be fetched
```

### Scenario: Pull changes
```gherkin
Given a Git repository
And remote has new commits
When I call pull()
Then new commits should be integrated
```

### Scenario: Pull with uncommitted changes fails
```gherkin
Given a Git repository with uncommitted changes
When I call pull()
Then error should be raised
And error should mention uncommitted changes
```

### Scenario: Push to remote
```gherkin
Given a Git repository
And local has commits to push
When I call push()
Then commits should be pushed to remote
```

### Scenario: Push with set upstream
```gherkin
Given a Git repository on new branch "feature"
When I call push(set_upstream=True)
Then branch should be pushed
And tracking should be set up
```

### Scenario: Push to specific remote
```gherkin
Given a Git repository with multiple remotes
When I call push(remote="upstream")
Then changes should go to upstream
```

---

## Feature: Safety Guards

### Scenario: Check amend safety - safe
```gherkin
Given HEAD commit is not pushed
And HEAD commit is by current user
When I call check_amend()
Then result should be SafetyCheck(safe=True)
```

### Scenario: Check amend safety - pushed
```gherkin
Given HEAD commit is pushed to remote
When I call check_amend()
Then result should be SafetyCheck(safe=False)
And reason should mention "already pushed"
```

### Scenario: Check amend safety - different author
```gherkin
Given HEAD commit is by different author
When I call check_amend()
Then result should be SafetyCheck(safe=False)
And reason should mention authorship
```

### Scenario: Check force push safety
```gherkin
Given local and remote have diverged
When I call check_force_push()
Then result should be SafetyCheck(safe=False)
And warnings should mention "will overwrite remote"
```

### Scenario: Check hard reset safety
```gherkin
Given repository has uncommitted changes
When I call check_hard_reset()
Then result should be SafetyCheck(safe=False)
And reason should mention "uncommitted changes"
```

### Scenario: Check branch delete safety - merged
```gherkin
Given branch "feature" is fully merged
When I call check_branch_delete("feature")
Then result should be SafetyCheck(safe=True)
```

### Scenario: Check branch delete safety - unmerged
```gherkin
Given branch "feature" has unmerged commits
When I call check_branch_delete("feature")
Then result should be SafetyCheck(safe=False)
And reason should mention "unmerged commits"
```

### Scenario: Get HEAD authorship
```gherkin
Given HEAD commit by "Alice <alice@example.com>"
When I call get_head_authorship()
Then result should be ("Alice", "alice@example.com")
```

### Scenario: Check if commit is pushed
```gherkin
Given commit "abc123" exists on origin/main
When I call is_pushed("abc123")
Then result should be True
```

### Scenario: Check if local commit is pushed
```gherkin
Given commit "abc123" only exists locally
When I call is_pushed("abc123")
Then result should be False
```

---

## Feature: Git Context for LLM

### Scenario: Get context summary
```gherkin
Given a Git repository on branch "feature"
And repository has uncommitted changes
When I call get_context_summary()
Then result should include branch name
And result should indicate dirty state
And result should be suitable for system prompt
```

### Scenario: Get status summary
```gherkin
Given a Git repository with 3 staged, 2 unstaged files
When I call get_status_summary()
Then result should be brief status line
And should mention file counts
```

### Scenario: Format staged changes for commit
```gherkin
Given staged diff content
When I call format_for_commit(staged_diff)
Then result should be formatted for LLM
And should highlight what's being committed
```

---

## Feature: Error Handling

### Scenario: Handle git not installed
```gherkin
Given git is not installed on system
When I create GitRepository
Then appropriate error should be raised
And error should suggest installing git
```

### Scenario: Handle git command failure
```gherkin
Given a git command that fails
When run_git() is called
Then GitError should be raised
And error should contain stderr output
```

### Scenario: Handle permission denied
```gherkin
Given a repository without read permission
When I try to access it
Then error should indicate permission issue
```

### Scenario: Handle corrupt repository
```gherkin
Given a corrupted Git repository
When I try to get status
Then error should be handled gracefully
And error message should be informative
```

---

## Feature: Performance

### Scenario: Status under 1 second
```gherkin
Given a typical Git repository (< 10000 files)
When I call get_status()
Then operation should complete in < 1 second
```

### Scenario: Log query under 500ms
```gherkin
Given a Git repository with 1000+ commits
When I call get_log(count=10)
Then operation should complete in < 500ms
```

### Scenario: Diff generation under 2 seconds
```gherkin
Given a Git repository with significant changes
When I call diff_working()
Then operation should complete in < 2 seconds
```

### Scenario: Cache repository detection
```gherkin
Given repeated access to is_git_repo
When I access the property multiple times
Then git command should only run once
And cached value should be returned
```
