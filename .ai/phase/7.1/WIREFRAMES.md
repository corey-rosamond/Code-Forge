# Phase 7.1: Subagents System - Wireframes & Usage Examples

**Phase:** 7.1
**Name:** Subagents System
**Dependencies:** Phase 3.2 (LangChain Integration), Phase 2.1 (Tool System)

---

## 1. Agent Spawning from REPL

### Implicit Agent Spawning

```
You: Find all files that handle authentication in this codebase

Spawning explore agent...

[Agent: explore-a1b2c3]
Searching for authentication-related files...
  - Found auth/login.py
  - Found auth/session.py
  - Found middleware/auth.py
  - Found tests/test_auth.py

Agent completed (4.2s, 3,500 tokens)

I found 4 files related to authentication:

1. **auth/login.py** - Main login/logout handlers
2. **auth/session.py** - Session management
3. **middleware/auth.py** - Auth middleware for protected routes
4. **tests/test_auth.py** - Authentication tests

Would you like me to examine any of these in detail?
```

### Explicit Agent Spawning

```
You: /agent explore "Find all API endpoints"

Spawned agent: explore-d4e5f6
Task: Find all API endpoints
Status: Running...

You: /agent status

Active Agents (1):

  explore-d4e5f6 [RUNNING]
    Task: Find all API endpoints
    Started: 5 seconds ago
    Tokens: 1,200
    Tool calls: 8
```

---

## 2. Agent Status Display

### Single Agent Status

```
You: /agent status d4e5

Agent: explore-d4e5f6
Type: explore
State: RUNNING
Task: Find all API endpoints

Started: 2024-01-15 10:30:45
Running: 12 seconds

Resource Usage:
  Tokens: 2,450 / 30,000 (8.2%)
  Tool Calls: 15 / 100 (15%)
  Time: 12s / 180s (6.7%)

Recent Activity:
  [10:30:57] Executed grep for "@app.route"
  [10:30:56] Executed glob for "*.py"
  [10:30:55] Executed read on routes/api.py
```

### All Agents Status

```
You: /agent list

Agents (3 total):

  explore-a1b2c3 [COMPLETED]
    Find auth files
    Completed 2 minutes ago
    Result: Found 4 files

  explore-d4e5f6 [RUNNING]
    Find API endpoints
    Running for 15 seconds
    Progress: 2,500 tokens used

  plan-g7h8i9 [PENDING]
    Create implementation plan
    Waiting in queue
```

---

## 3. Parallel Agent Execution

### Spawning Multiple Agents

```
You: I need to understand this codebase. Explore the models, routes, and utils.

Spawning 3 parallel agents...

[Agent: explore-models]  Started
[Agent: explore-routes]  Started
[Agent: explore-utils]   Started

---

[Agent: explore-models] COMPLETED (3.1s)
Found 5 model files:
  - models/user.py
  - models/post.py
  - models/comment.py
  - models/tag.py
  - models/base.py

---

[Agent: explore-routes] COMPLETED (4.2s)
Found 8 route modules:
  - routes/auth.py
  - routes/users.py
  - routes/posts.py
  - routes/comments.py
  ...

---

[Agent: explore-utils] COMPLETED (2.8s)
Found 6 utility modules:
  - utils/auth.py
  - utils/validators.py
  - utils/formatters.py
  ...

---

All agents completed.

## Codebase Summary

**Models (5 files)**
The models use SQLAlchemy ORM with a base model pattern...

**Routes (8 files)**
RESTful API routes organized by resource...

**Utilities (6 files)**
Helper functions for validation, formatting, and auth...
```

---

## 4. Agent Results

### Explore Agent Result

```
[Agent: explore-a1b2c3] COMPLETED

## Findings

### Files Found (4)
| File | Relevance | Description |
|------|-----------|-------------|
| auth/login.py | High | Login/logout handlers |
| auth/session.py | High | Session management |
| middleware/auth.py | Medium | Auth middleware |
| tests/test_auth.py | Low | Test file |

### Key Observations
- Authentication uses JWT tokens
- Sessions stored in Redis
- Middleware checks on all /api routes

### Code Snippets

**auth/login.py:45**
```python
def login_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return create_access_token(user.id)
```

Resource Usage:
  Tokens: 3,500
  Time: 4.2s
  Tool Calls: 15
```

