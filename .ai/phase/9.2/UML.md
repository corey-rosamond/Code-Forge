# Phase 9.2: GitHub Integration - UML Diagrams

**Phase:** 9.2
**Name:** GitHub Integration
**Dependencies:** Phase 9.1 (Git Integration), Phase 8.2 (Web Tools)

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GitHub Integration System                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│          <<dataclass>>              │       │        GitHubAuthenticator          │
│           GitHubAuth                │       ├─────────────────────────────────────┤
├─────────────────────────────────────┤       │ - _token: str | None                │
│ + token: str                        │◄──────│ - _auth_info: GitHubAuth | None     │
│ + username: str                     │       │ - _validated: bool                  │
│ + scopes: list[str]                 │       ├─────────────────────────────────────┤
│ + rate_limit: int                   │       │ + has_token: bool                   │
│ + rate_remaining: int               │       │ + is_authenticated: bool            │
│ + rate_reset: int                   │       │ + validate(): GitHubAuth            │
├─────────────────────────────────────┤       │ + get_headers(): dict               │
│ + rate_reset_time: datetime         │       │ + update_rate_limit(limit, rem, rst)│
│ + is_rate_limited: bool             │       └─────────────────────────────────────┘
└─────────────────────────────────────┘
                                                              │
                                                              ▼
                              ┌─────────────────────────────────────────────────┐
                              │                  GitHubClient                    │
                              ├─────────────────────────────────────────────────┤
                              │ - auth: GitHubAuthenticator                     │
                              │ - timeout: ClientTimeout                        │
                              │ - max_retries: int                              │
                              │ - _session: ClientSession | None                │
                              ├─────────────────────────────────────────────────┤
                              │ + get(path, **params): dict                     │
                              │ + get_raw(path, accept): str                    │
                              │ + post(path, data): dict                        │
                              │ + patch(path, data): dict                       │
                              │ + put(path, data): dict                         │
                              │ + delete(path): None                            │
                              │ + get_paginated(path, per_page, max_pages): list│
                              │ + close(): None                                 │
                              └───────────────────────┬─────────────────────────┘
                                                      │
                    ┌─────────────────────────────────┼─────────────────────────────────┐
                    │                                 │                                 │
                    ▼                                 ▼                                 ▼
┌─────────────────────────────┐  ┌─────────────────────────────┐  ┌─────────────────────────────┐
│     RepositoryService       │  │       IssueService          │  │    PullRequestService       │
├─────────────────────────────┤  ├─────────────────────────────┤  ├─────────────────────────────┤
│ - client: GitHubClient      │  │ - client: GitHubClient      │  │ - client: GitHubClient      │
├─────────────────────────────┤  ├─────────────────────────────┤  ├─────────────────────────────┤
│ + get(owner, repo)          │  │ + list(owner, repo, ...)    │  │ + list(owner, repo, ...)    │
│ + list_branches(owner, repo)│  │ + get(owner, repo, number)  │  │ + get(owner, repo, number)  │
│ + get_branch(owner, repo)   │  │ + create(owner, repo, ...)  │  │ + create(owner, repo, ...)  │
│ + list_tags(owner, repo)    │  │ + update(owner, repo, ...)  │  │ + update(owner, repo, ...)  │
│ + get_readme(owner, repo)   │  │ + close(owner, repo, num)   │  │ + get_diff(owner, repo, num)│
│ + get_content(owner, repo)  │  │ + list_comments(...)        │  │ + get_files(owner, repo)    │
│ + parse_remote_url(url)     │  │ + add_comment(...)          │  │ + get_commits(owner, repo)  │
└─────────────────────────────┘  │ + add_labels(...)           │  │ + list_reviews(...)         │
                                 └─────────────────────────────┘  │ + create_review(...)        │
                                                                  │ + get_checks(owner, repo)   │
                                                                  │ + merge(owner, repo, ...)   │
                                                                  │ + request_reviewers(...)    │
                                                                  └─────────────────────────────┘

