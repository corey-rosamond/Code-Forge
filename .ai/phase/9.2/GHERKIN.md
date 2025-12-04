# Phase 9.2: GitHub Integration - Gherkin Specifications

**Phase:** 9.2
**Name:** GitHub Integration
**Dependencies:** Phase 9.1 (Git Integration), Phase 8.2 (Web Tools)

---

## Feature: GitHub Authentication

### Scenario: Authenticate with valid token
```gherkin
Given a valid GitHub personal access token
When I create GitHubAuthenticator with the token
And I call validate()
Then authentication should succeed
And GitHubAuth should contain username
And GitHubAuth should contain scopes
And GitHubAuth should contain rate limit info
```

### Scenario: Authenticate from environment variable
```gherkin
Given GITHUB_TOKEN environment variable is set
When I create GitHubAuthenticator without token
And I call validate()
Then token should be read from environment
And authentication should succeed
```

### Scenario: Authenticate from GH_TOKEN fallback
```gherkin
Given GITHUB_TOKEN is not set
And GH_TOKEN environment variable is set
When I create GitHubAuthenticator without token
Then token should be read from GH_TOKEN
```

### Scenario: Authentication fails with invalid token
```gherkin
Given an invalid GitHub token
When I call validate()
Then GitHubAuthError should be raised
And error message should mention "Invalid token"
```

### Scenario: Authentication fails with no token
```gherkin
Given no token is provided
And no environment variable is set
When I call validate()
Then GitHubAuthError should be raised
And error should mention GITHUB_TOKEN
```

### Scenario: Get authentication headers
```gherkin
Given an authenticated GitHubAuthenticator
When I call get_headers()
Then headers should contain "Authorization: Bearer <token>"
And headers should contain "Accept: application/vnd.github+json"
And headers should contain "X-GitHub-Api-Version"
```

---

## Feature: GitHub API Client

### Scenario: Make GET request
```gherkin
Given a GitHubClient with valid auth
When I call get("/repos/owner/repo")
Then request should be made to api.github.com
And response should be parsed as JSON
And rate limits should be updated
```

### Scenario: Make POST request
```gherkin
Given a GitHubClient
When I call post("/repos/owner/repo/issues", data)
Then POST request should be made
And request body should contain data
And response should be returned
```

### Scenario: Handle pagination
```gherkin
Given an API endpoint with 100 results
And per_page is 30
When I call get_paginated(path)
Then multiple requests should be made
And all results should be combined
And final list should have 100 items
```

### Scenario: Respect max_pages limit
```gherkin
Given an API endpoint with many pages
When I call get_paginated(path, max_pages=2)
Then only 2 pages should be fetched
And remaining pages should be ignored
```

### Scenario: Handle rate limit error
```gherkin
Given API returns 403 with X-RateLimit-Remaining: 0
When I make any request
Then GitHubRateLimitError should be raised
And rate limit info should be updated
```

### Scenario: Handle 404 error
```gherkin
Given a non-existent resource
When I call get("/repos/owner/nonexistent")
Then GitHubNotFoundError should be raised
And error should have status 404
```

### Scenario: Retry on transient failure
```gherkin
Given network error on first attempt
When I make a request
Then request should be retried
And exponential backoff should be used
```

---

## Feature: Repository Operations

### Scenario: Get repository information
```gherkin
Given a valid repository "owner/repo"
When I call repo_service.get("owner", "repo")
Then GitHubRepository should be returned
And repository should have owner, name, description
And repository should have default_branch
And repository should have stars, forks counts
```

### Scenario: List repository branches
```gherkin
Given a repository with branches "main", "develop", "feature"
When I call list_branches("owner", "repo")
Then list of GitHubBranch should be returned
And list should contain 3 branches
And each branch should have name and commit_sha
```

### Scenario: List protected branches only
```gherkin
Given a repository with protected and unprotected branches
When I call list_branches("owner", "repo", protected=True)
Then only protected branches should be returned
```

### Scenario: List repository tags
```gherkin
Given a repository with tags "v1.0", "v1.1", "v2.0"
When I call list_tags("owner", "repo")
Then list of GitHubTag should be returned
And each tag should have name and commit_sha
```

### Scenario: Parse HTTPS remote URL
```gherkin
Given remote URL "https://github.com/owner/repo.git"
When I call parse_remote_url(url)
Then result should be ("owner", "repo")
```

### Scenario: Parse SSH remote URL
```gherkin
Given remote URL "git@github.com:owner/repo.git"
When I call parse_remote_url(url)
Then result should be ("owner", "repo")
```

