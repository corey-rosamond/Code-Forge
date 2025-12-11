# Code-Forge: Current Work

**Last Updated:** 2025-12-12

---

## Active Tasks

_No active tasks._

---

## Recently Completed (P0)

#### BUG-001: ReadTool Line Limit Broken
**Status:** ✅ Fixed (2025-12-12)
**File:** `src/code_forge/tools/file/read.py:158`
**Fix:** Changed `continue` to `break` to stop reading after limit reached

#### SEC-001: No SSRF Protection in URL Fetcher
**Status:** ✅ Fixed (2025-12-12)
**File:** `src/code_forge/web/fetch/fetcher.py`
**Fix:** Added `validate_url_host()` with private IP range detection (127.x, 10.x, 172.16.x, 192.168.x, 169.254.x, IPv6 private)

#### SEC-002: API Keys Exposed in Logs/Repr
**Status:** ✅ Fixed (2025-12-12)
**Files:** `src/code_forge/github/auth.py`, `src/code_forge/web/config.py`
**Fix:** Wrapped token fields with `pydantic.SecretStr`, masked in `to_dict()` output

#### PERF-001: Agent Makes Double API Calls
**Status:** ✅ Fixed (2025-12-12)
**File:** `src/code_forge/langchain/agent.py`
**Fix:** Added `_assemble_tool_calls()` method to build tool calls from streamed chunks instead of re-calling API

#### PERF-002: Unbounded Shell Output Buffers
**Status:** ✅ Fixed (2025-12-12)
**File:** `src/code_forge/tools/execution/shell_manager.py`
**Fix:** Added `MAX_BUFFER_SIZE` (10MB) and `_append_to_buffer()` with circular buffer behavior

---

## Backlog

### High Priority (P1)

#### ARCH-001: Duplicate Type Definitions
**Status:** Pending
**Files:** `src/code_forge/core/types.py` vs `src/code_forge/tools/base.py`
**Issue:** `ToolParameter` and `ToolResult` defined twice with different features
**Impact:** Maintenance burden, potential import confusion, DRY violation
**Fix:** Consolidate into core/types.py, import in tools/base.py

#### ARCH-002: Core Interfaces Not Implemented
**Status:** Pending
**File:** `src/code_forge/core/interfaces.py`
**Issue:** `ITool`, `IModelProvider`, `ISessionRepository` defined but never used
**Impact:** Abstractions are theoretical, not enforced
**Fix:** Make concrete classes implement interfaces or remove unused interfaces

#### ARCH-003: Tight Coupling in CLI Entry Point
**Status:** Pending
**File:** `src/code_forge/cli/main.py`
**Issue:** Direct instantiation of ConfigLoader, OpenRouterClient, etc.
**Impact:** Hard to test, difficult to swap implementations
**Fix:** Implement dependency injection pattern

#### ARCH-004: Configuration System Fragmentation
**Status:** Pending
**Files:** `config/`, `mcp/config.py`, `hooks/config.py`, `permissions/config.py`, `web/config.py`
**Issue:** 6+ modules use different config patterns (Pydantic vs dataclass vs custom)
**Impact:** Inconsistent API, hard to compose/test configurations
**Fix:** Standardize on Pydantic models with common base class

#### TOOL-001: Timeout Units Inconsistent
**Status:** Pending
**Files:** `src/code_forge/tools/execution/bash.py`, `src/code_forge/tools/base.py`
**Issue:** BashTool uses milliseconds, ExecutionContext uses seconds
**Impact:** Developer confusion, potential timeout bugs
**Fix:** Standardize on seconds throughout, update documentation

#### TOOL-002: Missing JSON Error Handling in Notebook Read
**Status:** Pending
**File:** `src/code_forge/tools/file/read.py:253-254`
**Issue:** `_read_notebook` has no try-except for `json.JSONDecodeError`
**Impact:** Malformed .ipynb files cause unhandled exceptions
**Fix:** Add proper exception handling with user-friendly error message

#### TOOL-003: Glob Pattern Can Escape Working Directory
**Status:** Pending
**File:** `src/code_forge/tools/file/glob.py:112-115`
**Issue:** Absolute patterns like `/etc/*` can enumerate any directory
**Impact:** Information disclosure outside intended scope
**Fix:** Validate patterns stay within base_path