┌─────────────────────────────┐
│      ActionsService         │
├─────────────────────────────┤
│ - client: GitHubClient      │
├─────────────────────────────┤
│ + list_workflows(owner,repo)│
│ + list_runs(owner, repo)    │
│ + get_run(owner, repo, id)  │
│ + list_run_jobs(...)        │
│ + get_run_logs(...)         │
│ + rerun(owner, repo, id)    │
│ + rerun_failed(...)         │
│ + cancel(owner, repo, id)   │
│ + get_job_logs(...)         │
└─────────────────────────────┘
```

---

## Data Types Class Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GitHub Data Types                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│          <<dataclass>>              │       │          <<dataclass>>              │
│         GitHubRepository            │       │          GitHubBranch               │
├─────────────────────────────────────┤       ├─────────────────────────────────────┤
│ + owner: str                        │       │ + name: str                         │
│ + name: str                         │       │ + commit_sha: str                   │
│ + full_name: str                    │       │ + protected: bool                   │
│ + description: str | None           │       └─────────────────────────────────────┘
│ + private: bool                     │
│ + default_branch: str               │       ┌─────────────────────────────────────┐
│ + url: str                          │       │          <<dataclass>>              │
│ + clone_url: str                    │       │           GitHubTag                 │
│ + ssh_url: str                      │       ├─────────────────────────────────────┤
│ + language: str | None              │       │ + name: str                         │
│ + stars: int                        │       │ + commit_sha: str                   │
│ + forks: int                        │       │ + zipball_url: str                  │
│ + open_issues: int                  │       │ + tarball_url: str                  │
│ + archived: bool                    │       └─────────────────────────────────────┘
│ + topics: list[str]                 │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│          <<dataclass>>              │       │          <<dataclass>>              │
│           GitHubUser                │       │          GitHubLabel                │
├─────────────────────────────────────┤       ├─────────────────────────────────────┤
│ + login: str                        │       │ + name: str                         │
│ + id: int                           │       │ + color: str                        │
│ + avatar_url: str                   │       │ + description: str | None           │
│ + url: str                          │       └─────────────────────────────────────┘
│ + type: str                         │
└─────────────────────────────────────┘       ┌─────────────────────────────────────┐
                                              │          <<dataclass>>              │
                                              │        GitHubMilestone              │
                                              ├─────────────────────────────────────┤
                                              │ + number: int                       │
                                              │ + title: str                        │
                                              │ + description: str | None           │
                                              │ + state: str                        │
                                              │ + due_on: str | None                │
                                              └─────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          <<dataclass>> GitHubIssue                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ + number: int                                                               │
│ + title: str                                                                │
│ + body: str | None                                                          │
│ + state: str                                                                │
│ + state_reason: str | None                                                  │
│ + author: GitHubUser                                                        │
│ + assignees: list[GitHubUser]                                               │
│ + labels: list[GitHubLabel]                                                 │
│ + milestone: GitHubMilestone | None                                         │
│ + created_at: str                                                           │
│ + updated_at: str                                                           │
│ + closed_at: str | None                                                     │
│ + comments_count: int                                                       │
│ + url: str                                                                  │
│ + html_url: str                                                             │
│ + is_pull_request: bool                                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                       <<dataclass>> GitHubPullRequest                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ + number: int                    + head_ref: str                            │
│ + title: str                     + head_sha: str                            │
│ + body: str | None               + head_repo: str | None                    │
│ + state: str                     + base_ref: str                            │
│ + draft: bool                    + base_sha: str                            │
│ + merged: bool                   + created_at: str                          │
│ + mergeable: bool | None         + updated_at: str                          │
│ + mergeable_state: str | None    + merged_at: str | None                    │
│ + author: GitHubUser             + merged_by: GitHubUser | None             │
│ + assignees: list[GitHubUser]    + additions: int                           │
│ + requested_reviewers: list      + deletions: int                           │
│ + labels: list[GitHubLabel]      + changed_files: int                       │
│                                  + commits: int                             │
│                                  + html_url: str                            │
│                                  + diff_url: str                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│          <<dataclass>>              │       │          <<dataclass>>              │
│          GitHubReview               │       │       GitHubReviewComment           │
├─────────────────────────────────────┤       ├─────────────────────────────────────┤
│ + id: int                           │       │ + id: int                           │
│ + author: GitHubUser                │       │ + body: str                         │
│ + body: str | None                  │       │ + author: GitHubUser                │
│ + state: str                        │       │ + path: str                         │
│ + submitted_at: str | None          │       │ + position: int | None              │
│ + html_url: str                     │       │ + line: int | None                  │
└─────────────────────────────────────┘       │ + commit_id: str                    │
                                              │ + created_at: str                   │
                                              └─────────────────────────────────────┘

┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│          <<dataclass>>              │       │          <<dataclass>>              │
│         GitHubCheckRun              │       │          GitHubPRFile               │
├─────────────────────────────────────┤       ├─────────────────────────────────────┤
│ + id: int                           │       │ + filename: str                     │
│ + name: str                         │       │ + status: str                       │
│ + status: str                       │       │ + additions: int                    │
│ + conclusion: str | None            │       │ + deletions: int                    │
│ + started_at: str | None            │       │ + changes: int                      │
│ + completed_at: str | None          │       │ + patch: str | None                 │
│ + url: str                          │       │ + blob_url: str                     │
│ + html_url: str | None              │       │ + raw_url: str                      │
│ + app_name: str | None              │       └─────────────────────────────────────┘
└─────────────────────────────────────┘

┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│          <<dataclass>>              │       │          <<dataclass>>              │
│           Workflow                  │       │          WorkflowRun                │
├─────────────────────────────────────┤       ├─────────────────────────────────────┤
│ + id: int                           │       │ + id: int                           │
│ + name: str                         │       │ + name: str                         │
│ + path: str                         │       │ + workflow_id: int                  │
│ + state: str                        │       │ + status: str                       │
│ + created_at: str                   │       │ + conclusion: str | None            │
│ + updated_at: str                   │       │ + event: str                        │
│ + url: str                          │       │ + head_branch: str                  │
│ + html_url: str                     │       │ + head_sha: str                     │
└─────────────────────────────────────┘       │ + run_number: int                   │
                                              │ + created_at: str                   │
                                              │ + html_url: str                     │
                                              └─────────────────────────────────────┘
```

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            GitHub Integration                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐                                     │
│  │    auth      │     │   client     │                                     │
│  │    .py       │────▶│    .py       │                                     │
│  │              │     │              │                                     │
│  │ Authenticator│     │ GitHubClient │                                     │
│  │  GitHubAuth  │     │  API calls   │                                     │
│  └──────────────┘     └──────┬───────┘                                     │
│                              │                                              │
│         ┌────────────────────┼────────────────────┐                        │
│         │                    │                    │                        │
│         ▼                    ▼                    ▼                        │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐               │
│  │ repository   │     │   issues     │     │pull_requests │               │
│  │    .py       │     │    .py       │     │    .py       │               │
│  │              │     │              │     │              │               │
│  │RepoService   │     │IssueService  │     │  PRService   │               │
│  │GitHubRepo    │     │GitHubIssue   │     │GitHubPR      │               │
│  │GitHubBranch  │     │GitHubComment │     │GitHubReview  │               │
│  └──────────────┘     └──────────────┘     └──────────────┘               │
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐                                     │
│  │  actions     │     │   context    │                                     │
│  │    .py       │     │    .py       │                                     │
│  │              │     │              │                                     │
│  │ActionsService│     │GitHubContext │                                     │
│  │WorkflowRun   │     │  formatting  │                                     │
│  │WorkflowJob   │     │  for LLM     │                                     │
│  └──────────────┘     └──────────────┘                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │       GitHub REST API         │
                    │     api.github.com            │
                    └───────────────────────────────┘
