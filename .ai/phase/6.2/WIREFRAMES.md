# Phase 6.2: Operating Modes - Wireframes & Usage Examples

**Phase:** 6.2
**Name:** Operating Modes
**Dependencies:** Phase 1.3 (Basic REPL Shell), Phase 3.2 (LangChain Integration)

---

## 1. Mode Status Display

### Current Mode Indicator

```
You: /mode

Current Mode: normal
Description: Normal operating mode

Available modes:
  normal    - Default mode, no special behavior
  plan      - Structured planning mode
  thinking  - Extended reasoning mode
  headless  - Non-interactive automation mode

Use /mode <name> to switch modes.
```

### Plan Mode Active

```
[MODE: PLAN]
You: /mode

Current Mode: plan
Description: Structured planning mode

Plan mode creates actionable plans before implementation.
Use /plan show to see current plan.
Use /plan execute to start implementation.
Use /plan cancel to abort.
```

---

## 2. Plan Mode

### Entering Plan Mode

```
You: /plan

Entered plan mode. I'll create a structured plan before implementing.
Use /plan execute to implement, /plan cancel to abort.

[MODE: PLAN]
You: Add user authentication to the app
```

### Plan Generation

```
[MODE: PLAN]
You: Add user authentication to the app

## Plan: Add User Authentication

### Summary
Implement a complete authentication system with registration,
login, logout, and session management.

### Steps
1. [ ] Create user model and database schema
   - Files: models/user.py, migrations/001_users.py
   - Complexity: Low
   - Dependencies: None

2. [ ] Implement password hashing utilities
   - Files: utils/auth.py
   - Complexity: Low
   - Dependencies: Step 1

3. [ ] Create registration endpoint
   - Files: routes/auth.py, templates/register.html
   - Complexity: Medium
   - Dependencies: Steps 1, 2

4. [ ] Create login/logout endpoints
   - Files: routes/auth.py, templates/login.html
   - Complexity: Medium
   - Dependencies: Steps 1, 2

5. [ ] Add session middleware
   - Files: middleware/session.py, config.py
   - Complexity: Medium
   - Dependencies: Step 4

6. [ ] Implement protected route decorator
   - Files: utils/auth.py, routes/protected.py
   - Complexity: Low
   - Dependencies: Step 5

### Considerations
- Password hashing should use bcrypt or argon2
- Session tokens should be cryptographically secure
- Consider rate limiting on login attempts
- Add password reset flow in future iteration

### Success Criteria
- Users can register with email/password
- Users can log in and receive session token
- Protected routes require valid session
- Logout invalidates session

Ready to execute this plan?
Use /plan execute to begin, /plan show to review, or /plan cancel to abort.
```

### Show Current Plan

```
[MODE: PLAN]
You: /plan show

## Plan: Add User Authentication

Progress: 2/6 steps complete (33%)

### Steps
1. [x] Create user model and database schema
   - Completed

2. [x] Implement password hashing utilities
   - Completed

3. [ ] Create registration endpoint
   - Files: routes/auth.py, templates/register.html
   - Complexity: Medium
   - Dependencies: Steps 1, 2
   - Status: In Progress

4. [ ] Create login/logout endpoints
   - Pending

5. [ ] Add session middleware
   - Pending

6. [ ] Implement protected route decorator
   - Pending
```

### Execute Plan

```
[MODE: PLAN]
You: /plan execute

Executing plan: Add User Authentication

Created 6 todo items:
  1. Create user model and database schema
  2. Implement password hashing utilities
  3. Create registration endpoint
  4. Create login/logout endpoints
  5. Add session middleware
  6. Implement protected route decorator

Starting with Step 1: Create user model and database schema...

[Assistant proceeds with implementation]
```

### Cancel Plan

```
[MODE: PLAN]
You: /plan cancel

Plan cancelled: Add User Authentication
Exited plan mode.

You:
```

### Auto-Activation

```
You: Plan out how to refactor the database layer

I noticed you want to create a plan. Switching to plan mode...

[MODE: PLAN]

## Plan: Refactor Database Layer

### Summary
Restructure the database layer for better separation of concerns
and testability.

[... plan continues ...]
```

---

## 3. Thinking Mode

### Entering Thinking Mode

```
You: /think

Entered thinking mode.
I'll show my reasoning process in detail.

[MODE: THINKING]
You: Should we use a microservices or monolithic architecture?
```

### Thinking Response