### Scenario: Parse non-GitHub URL
```gherkin
Given remote URL "https://gitlab.com/owner/repo.git"
When I call parse_remote_url(url)
Then result should be None
```

---

## Feature: Issue Operations

### Scenario: List open issues
```gherkin
Given a repository with 5 open issues
When I call issue_service.list("owner", "repo", state="open")
Then list of GitHubIssue should be returned
And all issues should have state "open"
And pull requests should be excluded
```

### Scenario: List issues with label filter
```gherkin
Given a repository with issues labeled "bug" and "feature"
When I call list("owner", "repo", labels=["bug"])
Then only issues with "bug" label should be returned
```

### Scenario: List issues assigned to user
```gherkin
Given issues assigned to different users
When I call list("owner", "repo", assignee="alice")
Then only issues assigned to alice should be returned
```

### Scenario: Get single issue
```gherkin
Given issue #42 exists
When I call get("owner", "repo", 42)
Then GitHubIssue should be returned
And issue.number should be 42
And issue should have title, body, author
```

### Scenario: Create new issue
```gherkin
Given valid issue data
When I call create("owner", "repo", "Bug report", body="Details")
Then new issue should be created
And GitHubIssue should be returned with number
And issue.state should be "open"
```

### Scenario: Update issue
```gherkin
Given existing issue #42
When I call update("owner", "repo", 42, title="New title")
Then issue should be updated
And returned issue should have new title
```

### Scenario: Close issue
```gherkin
Given open issue #42
When I call close("owner", "repo", 42)
Then issue state should be "closed"
And state_reason should be "completed"
```

### Scenario: List issue comments
```gherkin
Given issue #42 with 3 comments
When I call list_comments("owner", "repo", 42)
Then list of GitHubComment should be returned
And list should have 3 comments
And each comment should have body and author
```

### Scenario: Add comment to issue
```gherkin
Given issue #42
When I call add_comment("owner", "repo", 42, "My comment")
Then new comment should be created
And GitHubComment should be returned
```

### Scenario: Add labels to issue
```gherkin
Given issue #42 with no labels
When I call add_labels("owner", "repo", 42, ["bug", "urgent"])
Then issue should have both labels
And list of GitHubLabel should be returned
```

---

## Feature: Pull Request Operations

### Scenario: List open pull requests
```gherkin
Given a repository with 3 open PRs
When I call pr_service.list("owner", "repo", state="open")
Then list of GitHubPullRequest should be returned
And all PRs should have state "open"
```

### Scenario: List PRs by base branch
```gherkin
Given PRs targeting "main" and "develop"
When I call list("owner", "repo", base="main")
Then only PRs targeting main should be returned
```

### Scenario: Get single pull request
```gherkin
Given PR #123 exists
When I call get("owner", "repo", 123)
Then GitHubPullRequest should be returned
And PR should have head_ref and base_ref
And PR should have additions, deletions, changed_files
```

### Scenario: Create pull request
```gherkin
Given a branch "feature" with commits
When I call create("owner", "repo", "New feature", "feature", "main")
Then new PR should be created
And GitHubPullRequest should be returned
And PR should be open and not merged
```

### Scenario: Create draft pull request
```gherkin
Given a branch with changes
When I call create(..., draft=True)
Then PR should be created as draft
And pr.draft should be True
```

### Scenario: Get PR diff
```gherkin
Given PR #123 with file changes
When I call get_diff("owner", "repo", 123)
Then unified diff string should be returned
And diff should show additions and deletions
```

### Scenario: Get PR files
```gherkin
Given PR #123 changing 5 files
When I call get_files("owner", "repo", 123)
Then list of GitHubPRFile should be returned
And each file should have filename, status, additions
```

### Scenario: Get PR commits
```gherkin
Given PR #123 with 3 commits
When I call get_commits("owner", "repo", 123)
Then list of commits should be returned
And list should have 3 commits
```

### Scenario: List PR reviews
```gherkin
Given PR #123 with 2 reviews
When I call list_reviews("owner", "repo", 123)
Then list of GitHubReview should be returned
And each review should have state and author
```

### Scenario: Create approval review
```gherkin
Given PR #123 ready for review
When I call create_review("owner", "repo", 123, event="APPROVE")
Then review should be created
And review.state should be "APPROVED"
```

### Scenario: Request changes review
```gherkin
Given PR #123
When I call create_review(..., event="REQUEST_CHANGES", body="Fix X")
Then review should request changes
And review should have body
```