```

---

## Sequence Diagram: Authentication Flow

```
┌─────────┐     ┌──────────────────┐     ┌──────────────┐     ┌─────────────┐
│  User   │     │GitHubAuthenticator│    │   aiohttp    │     │ GitHub API  │
└────┬────┘     └────────┬─────────┘     └──────┬───────┘     └──────┬──────┘
     │                   │                      │                     │
     │ Initialize with   │                      │                     │
     │ token or env      │                      │                     │
     │──────────────────▶│                      │                     │
     │                   │                      │                     │
     │                   │ [Check env vars]     │                     │
     │                   │ GITHUB_TOKEN or      │                     │
     │                   │ GH_TOKEN             │                     │
     │                   │                      │                     │
     │   validate()      │                      │                     │
     │──────────────────▶│                      │                     │
     │                   │                      │                     │
     │                   │ GET /user            │                     │
     │                   │─────────────────────▶│                     │
     │                   │                      │                     │
     │                   │                      │ Authorization:      │
     │                   │                      │ Bearer <token>      │
     │                   │                      │────────────────────▶│
     │                   │                      │                     │
     │                   │                      │  200 OK             │
     │                   │                      │  { "login": "...",  │
     │                   │                      │    "id": ... }      │
     │                   │                      │◀────────────────────│
     │                   │                      │                     │
     │                   │  Response + headers  │                     │
     │                   │◀─────────────────────│                     │
     │                   │                      │                     │
     │                   │  [Parse X-OAuth-Scopes]                    │
     │                   │  [Parse X-RateLimit-*]                     │
     │                   │                      │                     │
     │   GitHubAuth      │                      │                     │
     │   (username,      │                      │                     │
     │    scopes,        │                      │                     │
     │    rate limits)   │                      │                     │
     │◀──────────────────│                      │                     │
     │                   │                      │                     │