```
[MODE: THINKING]
You: Should we use a microservices or monolithic architecture?

### Thinking Process

First, let me consider the key factors for this decision:

**Team Size & Structure**
- Smaller teams often benefit from monoliths (simpler deployment)
- Larger teams can parallelize with microservices
- Need to know current team size and growth plans

**System Complexity**
- Current system appears to be a web application
- Features seem moderately coupled
- No extreme scaling requirements mentioned

**Operational Maturity**
- Microservices require sophisticated DevOps
- Need container orchestration (K8s)
- Distributed tracing and monitoring
- Service mesh considerations

**Trade-off Analysis**
Monolith Pros:
- Simpler deployment pipeline
- Easier debugging and testing
- Lower operational overhead
- Faster initial development

Microservices Pros:
- Independent scaling of components
- Technology flexibility per service
- Fault isolation
- Team autonomy

Given typical startup/small team context, the operational
overhead of microservices often outweighs benefits early on.

---

Based on my analysis, I recommend starting with a **modular monolith**.

This gives you:
1. Clean module boundaries (future microservice candidates)
2. Simple deployment and operations
3. Easy local development
4. Option to extract services later when needed

The key is designing with clear module boundaries now, so extraction
to microservices is straightforward when scale demands it.

*Thinking time: 2.3s*
```

### Deep Thinking Mode

```
You: /think deep

Entered deep thinking mode for complex analysis.

[MODE: THINKING (DEEP)]
You: Compare REST vs GraphQL for our API

### Thinking Process

## Problem Analysis

The core question is which API paradigm best serves our needs.
Let me decompose this into component considerations:

**Data Requirements**
- Multiple client types (web, mobile, third-party)
- Data relationships are moderately nested
- Some views need aggregated data
- Real-time updates desired for some features

**Performance Considerations**
- Mobile clients are bandwidth-sensitive
- Over-fetching is currently problematic with REST
- Some endpoints return large payloads with unused fields

**Developer Experience**
- Team has REST experience
- GraphQL learning curve to consider
- Tooling ecosystem comparison needed

## Approaches Considered

### Approach 1: REST API
**Pros:**
- Team familiarity, faster initial development
- Well-understood caching strategies
- Simpler error handling
- Excellent tooling maturity

**Cons:**
- Over-fetching on complex views
- Endpoint proliferation for different use cases
- N+1 queries harder to optimize
- Multiple round-trips for nested data

### Approach 2: GraphQL API
**Pros:**
- Clients request exactly needed data
- Single endpoint, flexible queries
- Strong typing via schema
- Introspection for tooling

**Cons:**
- Learning curve for team
- Complex caching (no HTTP caching)
- Query complexity limits needed
- N+1 problems require dataloader pattern

### Approach 3: Hybrid (REST + GraphQL)
**Pros:**
- Use each where it fits best
- Gradual migration path
- Best of both worlds

**Cons:**
- Two systems to maintain
- Inconsistent API experience
- Doubled documentation effort

## Trade-off Analysis

| Criterion        | REST | GraphQL | Hybrid |
|------------------|------|---------|--------|
| Time to market   | +++  | +       | ++     |
| Flexibility      | +    | +++     | ++     |
| Performance      | ++   | +++     | ++     |
| Team experience  | +++  | +       | ++     |
| Maintenance      | ++   | ++      | +      |

## Recommendation

For your current situation, I recommend **GraphQL with REST fallback**.

Rationale:
1. Mobile bandwidth sensitivity makes GraphQL's precision valuable
2. Nested data requirements fit GraphQL's strengths
3. One team member has GraphQL experience (can mentor)
4. Keep simple CRUD operations as REST for familiarity

---

**Recommended approach: Implement GraphQL for complex, nested data needs
while maintaining REST endpoints for simple CRUD operations.**

Start with GraphQL for the dashboard views (most over-fetching pain),
then evaluate expanding coverage based on team comfort.

*Deep thinking time: 4.7s*
```

### Exit Thinking Mode

```
[MODE: THINKING]
You: /normal

Exited thinking mode.

You:
```

---

## 4. Headless Mode

### CLI Invocation

```bash
# Basic headless execution
$ forge --headless "Fix the syntax error in app.py"

{
  "status": "success",
  "message": "Fixed syntax error in app.py:42",
  "output": "Changed 'pritn' to 'print' on line 42",
  "exit_code": 0,
  "execution_time": 1.23
}

# With input file
$ forge --headless --input tasks.txt --output results.json

# JSON output format
$ forge --headless --json "Run the test suite"

{
  "status": "success",
  "message": "All 47 tests passed",
  "output": "...",
  "details": {
    "tests_run": 47,
    "tests_passed": 47,
    "tests_failed": 0
  },
  "exit_code": 0
}
```

### Headless with Safe Operations

```bash
$ forge --headless "Read the README and summarize it"

{
  "status": "success",
  "message": "README summarized",
  "output": "This project is a CLI tool for...",
  "exit_code": 0
}
```

### Headless with Unsafe Operations

```bash
$ forge --headless "Delete all test files"

{
  "status": "failure",
  "message": "Operation blocked - requires approval",
  "error": "Destructive operation 'delete files' not allowed in headless mode",
  "exit_code": 1
}
```

