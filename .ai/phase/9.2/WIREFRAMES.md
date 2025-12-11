# Phase 9.2: GitHub Integration - Wireframes & Usage Examples

**Phase:** 9.2
**Name:** GitHub Integration
**Dependencies:** Phase 9.1 (Git Integration), Phase 8.2 (Web Tools)

---

## 1. GitHub Authentication Status

### Authenticated Status

```
You: /gh

GitHub Status
═══════════════════════════════════════════

Authenticated as: @alice
Token scopes: repo, workflow, read:org

Rate Limit: 4,892 / 5,000 remaining
Resets at: 2024-01-15 15:45:00

Repository: alice/my-project
Default branch: main
Open issues: 12
Open PRs: 3

Commands:
  /gh repo     - Repository details
  /gh issues   - List issues
  /gh prs      - List pull requests
  /gh pr <n>   - Show PR details
  /gh actions  - Workflow status
```

### Not Authenticated

```
You: /gh

GitHub Status
═══════════════════════════════════════════

⚠️ Not authenticated

To use GitHub features, set one of:
  - GITHUB_TOKEN environment variable
  - GH_TOKEN environment variable

Or configure in ~/.src/forge/config.yaml:
  github:
    token: "ghp_your_token_here"

Get a token at: https://github.com/settings/tokens
```

---

## 2. Repository Information

### Repository Details

```
You: /gh repo

Repository: alice/my-project
═══════════════════════════════════════════

Description: A sample project for demonstration
URL: https://github.com/alice/my-project

Visibility: Public
Language: Python
Default branch: main

Stars: 234
Forks: 45
Open issues: 12

Topics: python, api, cli

Recent activity:
  Last push: 2 hours ago
  Last commit: "Fix authentication bug"
```

### Private Repository

```
You: /gh repo

Repository: alice/internal-tool
═══════════════════════════════════════════

Description: Internal company tool
URL: https://github.com/alice/internal-tool

Visibility: Private 🔒
Language: Go
Default branch: main

Stars: 5
Forks: 0
Open issues: 3

Topics: internal, automation
```

---

## 3. Issues

### List Issues

```
You: /gh issues

Open Issues (12)
═══════════════════════════════════════════

#45 Login fails with special characters [bug, auth]
    @bob, opened 2 hours ago, 3 comments

#42 Add dark mode support [enhancement, ui]
    @alice, opened 1 day ago, 7 comments

#38 Update documentation for v2.0 [docs]
    @carol, opened 3 days ago, 1 comment

#35 Performance regression in search [bug, performance]
    @david, opened 5 days ago, 12 comments

...showing 4 of 12 issues

Use '/gh issues --all' to see closed issues
```

### Issue Details

```
You: /gh issue 45

Issue #45: Login fails with special characters
═══════════════════════════════════════════

State: Open
Author: @bob
Created: 2024-01-15 10:30:00
Labels: bug, auth
Assignees: @alice

Description:
────────────────────────────────────────────
When a user has special characters (like @, #, $) in their
password, the login fails with a 500 error.

Steps to reproduce:
1. Create account with password "Test@123"
2. Try to login
3. Get 500 error

Expected: Login should work
Actual: Server error
────────────────────────────────────────────

Comments (3):

@alice (2 hours ago):
  I can reproduce this. Looking into it.

@bob (1 hour ago):
  Thanks! Let me know if you need more info.

@alice (30 minutes ago):
  Found the issue - escaping problem in SQL query.
  Working on a fix.
```

### Create Issue

```
You: Create a GitHub issue for the memory leak we discussed

Creating issue...

Issue #46 created: Memory leak in connection pool
═══════════════════════════════════════════

URL: https://github.com/alice/my-project/issues/46

Title: Memory leak in connection pool
Labels: bug, memory
Assignees: (none)

Description:
────────────────────────────────────────────
The connection pool in `src/pool.py` is not properly
releasing connections, leading to memory growth over time.

Observed in production after ~24 hours of uptime.

Related: Discussion in session about pool.py:145
────────────────────────────────────────────

Would you like to add labels or assign someone?
```

---

## 4. Pull Requests

### List Pull Requests

```
You: /gh prs

Open Pull Requests (3)
═══════════════════════════════════════════

#52 Add OAuth2 authentication [feature, auth]
    feature/oauth -> main
    @alice, opened 1 day ago
    +847 -23 in 12 files
    ✓ All checks passed

#48 Fix memory leak in pool [bug]
    fix/memory-leak -> main
    @bob, opened 3 days ago
    +45 -12 in 3 files
    ⏳ Waiting for review

#47 Update dependencies [DRAFT]
    chore/deps -> main
    @carol, opened 4 days ago
    +234 -189 in 2 files
```

### PR Details