```

---

## Sequence Diagram: List Issues with Pagination

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│  User   │     │ IssueService │     │ GitHubClient │     │ GitHub API  │
└────┬────┘     └──────┬───────┘     └──────┬───────┘     └──────┬──────┘
     │                 │                    │                     │
     │  list(owner,    │                    │                     │
     │   repo,         │                    │                     │
     │   state="open") │                    │                     │
     │────────────────▶│                    │                     │
     │                 │                    │                     │
     │                 │  get_paginated(    │                     │
     │                 │   "/repos/.../     │                     │
     │                 │    issues",        │                     │
     │                 │   state="open")    │                     │
     │                 │───────────────────▶│                     │
     │                 │                    │                     │
     │                 │                    │  GET /repos/.../    │
     │                 │                    │  issues?page=1&     │
     │                 │                    │  per_page=30&       │
     │                 │                    │  state=open         │
     │                 │                    │────────────────────▶│
     │                 │                    │                     │
     │                 │                    │  200 OK             │
     │                 │                    │  [30 issues]        │
     │                 │                    │  Link: <...page=2>  │
     │                 │                    │◀────────────────────│
     │                 │                    │                     │
     │                 │                    │  [Check Link header]│
     │                 │                    │  [has rel="next"]   │
     │                 │                    │                     │
     │                 │                    │  GET /repos/.../    │
     │                 │                    │  issues?page=2&...  │
     │                 │                    │────────────────────▶│
     │                 │                    │                     │
     │                 │                    │  200 OK             │
     │                 │                    │  [15 issues]        │
     │                 │                    │  (no next link)     │
     │                 │                    │◀────────────────────│
     │                 │                    │                     │
     │                 │  all_items (45)    │                     │
     │                 │◀───────────────────│                     │
     │                 │                    │                     │
     │                 │  [Filter out PRs]  │                     │
     │                 │  [Parse to         │                     │
     │                 │   GitHubIssue]     │                     │
     │                 │                    │                     │
     │ list[GitHubIssue]                    │                     │
     │◀────────────────│                    │                     │
     │                 │                    │                     │
```