### Plan Agent Result

```
[Agent: plan-g7h8i9] COMPLETED

## Implementation Plan: Add Email Verification

### Summary
Add email verification for new user registrations with
confirmation link and verification status tracking.

### Steps

1. [ ] Add email_verified column to User model
   - Files: models/user.py, migrations/
   - Complexity: Low
   - Dependencies: None

2. [ ] Create email service for sending verification
   - Files: services/email.py
   - Complexity: Medium
   - Dependencies: None

3. [ ] Add verification token generation
   - Files: utils/tokens.py
   - Complexity: Low
   - Dependencies: Step 1

4. [ ] Create verification endpoint
   - Files: routes/auth.py
   - Complexity: Medium
   - Dependencies: Steps 1, 2, 3

5. [ ] Update registration to send verification email
   - Files: routes/auth.py, services/email.py
   - Complexity: Medium
   - Dependencies: Steps 1, 2

6. [ ] Add verification check to protected routes
   - Files: middleware/auth.py
   - Complexity: Low
   - Dependencies: Step 1

### Considerations
- Token expiration (suggest 24 hours)
- Rate limiting on resend
- Graceful handling of email service failures

Resource Usage:
  Tokens: 5,200
  Time: 8.5s
  Tool Calls: 22
```

### Code Review Agent Result

```
[Agent: review-j0k1l2] COMPLETED

## Code Review: PR #123

### Critical Issues (1)

**SQL Injection Vulnerability**
- File: routes/search.py:45
- Severity: CRITICAL
- Finding: Raw SQL query with user input
```python
# Vulnerable code
query = f"SELECT * FROM posts WHERE title LIKE '%{search_term}%'"
```
- Suggestion: Use parameterized query
```python
query = "SELECT * FROM posts WHERE title LIKE :term"
db.execute(query, {"term": f"%{search_term}%"})
```

### Warnings (2)

**Missing Input Validation**
- File: routes/users.py:78
- Severity: WARNING
- Finding: Email not validated before database insert

**Hardcoded Secret**
- File: config.py:12
- Severity: WARNING
- Finding: API key in source code

### Suggestions (3)

1. Add type hints to new functions
2. Consider adding docstrings
3. Test coverage could be improved

### Overall Assessment
The PR has 1 critical issue that must be fixed before merge.
Address the SQL injection vulnerability and consider the
warnings for improved security.

Resource Usage:
  Tokens: 4,800
  Time: 6.3s
  Tool Calls: 18
```

---

## 5. Agent Commands

### List Available Agent Types

```
You: /agent types

Available Agent Types:

  explore
    Explores codebase to answer questions
    Default tools: glob, grep, read
    Max tokens: 30,000
    Max time: 180s

  plan
    Creates implementation plans
    Default tools: glob, grep, read
    Max tokens: 40,000
    Max time: 240s

  code-review
    Reviews code changes for issues
    Default tools: glob, grep, read, bash
    Max tokens: 40,000
    Max time: 300s

  general
    General purpose agent for any task
    Default tools: all
    Max tokens: 50,000
    Max time: 300s
```

### Spawn Specific Agent Type

```
You: /agent spawn plan "Add user notifications"

Spawned agent: plan-m2n3o4
Type: plan
Task: Add user notifications
Status: Running...
```

### Cancel Agent

```
You: /agent cancel m2n3

Cancelling agent plan-m2n3o4...
Agent cancelled.

Partial result saved.
Tokens used: 2,100
Time: 15.3s
```

### Wait for Agent

```
You: /agent wait m2n3

Waiting for agent plan-m2n3o4...

[Progress updates shown as agent works]

Agent completed.
[Shows result]
```

---

## 6. Resource Limits

### Limit Warning

```
[Agent: explore-p5q6r7]

WARNING: Approaching token limit
  Used: 27,500 / 30,000 (91.7%)

Agent wrapping up to stay within limits...

---

[Agent: explore-p5q6r7] COMPLETED

Note: Agent stopped early due to token limit.
Partial results returned.

Found 12 of approximately 20 matching files.
```