### Scenario: Get PR check runs
```gherkin
Given PR #123 with CI checks
When I call get_checks("owner", "repo", pr.head_sha)
Then list of GitHubCheckRun should be returned
And each check should have name, status, conclusion
```

### Scenario: Merge pull request
```gherkin
Given PR #123 is mergeable
When I call merge("owner", "repo", 123)
Then PR should be merged
And merge result should be returned
```

### Scenario: Squash merge pull request
```gherkin
Given PR #123
When I call merge(..., merge_method="squash")
Then commits should be squashed
And single commit should be created
```

### Scenario: Request reviewers
```gherkin
Given PR #123
When I call request_reviewers("owner", "repo", 123, ["alice", "bob"])
Then reviewers should be requested
And PR should have requested_reviewers
```

---

## Feature: GitHub Actions

### Scenario: List workflow runs
```gherkin
Given repository with CI workflows
When I call actions.list_runs("owner", "repo")
Then list of WorkflowRun should be returned
And each run should have status and conclusion
```

### Scenario: List runs for specific workflow
```gherkin
Given workflow "ci.yml"
When I call list_runs("owner", "repo", workflow_id="ci.yml")
Then only runs for that workflow should be returned
```

### Scenario: List runs by branch
```gherkin
Given runs on different branches
When I call list_runs("owner", "repo", branch="main")
Then only runs on main should be returned
```

### Scenario: Get workflow run
```gherkin
Given run with ID 12345
When I call get_run("owner", "repo", 12345)
Then WorkflowRun should be returned
And run should have status, conclusion, event
```

### Scenario: List run jobs
```gherkin
Given run 12345 with 3 jobs
When I call list_run_jobs("owner", "repo", 12345)
Then list of WorkflowJob should be returned
And each job should have steps
```

### Scenario: Re-run workflow
```gherkin
Given failed run 12345
When I call rerun("owner", "repo", 12345)
Then workflow should be re-triggered
```

### Scenario: Re-run failed jobs only
```gherkin
Given run with some failed jobs
When I call rerun_failed("owner", "repo", 12345)
Then only failed jobs should be re-run
```

### Scenario: Cancel running workflow
```gherkin
Given in-progress run 12345
When I call cancel("owner", "repo", 12345)
Then workflow should be cancelled
```

---

## Feature: GitHub Context for LLM

### Scenario: Get repository context summary
```gherkin
Given a GitHub repository "owner/repo"
When I call get_context_summary("owner", "repo")
Then summary should include repository name
And summary should include description
And summary should include default branch
And summary should include open issues count
```

### Scenario: Format issue for LLM
```gherkin
Given a GitHubIssue with labels and assignees
When I call format_issue(issue)
Then output should include issue number and title
And output should include state and author
And output should include labels
And output should include body
```

### Scenario: Format PR for LLM
```gherkin
Given a GitHubPullRequest with reviews
When I call format_pr(pr)
Then output should include PR number and title
And output should include branch info
And output should include change statistics
And output should include reviewer info
```

### Scenario: Format issue list
```gherkin
Given list of 5 issues
When I call format_issue_list(issues)
Then output should have 5 lines
And each line should show number, title, author
```

### Scenario: Format PR list
```gherkin
Given list of 3 PRs with one draft
When I call format_pr_list(prs)
Then output should have 3 lines
And draft PR should be marked [DRAFT]
```

---

## Feature: Error Handling

### Scenario: Handle network error
```gherkin
Given network is unavailable
When I make any API call
Then GitHubAPIError should be raised
And error should mention network
```

### Scenario: Handle rate limit
```gherkin
Given rate limit is exceeded
When I make API call
Then GitHubRateLimitError should be raised
And error should mention rate limit
And reset time should be available
```

### Scenario: Handle permission denied
```gherkin
Given user lacks permission for action
When I try to merge PR
Then GitHubAPIError should be raised
And status should be 403
```

### Scenario: Handle validation error
```gherkin
Given invalid data for create issue
When I call create with missing title
Then GitHubAPIError should be raised
And response should contain validation errors
```

---

## Feature: Rate Limit Tracking

### Scenario: Track rate limit from response
```gherkin
Given API response with rate limit headers
When request completes
Then rate_remaining should be updated
And rate_reset should be updated
```

### Scenario: Warn when approaching limit
```gherkin
Given rate_remaining is below threshold
When checking rate limit status
Then warning should be available
```

### Scenario: Check rate limit status
```gherkin
Given GitHubAuth with rate info
When I check is_rate_limited
Then should return False if remaining > 0
And should return True if remaining = 0
```
