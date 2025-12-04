# Phase 9.1: Git Integration - Wireframes & Usage Examples

**Phase:** 9.1
**Name:** Git Integration
**Dependencies:** Phase 2.3 (Execution Tools), Phase 2.1 (Tool System)

---

## 1. Git Status Display

### Basic Status

```
You: What's the git status?

On branch: feature/new-auth
Tracking: origin/feature/new-auth (2 ahead, 0 behind)

Changes to be committed:
  M  src/auth/login.py
  A  src/auth/oauth.py

Changes not staged for commit:
  M  src/config.py
  M  tests/test_auth.py

Untracked files:
  .env.local
  notes.md

3 files staged, 2 files modified, 2 files untracked
```

### Clean Repository

```
You: git status

On branch: main
Tracking: origin/main (up to date)

Working tree is clean. Nothing to commit.
```

### Merge Conflict Status

```
You: What's going on with my repo?

On branch: feature/refactor
Merging: main into feature/refactor

CONFLICTS (2 files):
  UU src/core/handler.py
  UU src/utils/parser.py

Changes to be committed:
  M  src/core/engine.py

Fix conflicts and run 'git add' to mark resolution.
```

---

## 2. Git Log Display

### Recent Commits

```
You: Show me recent commits

Recent commits on main:

abc1234 (HEAD -> main, origin/main)
  Author: Alice <alice@example.com>
  Date:   2024-01-15 14:32
  Add user authentication module

def5678
  Author: Bob <bob@example.com>
  Date:   2024-01-15 10:15
  Fix database connection timeout issue

789abcd
  Author: Alice <alice@example.com>
  Date:   2024-01-14 16:45
  Refactor API endpoints for v2

...showing 3 of 10 commits
```

### File History

```
You: Show commit history for src/auth/login.py

Commits affecting src/auth/login.py:

abc1234 (2024-01-15)
  Add user authentication module
  +145 -0 lines

def5678 (2024-01-10)
  Add basic login validation
  +32 -5 lines

789abcd (2024-01-05)
  Initial login implementation
  +89 -0 lines

3 commits found
```

### Commit Details

```
You: Show details for commit abc1234

Commit: abc1234def5678901234567890abcdef12345678
Author: Alice <alice@example.com>
Date:   Mon Jan 15 14:32:00 2024 -0500
Parent: def5678

    Add user authentication module

    - Implement OAuth2 flow
    - Add session management
    - Include rate limiting

Files changed (4):
  src/auth/login.py      | +145 -0
  src/auth/oauth.py      | +234 -0
  src/auth/session.py    | +89  -12
  tests/test_auth.py     | +156 -0

 4 files changed, 624 insertions(+), 12 deletions(-)
```

---

## 3. Git Diff Display

### Working Tree Diff

```
You: Show me what changed

Diff: working tree vs HEAD

src/config.py
─────────────────────────────────────
@@ -15,7 +15,8 @@ class Config:
     timeout: int = 30
     max_retries: int = 3
+    enable_cache: bool = True
+    cache_ttl: int = 300

tests/test_auth.py
─────────────────────────────────────
@@ -45,6 +45,15 @@ class TestLogin:
     def test_invalid_password(self):
         result = login("user", "wrong")
         assert result.error == "invalid_credentials"
+
+    def test_rate_limiting(self):
+        for i in range(10):
+            login("user", "wrong")
+        result = login("user", "wrong")
+        assert result.error == "rate_limited"

Summary: 2 files, +11 insertions, -0 deletions
```

### Staged Diff

```
You: What's staged for commit?

Staged changes (to be committed):

src/auth/login.py
─────────────────────────────────────
@@ -1,5 +1,6 @@
 from typing import Optional
+from datetime import datetime

 class LoginHandler:
     def __init__(self, config):
@@ -23,6 +24,12 @@ class LoginHandler:
         if not self._validate(password):
             return LoginResult(error="invalid_credentials")
+
+        # Log successful login
+        self._log_login(username, datetime.now())

         return LoginResult(success=True, token=self._generate_token())

src/auth/oauth.py (new file)
─────────────────────────────────────
+"""OAuth2 authentication handler."""
+
+class OAuth2Handler:
+    """Handle OAuth2 authentication flow."""
+
+    def __init__(self, client_id: str, client_secret: str):
+        self.client_id = client_id
...

Summary: 2 files staged, +178 insertions
```

### Branch Diff

```
You: Compare feature branch with main

Diff: main...feature/new-auth

12 files changed, 847 insertions(+), 23 deletions(-)

src/auth/login.py        | +145 -0
src/auth/oauth.py        | +234 -0  (new)
src/auth/session.py      | +189 -12
src/auth/validators.py   | +78  -0  (new)
src/config.py            | +15  -3
src/core/middleware.py   | +45  -8
tests/test_auth.py       | +156 -0  (new)
tests/test_session.py    | +85  -0  (new)

Would you like to see the full diff for any file?
```

---

## 4. Git Operations