#### TOOL-004: Symlink Parameter Creates Escape Route
**Status:** Pending
**File:** `src/code_forge/tools/file/utils.py:47`
**Issue:** `allow_symlinks=True` parameter enables path traversal via symlinks
**Impact:** Potential security bypass (currently all callers use safe default)
**Fix:** Remove parameter entirely or deprecate it

#### LLM-001: Streaming Errors Silently Skipped
**Status:** Pending
**File:** `src/code_forge/llm/client.py:211-212`
**Issue:** JSON parse failures during streaming just logged as warning
**Impact:** Data loss, incomplete responses without notification
**Fix:** Propagate errors or provide mechanism to detect incomplete streams

#### LLM-002: Thread Cleanup Timeout Too Short
**Status:** Pending
**File:** `src/code_forge/langchain/llm.py:260`
**Issue:** 1-second timeout for producer thread join may orphan threads
**Impact:** Resource leaks, orphaned background threads
**Fix:** Increase timeout or implement proper cancellation

#### LLM-003: Token Counter Race Condition
**Status:** Pending
**File:** `src/code_forge/llm/client.py:204-208`
**Issue:** Concurrent streams update token counts without locking
**Impact:** Inaccurate token/cost tracking
**Fix:** Add threading lock around counter updates

#### LLM-004: Tool Execution Has No Timeout
**Status:** Pending
**File:** `src/code_forge/langchain/agent.py:216-249`
**Issue:** LLM calls have iteration_timeout, but tool execution can hang forever
**Impact:** Agent can hang indefinitely on slow tools
**Fix:** Apply timeout to tool execution within agent loop

---

### Medium Priority (P2)

#### CLI-001: No Stdin/Batch Input Support
**Status:** Pending
**File:** `src/code_forge/cli/main.py`
**Issue:** No support for `echo "fix bug" | forge` or `forge < script.txt`
**Impact:** Can't use in automation pipelines
**Fix:** Add stdin detection and batch mode

#### CLI-002: No Output Format Options
**Status:** Pending
**File:** `src/code_forge/cli/repl.py`
**Issue:** No `--json`, `--no-color`, `-q` quiet mode options
**Impact:** Hard to integrate with other tools
**Fix:** Add output format flags to CLI

#### CLI-003: Generic Error Messages
**Status:** Pending
**Files:** `src/code_forge/cli/main.py:54-60`, `src/code_forge/commands/parser.py`
**Issue:** Errors don't explain what went wrong or how to fix
**Impact:** Poor user experience
**Fix:** Add context-specific error messages with suggestions

#### CLI-004: No Command Timeout Handling
**Status:** Pending
**File:** `src/code_forge/cli/main.py:197-230`
**Issue:** Commands can hang indefinitely with no interrupt mechanism
**Impact:** Unresponsive CLI
**Fix:** Add timeout wrapper around command execution

#### CLI-005: Missing UTF-8 Input Validation
**Status:** Pending
**File:** `src/code_forge/cli/repl.py:503-505`
**Issue:** No validation that input is valid UTF-8
**Impact:** Binary/invalid encoding could crash parser
**Fix:** Add encoding validation on input

#### CLI-006: Quote Parsing Falls Back Poorly
**Status:** Pending
**File:** `src/code_forge/commands/parser.py:145-150`
**Issue:** Unbalanced quotes fall back to `.split()` losing quoted strings
**Impact:** `/session title "My Title"` fails with unbalanced quotes
**Fix:** Better error handling or robust quote parsing

#### SEC-003: Dangerous Command Regex Bypassable
**Status:** Pending
**File:** `src/code_forge/tools/execution/bash.py:31-42`
**Issue:** Patterns like `rm -rf /` won't catch `rm -rf / | something`
**Impact:** Dangerous commands can slip through
**Fix:** Improve pattern matching or use allowlist approach

#### SEC-004: Domain Filter Uses Substring Match
**Status:** Pending
**File:** `src/code_forge/web/search/base.py:76`
**Issue:** `"github.com" in domain` matches `github.com.attacker.com`
**Impact:** Domain filtering can be bypassed
**Fix:** Use proper suffix matching for domains

#### SEC-005: HTML Parser Doesn't Remove Event Handlers
**Status:** Pending
**File:** `src/code_forge/web/fetch/parser.py:138-166`
**Issue:** Removes `<script>` but not `onerror=`, `onclick=` handlers
**Impact:** XSS if content rendered as HTML
**Fix:** Use proper HTML sanitizer (nh3, bleach)