### Limit Exceeded

```
[Agent: explore-s8t9u0]

ERROR: Token limit exceeded
  Used: 30,500 / 30,000 (101.7%)

Agent terminated.

Partial findings before limit:
  - Found 8 files
  - Analyzed 5 in detail

To continue, spawn a new agent with higher limits:
  /agent spawn explore "..." --max-tokens 50000
```

### Timeout

```
[Agent: plan-v1w2x3]

ERROR: Execution timeout
  Time: 300s / 300s (100%)

Agent terminated.

Partial plan before timeout:
  - 4 of 6 steps completed
  - Use /agent resume v1w2 to continue
```

---

## 7. Agent History

### View Agent History

```
You: /agent history

Recent Agents (last 10):

  2024-01-15 10:45:23  explore-a1b2c3  COMPLETED
    Find auth files
    4.2s | 3,500 tokens

  2024-01-15 10:42:15  plan-d4e5f6  COMPLETED
    Add notifications
    8.5s | 5,200 tokens

  2024-01-15 10:38:02  review-g7h8i9  FAILED
    Review PR #123
    Error: API rate limit

  ...
```

### View Specific Agent History

```
You: /agent history a1b2

Agent: explore-a1b2c3

Created: 2024-01-15 10:45:23
Completed: 2024-01-15 10:45:27
Duration: 4.2s

Task: Find auth files

Config:
  Type: explore
  Max Tokens: 30,000
  Max Time: 180s
  Tools: glob, grep, read

Usage:
  Tokens: 3,500
  Tool Calls: 15
  Iterations: 8

Result: SUCCESS
  Found 4 files related to authentication
```

---

## 8. Agent Statistics

```
You: /agent stats

Agent Statistics (This Session):

Total Agents: 12
  Completed: 10
  Failed: 1
  Cancelled: 1

Resource Usage:
  Total Tokens: 45,230
  Total Time: 78.5s
  Total Tool Calls: 156

By Type:
  explore: 6 agents
  plan: 4 agents
  code-review: 1 agent
  general: 1 agent

Success Rate: 83.3%
Avg Time: 6.5s
Avg Tokens: 3,769
```

---

## 9. Error Handling

### Agent Failure

```
[Agent: explore-y4z5a6]

ERROR: Agent execution failed

Error: Unable to read file - permission denied
  File: /root/secret.txt

Agent terminated with partial results.

Completed work:
  - Found 3 files before error
  - Results saved

Troubleshooting:
  - Check file permissions
  - Agent only has access to current directory
```

### Connection Error

```
[Agent: plan-b7c8d9]

ERROR: API connection failed

Error: OpenRouter API timeout after 30s

Agent paused. Options:
  /agent retry b7c8 - Retry from last checkpoint
  /agent cancel b7c8 - Cancel agent
```

---

## 10. Integration Example

### Complex Task with Multiple Agents

```
You: Help me understand and improve the authentication system

I'll analyze the authentication system using specialized agents.

---

Spawning exploration agent...

[Agent: explore-auth] COMPLETED (5.2s)
Found authentication components:
  - 4 auth-related files
  - JWT-based authentication
  - Redis session storage

---

Spawning code review agent...

[Agent: review-auth] COMPLETED (8.1s)
Found 2 security issues:
  - Token expiration too long (30 days)
  - Missing rate limiting on login

---

Spawning planning agent...

[Agent: plan-improve-auth] COMPLETED (6.8s)
Created improvement plan with 5 steps

---

## Summary

### Current State
Your authentication uses JWT tokens stored in Redis.
I found 2 security concerns that should be addressed.

### Security Issues
1. **Token expiration** - Currently 30 days, recommend 24 hours
2. **Rate limiting** - No protection against brute force

### Improvement Plan
1. Reduce token expiration to 24 hours
2. Add refresh token mechanism
3. Implement login rate limiting
4. Add failed attempt tracking
5. Add account lockout after X failures

Would you like me to implement any of these improvements?
```

---

## Notes

- Agents run autonomously in the background
- Progress updates shown in real-time
- Results formatted based on agent type
- Resource limits prevent runaway agents
- Parallel execution for faster results
- History preserved for reference
