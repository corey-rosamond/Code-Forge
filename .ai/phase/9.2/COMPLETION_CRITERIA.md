# Phase 9.2: GitHub Integration - Completion Criteria

**Phase:** 9.2
**Name:** GitHub Integration
**Dependencies:** Phase 9.1 (Git Integration), Phase 8.2 (Web Tools)

---

## Completion Checklist

### 1. Authentication (auth.py)

- [ ] `GitHubAuth` dataclass implemented
  - [ ] `token: str`
  - [ ] `username: str`
  - [ ] `scopes: list[str]`
  - [ ] `rate_limit: int`
  - [ ] `rate_remaining: int`
  - [ ] `rate_reset: int`
  - [ ] `rate_reset_time` property
  - [ ] `is_rate_limited` property

- [ ] `GitHubAuthenticator` class implemented
  - [ ] `__init__(token: str | None)` constructor
  - [ ] Token from GITHUB_TOKEN env var
  - [ ] Token from GH_TOKEN fallback
  - [ ] `has_token` property
  - [ ] `is_authenticated` property
  - [ ] `validate()` async method
  - [ ] `get_headers()` method
  - [ ] `update_rate_limit()` method

- [ ] `GitHubAuthError` exception defined

### 2. API Client (client.py)

- [ ] `GitHubClient` class implemented
  - [ ] `__init__(auth, timeout, max_retries)`
  - [ ] `get(path, **params)` async method
  - [ ] `get_raw(path, accept)` async method
  - [ ] `post(path, data)` async method
  - [ ] `patch(path, data)` async method
  - [ ] `put(path, data)` async method
  - [ ] `delete(path)` async method
  - [ ] `get_paginated(path, per_page, max_pages)` async method
  - [ ] `close()` async method

- [ ] Client features
  - [ ] Rate limit tracking from headers
  - [ ] Retry on transient failures
  - [ ] Proper error handling
  - [ ] Session management

- [ ] Exception classes
  - [ ] `GitHubAPIError`
  - [ ] `GitHubRateLimitError`
  - [ ] `GitHubNotFoundError`

### 3. Repository Service (repository.py)

- [ ] `GitHubRepository` dataclass implemented
  - [ ] All required fields
  - [ ] `from_api()` class method

- [ ] `GitHubBranch` dataclass implemented
  - [ ] `name: str`
  - [ ] `commit_sha: str`
  - [ ] `protected: bool`
  - [ ] `from_api()` class method

- [ ] `GitHubTag` dataclass implemented
  - [ ] `name: str`
  - [ ] `commit_sha: str`
  - [ ] `from_api()` class method

- [ ] `RepositoryService` class implemented
  - [ ] `get(owner, repo)` async method
  - [ ] `list_branches(owner, repo)` async method
  - [ ] `get_branch(owner, repo, branch)` async method
  - [ ] `list_tags(owner, repo)` async method
  - [ ] `get_readme(owner, repo)` async method
  - [ ] `get_content(owner, repo, path)` async method
  - [ ] `parse_remote_url(url)` static method

### 4. Issue Service (issues.py)

- [ ] `GitHubUser` dataclass implemented
- [ ] `GitHubLabel` dataclass implemented
- [ ] `GitHubMilestone` dataclass implemented
- [ ] `GitHubIssue` dataclass implemented
- [ ] `GitHubComment` dataclass implemented

- [ ] `IssueService` class implemented
  - [ ] `list(owner, repo, ...)` async method
  - [ ] `get(owner, repo, issue_number)` async method
  - [ ] `create(owner, repo, ...)` async method
  - [ ] `update(owner, repo, ...)` async method
  - [ ] `close(owner, repo, ...)` async method
  - [ ] `reopen(owner, repo, ...)` async method
  - [ ] `list_comments(...)` async method
  - [ ] `add_comment(...)` async method
  - [ ] `update_comment(...)` async method
  - [ ] `delete_comment(...)` async method
  - [ ] `add_labels(...)` async method
  - [ ] `remove_label(...)` async method

### 5. Pull Request Service (pull_requests.py)

- [ ] `GitHubPullRequest` dataclass implemented
- [ ] `GitHubReview` dataclass implemented
- [ ] `GitHubReviewComment` dataclass implemented
- [ ] `GitHubCheckRun` dataclass implemented
- [ ] `GitHubPRFile` dataclass implemented

- [ ] `PullRequestService` class implemented
  - [ ] `list(owner, repo, ...)` async method
  - [ ] `get(owner, repo, pr_number)` async method
  - [ ] `create(owner, repo, ...)` async method
  - [ ] `update(owner, repo, ...)` async method
  - [ ] `get_diff(owner, repo, pr_number)` async method
  - [ ] `get_files(owner, repo, pr_number)` async method
  - [ ] `get_commits(owner, repo, pr_number)` async method
  - [ ] `list_reviews(...)` async method
  - [ ] `create_review(...)` async method
  - [ ] `list_review_comments(...)` async method
  - [ ] `get_checks(owner, repo, ref)` async method
  - [ ] `get_combined_status(...)` async method
  - [ ] `merge(owner, repo, pr_number, ...)` async method
  - [ ] `request_reviewers(...)` async method