```
You: /gh pr 52

Pull Request #52: Add OAuth2 authentication
═══════════════════════════════════════════

State: Open
Author: @alice
Created: 2024-01-14 09:00:00
Branch: feature/oauth -> main

Labels: feature, auth
Assignees: @alice
Reviewers: @bob (pending), @carol (approved)

Changes: +847 -23 in 12 files
Commits: 8

Description:
────────────────────────────────────────────
## Summary
This PR adds OAuth2 authentication support.

## Changes
- Add OAuth2 provider configuration
- Implement token refresh logic
- Add login redirect flow
- Update user session handling

## Test Plan
- [x] Unit tests pass
- [x] Integration tests added
- [x] Manual testing completed
────────────────────────────────────────────

Checks:
  ✓ ci/build (passed)
  ✓ ci/test (passed)
  ✓ ci/lint (passed)
  ✓ codecov/project (passed)

Reviews:
  @bob: Pending (requested 1 day ago)
  @carol: Approved ✓
    "Looks good! Nice implementation."
```

### PR Diff Summary

```
You: Show me the files changed in PR 52

Files changed in PR #52 (12 files)
═══════════════════════════════════════════

Modified:
  src/auth/__init__.py          +5   -1
  src/auth/handler.py           +145 -8
  src/auth/session.py           +67  -3
  src/config.py                 +23  -2
  src/routes/login.py           +89  -5
  tests/test_auth.py            +234 -0

Added:
  src/auth/oauth.py             +178 -0
  src/auth/providers/__init__.py +12  -0
  src/auth/providers/google.py  +45  -0
  src/auth/providers/github.py  +49  -0

Summary: +847 insertions, -23 deletions

Would you like to see the diff for any specific file?
```

### Create PR

```
You: Create a pull request for my current branch

Analyzing branch 'fix/validation-error'...

Branch has 3 commits not in main:
  abc1234 Fix input validation
  def5678 Add validation tests
  789abcd Update error messages

Creating pull request...

Pull Request #53 created
═══════════════════════════════════════════

URL: https://github.com/alice/my-project/pull/53

Title: Fix input validation error handling
Branch: fix/validation-error -> main

Description:
────────────────────────────────────────────
## Summary
- Fix input validation to handle edge cases
- Add comprehensive validation tests
- Improve error messages for users

## Test plan
- [x] Unit tests added
- [ ] Manual testing

🤖 Generated with Code-Forge
────────────────────────────────────────────

Changes: +156 -34 in 5 files

Would you like to request reviewers?
```

---

## 5. GitHub Actions

### Workflow Status

```
You: /gh actions

Recent Workflow Runs
═══════════════════════════════════════════

CI/CD Pipeline:
  #456 ✓ Passed - main (abc1234)
      Triggered by push, 15 minutes ago

  #455 ✗ Failed - feature/oauth (def5678)
      Triggered by pull_request, 2 hours ago
      Failed job: test

  #454 ✓ Passed - main (789abcd)
      Triggered by push, 5 hours ago

Security Scan:
  #89 ✓ Passed - main
      Triggered by schedule, 6 hours ago

Commands:
  /gh run 455     - View run details
  /gh run 455 log - View logs
```

### Workflow Run Details

```
You: Show me the failed CI run

Workflow Run #455: CI/CD Pipeline
═══════════════════════════════════════════

Status: Failed ✗
Branch: feature/oauth
Commit: def5678 "Add OAuth provider"
Event: pull_request
Duration: 4m 32s

Jobs:
  build       ✓ Passed   (45s)
  lint        ✓ Passed   (1m 12s)
  test        ✗ Failed   (2m 35s)
  deploy      ⊘ Skipped

Failed Job: test
────────────────────────────────────────────
Step 4: Run tests (pytest)

FAILED tests/test_oauth.py::test_token_refresh
  AssertionError: Expected token to be refreshed

  > assert new_token != old_token
  E assert 'abc123' != 'abc123'

1 failed, 156 passed in 2m 18s
────────────────────────────────────────────

Actions:
  /gh run 455 rerun - Re-run all jobs
  /gh run 455 rerun-failed - Re-run failed only
```

### Re-run Workflow

```
You: Re-run the failed jobs

Re-running failed jobs for run #455...

Workflow run triggered.
View at: https://github.com/alice/my-project/actions/runs/455

Current status: queued
Jobs to run: test

Would you like me to monitor the progress?
```

---

## 6. PR Reviews

### View Reviews

```
You: Show reviews for PR 52

Reviews for PR #52
═══════════════════════════════════════════

@carol - Approved ✓
  Submitted: 2024-01-14 14:30
  ────────────────────────────────────────
  Looks good! Nice implementation of the OAuth flow.

  Minor suggestions:
  - Consider adding rate limiting for token refresh
  - Add logging for auth failures

@bob - Pending
  Requested: 2024-01-14 09:00
  No review submitted yet.

Review Comments (3):

  src/auth/oauth.py:45
  @carol: Consider using a constant for the timeout value.

  src/auth/oauth.py:78
  @carol: This could throw if response is empty.

  src/auth/handler.py:123
  @david: Nice error handling here!
```

### Create Review