### Headless Timeout

```bash
$ forge --headless --timeout 30 "Complex analysis task"

{
  "status": "failure",
  "message": "Execution timed out",
  "error": "Task exceeded 30 second timeout",
  "exit_code": 2
}
```

### CI/CD Integration

```yaml
# GitHub Actions example
steps:
  - name: Run Code-Forge Analysis
    run: |
      forge --headless --json \
        "Review the changes in this PR for security issues" \
        > analysis.json

  - name: Check Results
    run: |
      if [ $(jq -r '.status' analysis.json) = "failure" ]; then
        echo "Security issues found!"
        exit 1
      fi
```

---

## 5. Mode Switching

### Quick Mode Switch

```
You: /mode plan

Switched to plan mode.
I'll create structured plans before implementing.

[MODE: PLAN]
You:
```

### Mode with Current State

```
[MODE: PLAN]
You: /mode thinking

Note: Current plan "Add Authentication" will be preserved.
Switched to thinking mode.

[MODE: THINKING]
You: /mode plan

Restored plan mode.
Current plan: Add Authentication (2/6 steps complete)

[MODE: PLAN]
You:
```

### List Modes

```
You: /mode list

Available Modes:

  normal (active)
    Default operating mode with no special behavior.

  plan
    Creates structured, actionable plans before implementation.
    Auto-activates on planning keywords.
    Commands: /plan, /plan show, /plan execute, /plan cancel

  thinking
    Extended reasoning mode for complex problems.
    Shows detailed thinking process.
    Commands: /think, /think deep

  headless
    Non-interactive mode for automation.
    Used via CLI --headless flag.
    No user prompts, structured output.
```

---

## 6. Mode Indicators in REPL

### Normal Mode (No Indicator)

```
You: Hello

Hello! How can I help you today?

You:
```

### Plan Mode Indicator

```
[MODE: PLAN]
You: Create the user model

Planning step: Create User Model...

[MODE: PLAN]
You:
```

### Thinking Mode Indicator

```
[MODE: THINKING]
You: Analyze this algorithm

### Thinking Process
[Detailed reasoning...]

---
[Final response]

*Thinking time: 1.8s*

[MODE: THINKING]
You:
```

### Nested Mode Display

```
[MODE: PLAN → THINKING]
You: Think about the best approach for step 3

### Thinking Process
For step 3 (Create registration endpoint)...

[MODE: PLAN → THINKING]
You: /normal

Returned to plan mode.

[MODE: PLAN]
You:
```

---

## 7. Error Handling

### Unknown Mode

```
You: /mode quantum

Unknown mode: quantum

Available modes: normal, plan, thinking, headless
```

### Mode Switch Failure

```
You: /mode headless

Cannot switch to headless mode interactively.
Use the --headless CLI flag instead.
```

### Plan Mode Without Plan

```
[MODE: PLAN]
You: /plan show

No plan created yet.
Describe a task and I'll create a plan.
```

### Invalid Plan Command

```
[MODE: PLAN]
You: /plan unknown

Unknown plan command: unknown

Available commands:
  /plan         - Enter plan mode
  /plan show    - Show current plan
  /plan execute - Execute current plan
  /plan cancel  - Cancel and exit plan mode
```

---

## 8. Session Persistence

### Mode Saved on Exit

```
[MODE: PLAN]
You: /exit

Session saved with:
  - Mode: plan
  - Current plan: Add Authentication (2/6 complete)

Goodbye!
```

### Mode Restored on Resume

```
$ forge --resume abc123

Resumed session: Add Authentication Feature
Mode restored: plan

[MODE: PLAN]

Current plan: Add Authentication
Progress: 2/6 steps complete

Continuing from Step 3: Create registration endpoint

You:
```

---

## 9. Integration Examples

### Plan to Todo Conversion

```
[MODE: PLAN]
You: /plan execute

Converting plan to todo items...

Todo List:
  1. [pending] Create user model and database schema
  2. [pending] Implement password hashing utilities
  3. [pending] Create registration endpoint
  4. [pending] Create login/logout endpoints
  5. [pending] Add session middleware
  6. [pending] Implement protected route decorator

Starting implementation...

[1/6] Creating user model and database schema...
```

### Thinking Suggestion

```
You: Compare React, Vue, and Angular for our frontend

This is a complex comparison with many trade-offs.
Would you like me to use thinking mode for deeper analysis?
Use /think to enable, or I'll provide a standard response.

You: /think

[MODE: THINKING]

### Thinking Process
Let me analyze each framework systematically...
```

---

## Notes

- Mode indicators appear in prompt when non-normal
- Plans are preserved when temporarily switching modes
- Headless mode requires CLI flag, not interactive command
- Auto-activation can be disabled in config
- Mode state persists across session resume
- Thinking time displayed for transparency