### 6. Actions Service (actions.py)

- [ ] `Workflow` dataclass implemented
- [ ] `WorkflowRun` dataclass implemented
- [ ] `WorkflowJob` dataclass implemented

- [ ] `ActionsService` class implemented
  - [ ] `list_workflows(owner, repo)` async method
  - [ ] `list_runs(owner, repo, ...)` async method
  - [ ] `get_run(owner, repo, run_id)` async method
  - [ ] `list_run_jobs(...)` async method
  - [ ] `get_run_logs(...)` async method
  - [ ] `rerun(owner, repo, run_id)` async method
  - [ ] `rerun_failed(...)` async method
  - [ ] `cancel(owner, repo, run_id)` async method
  - [ ] `get_job_logs(...)` async method

### 7. GitHub Context (context.py)

- [ ] `GitHubContext` class implemented
  - [ ] `get_context_summary(owner, repo)` async method
  - [ ] `format_issue(issue)` method
  - [ ] `format_pr(pr)` method
  - [ ] `format_issue_list(issues)` method
  - [ ] `format_pr_list(prs)` method

### 8. Package Exports (__init__.py)

- [ ] All dataclasses exported
- [ ] All service classes exported
- [ ] All exception classes exported
- [ ] `GitHubAuthenticator` exported
- [ ] `GitHubClient` exported
- [ ] `GitHubContext` exported
- [ ] `__all__` list complete

### 9. Integration

- [ ] Detect GitHub remote from git config
- [ ] `/gh` slash command implemented
- [ ] `/gh repo` command implemented
- [ ] `/gh issues` command implemented
- [ ] `/gh issue <n>` command implemented
- [ ] `/gh prs` command implemented
- [ ] `/gh pr <n>` command implemented
- [ ] `/gh actions` command implemented
- [ ] GitHub context in system prompt

### 10. Testing

- [ ] Unit tests for GitHubAuthenticator
- [ ] Unit tests for GitHubClient (mocked)
- [ ] Unit tests for RepositoryService
- [ ] Unit tests for IssueService
- [ ] Unit tests for PullRequestService
- [ ] Unit tests for ActionsService
- [ ] Unit tests for GitHubContext
- [ ] Unit tests for remote URL parsing
- [ ] Test coverage >= 90%

### 11. Code Quality

- [ ] McCabe complexity <= 10 for all functions
- [ ] Type hints on all public methods
- [ ] Docstrings on all public classes/methods
- [ ] No circular imports
- [ ] Follows project code style

---

## Verification Commands

```bash
# Run unit tests
pytest tests/github/ -v

# Run with coverage
pytest tests/github/ --cov=src/opencode/github --cov-report=term-missing

# Check coverage threshold
pytest tests/github/ --cov=src/opencode/github --cov-fail-under=90

# Type checking
mypy src/opencode/github/

# Complexity check
flake8 src/opencode/github/ --max-complexity=10
```

---

## Test Scenarios

### Authentication Tests

```python
async def test_authenticate_with_valid_token(mock_http):
    mock_http.get(
        "https://api.github.com/user",
        json={"login": "alice", "id": 123},
        headers={"X-OAuth-Scopes": "repo, workflow"}
    )

    auth = GitHubAuthenticator("ghp_test_token")
    result = await auth.validate()

    assert result.username == "alice"
    assert "repo" in result.scopes


async def test_authenticate_from_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_env_token")

    auth = GitHubAuthenticator()
    assert auth.has_token is True


async def test_authentication_fails_with_invalid_token(mock_http):
    mock_http.get(
        "https://api.github.com/user",
        status=401,
        json={"message": "Bad credentials"}
    )

    auth = GitHubAuthenticator("invalid_token")

    with pytest.raises(GitHubAuthError) as exc:
        await auth.validate()

    assert "Invalid" in str(exc.value)
```

### API Client Tests

```python
async def test_get_request(mock_http, client):
    mock_http.get(
        "https://api.github.com/repos/owner/repo",
        json={"name": "repo", "full_name": "owner/repo"}
    )

    result = await client.get("/repos/owner/repo")

    assert result["name"] == "repo"


async def test_pagination(mock_http, client):
    mock_http.get(
        "https://api.github.com/repos/owner/repo/issues",
        json=[{"number": 1}, {"number": 2}],
        headers={"Link": '<...?page=2>; rel="next"'}
    )
    mock_http.get(
        "https://api.github.com/repos/owner/repo/issues?page=2",
        json=[{"number": 3}]
    )

    result = await client.get_paginated("/repos/owner/repo/issues")

    assert len(result) == 3


async def test_rate_limit_error(mock_http, client):
    mock_http.get(
        "https://api.github.com/repos/owner/repo",
        status=403,
        headers={"X-RateLimit-Remaining": "0"}
    )

    with pytest.raises(GitHubRateLimitError):
        await client.get("/repos/owner/repo")
```