### Staging Files

```
You: Stage the config and test files

Staged 2 files:
  + src/config.py
  + tests/test_auth.py

Current staging area:
  M  src/auth/login.py
  A  src/auth/oauth.py
  M  src/config.py
  M  tests/test_auth.py
```

### Creating Commits

```
You: Commit these changes with message "Add caching configuration"

[main abc1234] Add caching configuration
 4 files changed, 178 insertions(+)
 create mode 100644 src/auth/oauth.py

Committed by: You <you@example.com>
Date: Mon Jan 15 15:45:00 2024

Would you like to push this commit?
```

### Amend Commit

```
You: Amend the last commit to include the test file

Checking safety for amend...
✓ HEAD commit is not pushed
✓ HEAD commit is by you

[main abc1234] Add caching configuration
 5 files changed, 234 insertions(+)

Commit amended successfully.
```

### Amend Warning

```
You: Amend the commit

⚠️ Cannot amend safely:

The HEAD commit has already been pushed to origin/main.
Amending would rewrite history that others may have pulled.

Options:
1. Create a new commit instead
2. Force amend (may cause issues for collaborators)

How would you like to proceed?
```

---

## 5. Branch Operations

### List Branches

```
You: Show me all branches

Local branches:
* main                    abc1234 [origin/main]
  feature/new-auth        def5678 [origin/feature/new-auth: 2 ahead]
  feature/refactor        789abcd [origin/feature/refactor]
  bugfix/login-error      456def0

Remote branches:
  origin/main
  origin/feature/new-auth
  origin/feature/refactor
  origin/develop

4 local, 4 remote branches
```

### Create Branch

```
You: Create a new branch called feature/dark-mode

Created branch 'feature/dark-mode' at abc1234

Branch: feature/dark-mode
From:   main (abc1234)

Switch to this branch? [y/n]
```

### Switch Branch

```
You: Switch to the develop branch

Switched to branch 'develop'
Your branch is up to date with 'origin/develop'.

On branch: develop
Status: clean
```

### Delete Branch

```
You: Delete the bugfix/login-error branch

Checking branch safety...
✓ Branch 'bugfix/login-error' is fully merged into main

Deleted branch bugfix/login-error (was 456def0).
```

### Delete Unmerged Branch Warning

```
You: Delete feature/experimental

⚠️ Branch 'feature/experimental' is not fully merged.

Unmerged commits:
  abc1234 - Add experimental feature
  def5678 - WIP: testing new approach

Deleting will lose these 2 commits.

Force delete anyway? [y/n]
```

---

## 6. Remote Operations

### Fetch

```
You: Fetch latest from remote

Fetching from origin...

remote: Enumerating objects: 15, done.
remote: Counting objects: 100% (15/15), done.
remote: Compressing objects: 100% (8/8), done.

From github.com:user/project
   abc1234..def5678  main       -> origin/main
 * [new branch]      feature/x  -> origin/feature/x

Fetch complete. Your local branches:
  main: 3 commits behind origin/main
```

### Pull

```
You: Pull latest changes

Pulling from origin/main...

Updating abc1234..def5678
Fast-forward
 src/core/engine.py | 45 ++++++++++++++++++++
 src/utils/helper.py | 12 +++---
 2 files changed, 52 insertions(+), 5 deletions(-)

Your branch is now up to date with 'origin/main'.
```

### Pull with Uncommitted Changes

```
You: Pull the latest

⚠️ Cannot pull: You have uncommitted changes

Modified files:
  M  src/config.py
  M  tests/test_auth.py

Options:
1. Commit your changes first
2. Stash your changes (git stash)
3. Discard your changes (will lose work!)

What would you like to do?
```

### Push

```
You: Push my changes

Pushing to origin/feature/new-auth...

Enumerating objects: 12, done.
Counting objects: 100% (12/12), done.
Delta compression using up to 8 threads
Compressing objects: 100% (8/8), done.
Writing objects: 100% (8/8), 2.34 KiB | 2.34 MiB/s, done.

To github.com:user/project.git
   def5678..abc1234  feature/new-auth -> feature/new-auth

Push complete. Branch is up to date with remote.
```

### Push New Branch

```
You: Push this branch

Branch 'feature/dark-mode' has no upstream.

Setting upstream to origin/feature/dark-mode...

To github.com:user/project.git
 * [new branch]      feature/dark-mode -> feature/dark-mode

Branch 'feature/dark-mode' set up to track 'origin/feature/dark-mode'.
```

---

## 7. Safety Guard Examples

### Force Push Protection

```
You: Force push to main

🛑 DANGER: Force push to main

This will:
- Overwrite remote history
- Potentially break other developers' work
- May violate repository policies

Remote commits that would be lost:
  abc1234 - Fix critical bug (pushed 2 hours ago)
  def5678 - Update dependencies (pushed 1 day ago)

This is a destructive operation. Are you absolutely sure?
Type 'force push main' to confirm:
```

### Hard Reset Protection