---

## Sequence Diagram: Create Pull Request

```
┌─────────┐     ┌────────────────┐     ┌──────────────┐     ┌─────────────┐
│  User   │     │PullRequestSvc  │     │ GitHubClient │     │ GitHub API  │
└────┬────┘     └───────┬────────┘     └──────┬───────┘     └──────┬──────┘
     │                  │                     │                     │
     │  create(owner,   │                     │                     │
     │   repo, title,   │                     │                     │
     │   head, base,    │                     │                     │
     │   body)          │                     │                     │
     │─────────────────▶│                     │                     │
     │                  │                     │                     │
     │                  │  post("/repos/      │                     │
     │                  │   .../pulls",       │                     │
     │                  │   { title, head,    │                     │
     │                  │     base, body })   │                     │
     │                  │────────────────────▶│                     │
     │                  │                     │                     │
     │                  │                     │  POST /repos/.../   │
     │                  │                     │  pulls              │
     │                  │                     │  { "title": "...",  │
     │                  │                     │    "head": "...",   │
     │                  │                     │    "base": "...",   │
     │                  │                     │    "body": "..." }  │
     │                  │                     │────────────────────▶│
     │                  │                     │                     │
     │                  │                     │  201 Created        │
     │                  │                     │  { "number": 42,    │
     │                  │                     │    "html_url": ..., │
     │                  │                     │    ... }            │
     │                  │                     │◀────────────────────│
     │                  │                     │                     │
     │                  │  PR data            │                     │
     │                  │◀────────────────────│                     │
     │                  │                     │                     │
     │                  │  [Parse to          │                     │
     │                  │   GitHubPullRequest]│                     │
     │                  │                     │                     │
     │  GitHubPullRequest                     │                     │
     │  (number=42,     │                     │                     │
     │   html_url=...)  │                     │                     │
     │◀─────────────────│                     │                     │
     │                  │                     │                     │
```

---

## Sequence Diagram: Handle Rate Limiting

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│  User   │     │ GitHubClient │     │   aiohttp    │     │ GitHub API  │
└────┬────┘     └──────┬───────┘     └──────┬───────┘     └──────┬──────┘
     │                 │                    │                     │
     │  get("/repos")  │                    │                     │
     │────────────────▶│                    │                     │
     │                 │                    │                     │
     │                 │  request(GET, ...) │                     │
     │                 │───────────────────▶│                     │
     │                 │                    │                     │
     │                 │                    │  GET /repos/...     │
     │                 │                    │────────────────────▶│
     │                 │                    │                     │
     │                 │                    │  403 Forbidden      │
     │                 │                    │  X-RateLimit-       │
     │                 │                    │  Remaining: 0       │
     │                 │                    │◀────────────────────│
     │                 │                    │                     │
     │                 │  response          │                     │
     │                 │◀───────────────────│                     │
     │                 │                    │                     │
     │                 │ [Check status 403] │                     │
     │                 │ [Check Remaining=0]│                     │
     │                 │                    │                     │
     │                 │ [Update rate limit │                     │
     │                 │  info in auth]     │                     │
     │                 │                    │                     │
     │  GitHubRate     │                    │                     │
     │  LimitError     │                    │                     │
     │  "Rate limit    │                    │                     │
     │   exceeded"     │                    │                     │
     │◀────────────────│                    │                     │
     │                 │                    │                     │
```

---

## State Diagram: Pull Request States

```
                           ┌─────────────────┐
                           │                 │
                           │     Draft       │
                           │                 │
                           └────────┬────────┘
                                    │
                          Ready for Review
                                    │
                                    ▼