#### SEC-006: Permission Pattern Regex DoS Risk
**Status:** Pending
**File:** `src/code_forge/permissions/rules.py:149-172`
**Issue:** User-supplied patterns compiled as regex without complexity limits
**Impact:** Malicious regex can cause ReDoS
**Fix:** Add regex complexity limits or use simplified pattern language

#### MEM-001: Conversation Memory Trim is O(n²)
**Status:** Pending
**File:** `src/code_forge/langchain/memory.py:155-186`
**Issue:** Recalculates total tokens for ALL messages every iteration
**Impact:** Poor performance with large conversation histories
**Fix:** Track running total, update incrementally

#### MEM-002: Summary Memory Keeps Last 10 Hardcoded
**Status:** Pending
**File:** `src/code_forge/langchain/memory.py:295-319`
**Issue:** Always keeps last 10 messages regardless of conversation structure
**Impact:** May drop important context
**Fix:** Make configurable or use smarter heuristics

---

### Low Priority (P3)

#### TEST-001: 555 Weak Assertions
**Status:** Pending
**Location:** Throughout test suite
**Issue:** Heavy use of `assert is not None` instead of specific value checks
**Impact:** Tests may pass when they shouldn't
**Fix:** Replace with specific assertions

#### TEST-002: Only 1 Parametrized Test
**Status:** Pending
**Location:** Tests throughout
**Issue:** Could benefit from `@pytest.mark.parametrize` for variations
**Impact:** Missing edge case coverage
**Fix:** Add parametrization for HTTP codes, error scenarios, file formats

#### TEST-003: No Concurrent/Race Condition Tests
**Status:** Pending
**Location:** Test suite
**Issue:** No tests for simultaneous operations or race conditions
**Impact:** Concurrency bugs may exist
**Fix:** Add tests for parallel tool execution, concurrent sessions

#### TEST-004: providers/ Module Has No Tests
**Status:** Pending
**Location:** `src/code_forge/providers/`
**Issue:** Module exists but has no corresponding tests
**Impact:** Untested code
**Fix:** Add tests or remove placeholder module

#### DOC-001: Fixture Dependency Chains Not Documented
**Status:** Pending
**File:** `tests/conftest.py`
**Issue:** Complex fixture relationships not documented
**Impact:** Hard to understand test setup
**Fix:** Add documentation comments

#### TOOL-005: Remaining Lines Calculation Off-by-One
**Status:** Pending
**File:** `src/code_forge/tools/file/read.py:180-182`
**Issue:** `offset + limit - 1` should be `offset + limit`
**Impact:** Slightly incorrect metadata
**Fix:** Correct the calculation

#### TOOL-006: Dry Run Doesn't Validate Paths
**Status:** Pending
**File:** `src/code_forge/tools/file/write.py:80-88`
**Issue:** Dry run returns success without validating path would work
**Impact:** False positive on invalid paths
**Fix:** Perform validation even in dry run

#### TOOL-007: GrepTool head_limit=0 Treated as Default
**Status:** Pending
**File:** `src/code_forge/tools/file/grep.py:169`
**Issue:** `head_limit=0` falls back to DEFAULT instead of unlimited
**Impact:** Can't explicitly request unlimited results
**Fix:** Use `if head_limit is None:` check

---

## Completed Milestones

| Version | Date | Summary |
|---------|------|---------|
| 1.1.0 | 2025-12-09 | All 22 phases complete, production ready |
| 1.0.0 | 2025-12-09 | Initial release |

---

## Issue Counts

| Priority | Count | Description |
|----------|-------|-------------|
| P0 Critical | 0 | ✅ All resolved |
| P1 High | 12 | Architecture and significant functional issues |
| P2 Medium | 12 | Quality improvements and UX enhancements |
| P3 Low | 7 | Minor issues and nice-to-haves |
| **Total** | **31** | (5 P0 issues fixed 2025-12-12) |

---

## How to Use This File

When starting new work:
1. Pick an item from the backlog (start with P0/P1)
2. Move to "Active Tasks" with your progress
3. Update status as work progresses
4. Move to "Completed Milestones" when released

Format for active tasks:
```
### ISSUE-ID: Title
**Status:** In Progress | Blocked | Done
**Assignee:** (if applicable)
**Branch:** (if applicable)
**Notes:** Progress updates
```