```
You: Approve PR 52 with a comment

Creating review for PR #52...

Review submitted: APPROVED ✓
═══════════════════════════════════════════

Comment:
────────────────────────────────────────────
LGTM! The OAuth implementation looks solid.

Tested locally and it works well with both Google
and GitHub providers.

Minor note: Consider adding docs for the new
configuration options.
────────────────────────────────────────────

PR #52 now has 2 approvals.
Ready to merge!
```

---

## 7. Error Handling

### Rate Limit Warning

```
You: /gh issues

⚠️ Rate Limit Warning
═══════════════════════════════════════════

Remaining: 42 / 5000 requests
Resets at: 2024-01-15 15:45:00 (in 12 minutes)

Consider waiting before making more requests.

Proceed anyway? [y/n]
```

### Rate Limit Error

```
You: List all issues

❌ Rate Limit Exceeded
═══════════════════════════════════════════

You have exceeded the GitHub API rate limit.

Limit: 5000 requests per hour
Remaining: 0
Resets at: 2024-01-15 15:45:00 (in 8 minutes)

Options:
1. Wait 8 minutes and try again
2. Use authenticated requests (higher limit)
3. Consider GitHub API caching
```

### Not Found Error

```
You: Show me issue 999

❌ Not Found
═══════════════════════════════════════════

Issue #999 was not found in alice/my-project.

Possible causes:
- Issue number doesn't exist
- Issue was deleted
- Repository is private and you lack access

Check the issue number and try again.
```

### Authentication Error

```
You: Create an issue

❌ Authentication Required
═══════════════════════════════════════════

This action requires GitHub authentication.

Current status: Not authenticated

To authenticate:
1. Create a token at https://github.com/settings/tokens
2. Set GITHUB_TOKEN environment variable
3. Ensure token has 'repo' scope

Token requirements:
  ✓ repo (for private repos)
  ✓ public_repo (for public repos only)
```

---

## 8. Context Integration

### GitHub Context in System Prompt

```
You: /context

System Context
═══════════════════════════════════════════

Git Repository: /home/user/my-project
Branch: feature/new-auth
Status: clean (no uncommitted changes)

GitHub: alice/my-project
  Description: A sample project
  Default branch: main
  Open issues: 12
  Open PRs: 3

Current PR: #52 (Add OAuth2 authentication)
  Status: Open, awaiting review
  Checks: All passing ✓

Rate limit: 4,892 / 5,000 remaining
```

### Automatic GitHub Detection

```
You: What's happening on GitHub?

Detected GitHub repository: alice/my-project

GitHub Status
═══════════════════════════════════════════

Recent Activity:

Issues:
  #45 Login fails with special characters (opened 2h ago)
  #44 Feature request: dark mode (opened 1d ago)

Pull Requests:
  #52 Add OAuth2 authentication
      Ready for review, 2 approvals needed
      ✓ All checks passing

  #51 Fix memory leak
      Changes requested by @bob

Workflow Runs:
  ✓ CI passed on main (15 min ago)
  ✗ CI failed on feature/oauth (2h ago)
```

---

## 9. Slash Commands Reference

```
You: /help gh

GitHub Commands
═══════════════════════════════════════════

/gh                 Show GitHub status
/gh repo            Repository information
/gh issues          List open issues
/gh issues --all    List all issues
/gh issue <n>       Show issue details
/gh prs             List open PRs
/gh pr <n>          Show PR details
/gh pr create       Create pull request
/gh actions         Show workflow runs
/gh run <id>        Show run details

Issue Operations:
/gh issue create    Create new issue
/gh issue close <n> Close issue

PR Operations:
/gh pr merge <n>    Merge pull request
/gh pr approve <n>  Approve PR
/gh pr review <n>   Add review to PR

Actions:
/gh run rerun <id>  Re-run workflow
/gh run cancel <id> Cancel workflow
```

---

## 10. Combined Git + GitHub Workflows

### Push and Create PR

```
You: Push my changes and create a PR

Pushing to origin/feature/validation...
Enumerating objects: 15, done.
Writing objects: 100% (15/15), done.

To github.com:alice/my-project.git
   abc1234..def5678  feature/validation -> feature/validation

Creating pull request...

Pull Request #54 created
═══════════════════════════════════════════

URL: https://github.com/alice/my-project/pull/54

Title: Fix input validation
Branch: feature/validation -> main
Changes: +89 -12 in 4 files

CI is now running. I'll let you know when it completes.
```

### Check Status Before Merge

```
You: Can I merge PR 52?

Checking PR #52 status...

PR #52: Add OAuth2 authentication
═══════════════════════════════════════════

✓ Branch is up to date with main
✓ All checks have passed
✓ Has required approvals (2/2)
✓ No merge conflicts

Ready to merge!

Merge options:
1. Create merge commit
2. Squash and merge
3. Rebase and merge

Which would you prefer?
```

---

## Notes

- GitHub token is never displayed in output
- Rate limits are tracked and warnings shown proactively
- Repository context is auto-detected from git remote
- Commands work with both issue numbers and URLs
- PR creation uses smart defaults from git context
- Reviews can include line comments