┌─────────────┐           ┌─────────────────┐
│             │           │                 │
│   Closed    │◀──────────│      Open       │◀──────────┐
│             │   Close   │                 │           │
└─────────────┘           └────────┬────────┘           │
      │                            │                    │
      │                   ┌────────┴────────┐           │
      │                   │                 │           │
      │            Merge  │          Request Changes    │
      │                   │                 │           │
      │                   ▼                 ▼           │
      │          ┌─────────────────┐ ┌─────────────────┐│
      │          │                 │ │                 ││
      │          │     Merged      │ │Changes Requested││
      │          │                 │ │                 ││
      │          └─────────────────┘ └────────┬────────┘│
      │                                       │         │
      │                                 Push Changes    │
      │                                       │         │
      │                                       └─────────┘
      │
      │   Reopen
      └─────────────────────────────────────────────────┐
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │                 │
                                              │      Open       │
                                              │   (reopened)    │
                                              │                 │
                                              └─────────────────┘
```

---

## Activity Diagram: PR Review Workflow

```
                        ┌─────────────────┐
                        │  PR Created     │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │Request Reviewers│
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Await Review   │
                        └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
           ┌────────────┐ ┌────────────┐ ┌────────────┐
           │  Approve   │ │  Comment   │ │  Request   │
           │            │ │            │ │  Changes   │
           └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
                 │              │              │
                 │              │              ▼
                 │              │      ┌────────────────┐
                 │              │      │  Push Fixes    │
                 │              │      └───────┬────────┘
                 │              │              │
                 │              └──────────────┤
                 │                             │
                 │                             ▼
                 │                     ┌────────────────┐
                 │                     │  Re-request    │
                 │                     │   Review       │
                 │                     └───────┬────────┘
                 │                             │
                 │◀────────────────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  Check Status   │
        └────────┬────────┘
                 │
        ┌────────┴────────┐
        │                 │
    Passing           Failing
        │                 │
        ▼                 ▼
┌────────────────┐ ┌────────────────┐
│     Merge      │ │   Fix Checks   │
└────────┬───────┘ └───────┬────────┘
         │                 │
         ▼                 │
┌────────────────┐         │
│    Merged!     │◀────────┘
└────────────────┘
```

---

## Integration with Git (Phase 9.1)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Code-Forge Git + GitHub                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────┐       ┌───────────────────────────────┐
│        Git Integration        │       │      GitHub Integration       │
│         (Phase 9.1)           │       │         (Phase 9.2)           │
├───────────────────────────────┤       ├───────────────────────────────┤
│                               │       │                               │
│  ┌─────────────────────────┐  │       │  ┌─────────────────────────┐  │
│  │    GitRepository        │  │       │  │  RepositoryService      │  │
│  │    get_remotes()       ─┼──┼───────┼─▶│  parse_remote_url()     │  │
│  └─────────────────────────┘  │       │  └─────────────────────────┘  │
│                               │       │                               │
│  ┌─────────────────────────┐  │       │  ┌─────────────────────────┐  │
│  │    GitOperations        │  │       │  │  PullRequestService     │  │
│  │    push()              ─┼──┼───────┼─▶│  create()               │  │
│  └─────────────────────────┘  │       │  └─────────────────────────┘  │
│                               │       │                               │
│  ┌─────────────────────────┐  │       │  ┌─────────────────────────┐  │
│  │    GitDiffTool          │  │       │  │  PullRequestService     │  │
│  │    diff_branches()     ─┼──┼───────┼─▶│  get_diff()             │  │
│  └─────────────────────────┘  │       │  └─────────────────────────┘  │
│                               │       │                               │
└───────────────────────────────┘       └───────────────────────────────┘
```

---

## Notes

- All API calls use async/await pattern
- Rate limiting tracked and handled
- Pagination handled automatically
- Token never logged or exposed
- Data classes provide type safety
- Services follow single responsibility principle