```
You: Reset hard to origin/main

⚠️ Hard reset warning

You have uncommitted changes that will be LOST:
  M  src/config.py (15 lines changed)
  M  tests/test_auth.py (32 lines changed)
  ?  notes.md

These changes are NOT recoverable after hard reset.

Alternatives:
1. Stash changes before reset
2. Commit changes to a temporary branch
3. Continue without resetting

Proceed with hard reset? [y/n]
```

---

## 8. Git Context in System Prompt

### Context Display

```
You: /context

System Context:
═══════════════════════════════════════════

Git Repository: /home/user/project
Branch: feature/new-auth
Status: 3 staged, 2 modified
Tracking: origin/feature/new-auth (2 ahead)

Last commit: abc1234 "Add OAuth handler"
  by You, 15 minutes ago

...
```

### Commit Message Generation

```
You: Generate a commit message for the staged changes

Based on the staged changes, here's a suggested commit message:

───────────────────────────────────────────
Add caching configuration and extend auth tests

- Add enable_cache and cache_ttl settings to Config
- Add rate limiting test to authentication suite
- Import datetime for login timestamp logging
───────────────────────────────────────────

Changes analyzed:
  src/config.py: Added cache configuration fields
  tests/test_auth.py: Added rate limiting test case
  src/auth/login.py: Added login timestamp logging

Use this message? [y/n/edit]
```

---

## 9. Error Handling

### Repository Not Found

```
You: git status

Error: Not a Git repository

The current directory '/home/user/documents' is not a Git repository
or any parent directory.

To initialize a new repository:
  git init

To clone an existing repository:
  git clone <url>
```

### Git Not Installed

```
You: Show git status

Error: Git is not installed

Git is required for repository operations.

Install Git:
  Ubuntu/Debian: sudo apt install git
  macOS: brew install git
  Windows: Download from git-scm.com
```

### Permission Denied

```
You: Push to origin

Error: Permission denied

You don't have push access to 'origin/main'.

Possible causes:
- SSH key not configured
- Insufficient repository permissions
- Branch protection rules

Check your credentials and repository access.
```

### Merge Conflict

```
You: Pull latest

Error: Merge conflict

Automatic merge failed for:
  src/core/handler.py
  src/utils/parser.py

Fix conflicts and then commit the result.

To see conflicts:
  git diff --name-only --diff-filter=U

To abort the merge:
  git merge --abort
```

---

## 10. Slash Commands

### /git command

```
You: /git

Git Status
═══════════════════════════════════════════

Branch: feature/new-auth
Tracking: origin/feature/new-auth (2 ahead)

Staged (3):
  M  src/auth/login.py
  A  src/auth/oauth.py
  M  src/config.py

Modified (2):
  M  tests/test_auth.py
  M  README.md

Available commands:
  /git status    - Detailed status
  /git log       - Recent commits
  /git diff      - Show changes
  /git branches  - List branches
  /git commit    - Commit staged changes
```

### /git log

```
You: /git log

Recent Commits
═══════════════════════════════════════════

abc1234 (HEAD -> feature/new-auth)
  Add OAuth handler
  Alice, 15 minutes ago

def5678
  Refactor login validation
  Alice, 2 hours ago

789abcd
  Initial auth implementation
  Bob, yesterday

456def0 (origin/main, main)
  Release v1.2.0
  Alice, 2 days ago

Showing 4 of 127 commits. Use --count for more.
```

### /git diff

```
You: /git diff

Working Tree Changes
═══════════════════════════════════════════

tests/test_auth.py
@@ -45,6 +45,15 @@
     def test_invalid_password(self):
         result = login("user", "wrong")
         assert result.error == "invalid_credentials"
+
+    def test_rate_limiting(self):
+        # Test rate limiting behavior
+        for i in range(10):
+            login("user", "wrong")
+        result = login("user", "wrong")
+        assert result.error == "rate_limited"

README.md
@@ -1,4 +1,4 @@
-# Project Name
+# Project Name v2

2 files changed, +10 -1
```

### /git branches

```
You: /git branches

Branches
═══════════════════════════════════════════

Local:
* feature/new-auth     abc1234 [+2]
  main                 456def0 [=]
  develop              789abcd [+1, -3]
  bugfix/login         012abc3 [+1]

Remote:
  origin/main
  origin/develop
  origin/feature/new-auth

4 local, 3 remote tracking
```

### /git commit

```
You: /git commit Add new authentication module

Committing staged changes...

[feature/new-auth abc1234] Add new authentication module
 3 files changed, 312 insertions(+), 15 deletions(-)
 create mode 100644 src/auth/oauth.py

Commit created successfully.

Push to origin? [y/n]
```

---

## Notes

- Git operations run asynchronously via subprocess
- Output is formatted for terminal display with colors where supported
- Safety checks run before any potentially destructive operation
- Context is automatically provided to LLM for git-aware responses
- All operations respect user's git configuration (signing, hooks, etc.)