### Repository Service Tests

```python
async def test_get_repository(mock_http, repo_service):
    mock_http.get(
        "https://api.github.com/repos/owner/repo",
        json={
            "name": "repo",
            "full_name": "owner/repo",
            "owner": {"login": "owner"},
            "default_branch": "main",
            # ... other fields
        }
    )

    repo = await repo_service.get("owner", "repo")

    assert repo.name == "repo"
    assert repo.default_branch == "main"


def test_parse_https_url():
    url = "https://github.com/owner/repo.git"
    result = RepositoryService.parse_remote_url(url)

    assert result == ("owner", "repo")


def test_parse_ssh_url():
    url = "git@github.com:owner/repo.git"
    result = RepositoryService.parse_remote_url(url)

    assert result == ("owner", "repo")
```

### Issue Service Tests

```python
async def test_list_issues(mock_http, issue_service):
    mock_http.get(
        "https://api.github.com/repos/owner/repo/issues",
        json=[
            {"number": 1, "title": "Bug", "user": {"login": "alice"}, ...},
            {"number": 2, "title": "Feature", "user": {"login": "bob"}, ...},
        ]
    )

    issues = await issue_service.list("owner", "repo")

    assert len(issues) == 2
    assert issues[0].number == 1


async def test_create_issue(mock_http, issue_service):
    mock_http.post(
        "https://api.github.com/repos/owner/repo/issues",
        json={"number": 42, "title": "New Issue", ...}
    )

    issue = await issue_service.create(
        "owner", "repo",
        title="New Issue",
        body="Description"
    )

    assert issue.number == 42
```

### Pull Request Service Tests

```python
async def test_list_prs(mock_http, pr_service):
    mock_http.get(
        "https://api.github.com/repos/owner/repo/pulls",
        json=[
            {"number": 1, "title": "Feature", "state": "open", ...},
        ]
    )

    prs = await pr_service.list("owner", "repo")

    assert len(prs) == 1
    assert prs[0].state == "open"


async def test_create_pr(mock_http, pr_service):
    mock_http.post(
        "https://api.github.com/repos/owner/repo/pulls",
        json={"number": 123, "html_url": "...", ...}
    )

    pr = await pr_service.create(
        "owner", "repo",
        title="New Feature",
        head="feature-branch",
        base="main"
    )

    assert pr.number == 123


async def test_merge_pr(mock_http, pr_service):
    mock_http.put(
        "https://api.github.com/repos/owner/repo/pulls/123/merge",
        json={"merged": True, "sha": "abc123"}
    )

    result = await pr_service.merge("owner", "repo", 123)

    assert result["merged"] is True
```

---

## Definition of Done

Phase 9.2 is complete when:

1. All checklist items are checked off
2. All unit tests pass
3. Test coverage is >= 90%
4. Code complexity is <= 10
5. Type checking passes with no errors
6. Token authentication works
7. Rate limiting is handled properly
8. Repository info retrieval works
9. Issue CRUD operations work
10. PR CRUD operations work
11. PR reviews work correctly
12. GitHub Actions status works
13. Error handling is graceful
14. GitHub context provided to LLM
15. Slash commands work correctly
16. Token is never logged or exposed
17. Documentation is complete
18. Code review approved

---

## Dependencies Verification

Before starting Phase 9.2, verify:

- [ ] Phase 9.1 (Git Integration) is complete
  - [ ] GitRepository can get remotes
  - [ ] Can parse remote URLs

- [ ] Phase 8.2 (Web Tools) is complete
  - [ ] HTTP client patterns established
  - [ ] Caching patterns available

- [ ] Phase 6.1 (Slash Commands) is complete
  - [ ] Slash command registration works

---

## Security Considerations

- [ ] Token never appears in logs
- [ ] Token never in error messages
- [ ] Token not displayed in UI
- [ ] Secure token storage
- [ ] Minimal required scopes
- [ ] Rate limit info sanitized

---

## Performance Requirements

| Operation | Max Time |
|-----------|----------|
| Authentication | 2s |
| Get repository | 2s |
| List issues (30) | 3s |
| List PRs (30) | 3s |
| Get single PR | 2s |
| Create issue | 3s |
| Create PR | 3s |

---

## Notes

- Focus on github.com, not GitHub Enterprise
- Use async/await for all API calls
- Implement pagination for list operations
- Track and expose rate limit info
- Cache responses where appropriate
- Token from environment is preferred
- Support both HTTPS and SSH remote URLs
