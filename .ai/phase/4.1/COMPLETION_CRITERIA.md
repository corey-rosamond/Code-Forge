# Phase 4.1: Permission System - Completion Criteria

**Phase:** 4.1
**Name:** Permission System
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## Definition of Done

All of the following criteria must be met before Phase 4.1 is considered complete.

---

## Checklist

### Permission Models (src/opencode/permissions/models.py)
- [ ] PermissionLevel enum defined (ALLOW, ASK, DENY)
- [ ] PermissionLevel comparison operators work (ALLOW < ASK < DENY)
- [ ] PermissionCategory enum defined
- [ ] PermissionRule dataclass with pattern, permission, description
- [ ] PermissionRule.to_dict() serializes correctly
- [ ] PermissionRule.from_dict() deserializes correctly
- [ ] PermissionResult dataclass with level, rule, reason
- [ ] PermissionResult.allowed property
- [ ] PermissionResult.needs_confirmation property
- [ ] PermissionResult.denied property
- [ ] TOOL_CATEGORIES mapping defined
- [ ] get_tool_category() function

### Pattern Matching (src/opencode/permissions/rules.py)
- [ ] PatternMatcher.match() for tool patterns
- [ ] PatternMatcher.match() for argument patterns
- [ ] PatternMatcher.match() for category patterns
- [ ] PatternMatcher.match() for combined patterns
- [ ] PatternMatcher.parse_pattern() extracts components
- [ ] PatternMatcher.specificity() calculates score
- [ ] Glob pattern matching works
- [ ] Regex pattern matching works

### Rule Set (src/opencode/permissions/rules.py)
- [ ] RuleSet class with rules list and default
- [ ] RuleSet.add_rule() adds rules
- [ ] RuleSet.remove_rule() removes by pattern
- [ ] RuleSet.get_rule() retrieves by pattern
- [ ] RuleSet.evaluate() returns PermissionResult
- [ ] Evaluation respects priority
- [ ] Evaluation respects specificity
- [ ] Most restrictive wins on ties
- [ ] RuleSet.to_dict() serializes
- [ ] RuleSet.from_dict() deserializes

### Permission Checker (src/opencode/permissions/checker.py)
- [ ] PermissionChecker class with multiple rule sources
- [ ] PermissionChecker.check() evaluates all sources
- [ ] Session rules take highest priority
- [ ] Project rules override global rules
- [ ] add_session_rule() adds temporary rules
- [ ] remove_session_rule() removes rules
- [ ] clear_session_rules() clears all session rules
- [ ] get_session_rules() returns list
- [ ] allow_always() creates ALLOW session rule
- [ ] deny_always() creates DENY session rule
- [ ] PermissionChecker.from_config() factory method
- [ ] PermissionError exception class

### User Confirmation (src/opencode/permissions/prompt.py)
- [ ] ConfirmationChoice enum (ALLOW, ALLOW_ALWAYS, DENY, DENY_ALWAYS, TIMEOUT)
- [ ] ConfirmationRequest dataclass
- [ ] PermissionPrompt.format_request() creates display string
- [ ] PermissionPrompt.confirm() synchronous confirmation
- [ ] PermissionPrompt.confirm_async() async with timeout
- [ ] Input parsing handles a/A/d/D
- [ ] Invalid input defaults to deny
- [ ] Timeout returns TIMEOUT choice
- [ ] create_rule_from_choice() creates rules for "always" choices

### Configuration (src/opencode/permissions/config.py)
- [ ] DEFAULT_RULES list defined
- [ ] Default read operations ALLOW
- [ ] Default write operations ASK
- [ ] Default dangerous operations DENY
- [ ] PermissionConfig.get_global_path()
- [ ] PermissionConfig.get_project_path()
- [ ] PermissionConfig.load_global() returns RuleSet
- [ ] PermissionConfig.load_project() returns RuleSet or None
- [ ] PermissionConfig.save_global() persists rules
- [ ] PermissionConfig.save_project() persists rules
- [ ] PermissionConfig.get_default_rules()
- [ ] PermissionConfig.reset_to_defaults()
- [ ] Handles corrupted files gracefully

### Package Structure
- [ ] src/opencode/permissions/__init__.py exports all public classes
- [ ] All imports work correctly
- [ ] No circular dependencies

### Testing
- [ ] Unit tests for PermissionLevel comparison
- [ ] Unit tests for PatternMatcher.match()
- [ ] Unit tests for glob patterns
- [ ] Unit tests for regex patterns
- [ ] Unit tests for combined patterns
- [ ] Unit tests for RuleSet.evaluate()
- [ ] Unit tests for rule precedence
- [ ] Unit tests for PermissionChecker
- [ ] Unit tests for session rule management
- [ ] Unit tests for confirmation parsing
- [ ] Unit tests for config loading/saving
- [ ] Test coverage ≥ 90%

---

## Verification Commands

```bash
# 1. Verify module structure
ls -la src/opencode/permissions/
# Expected: __init__.py, models.py, rules.py, checker.py, prompt.py, config.py

# 2. Test imports
python -c "
from opencode.permissions import (
    PermissionLevel,
    PermissionCategory,
    PermissionResult,
    PermissionRule,
    PatternMatcher,
    RuleSet,
    PermissionChecker,
    PermissionError,
    ConfirmationChoice,
    ConfirmationRequest,
    PermissionPrompt,
    create_rule_from_choice,
    PermissionConfig,
    DEFAULT_RULES,
    TOOL_CATEGORIES,
    get_tool_category,
)
print('All permission imports successful')
"

# 3. Test PermissionLevel comparison
python -c "
from opencode.permissions import PermissionLevel

assert PermissionLevel.ALLOW < PermissionLevel.ASK
assert PermissionLevel.ASK < PermissionLevel.DENY
assert PermissionLevel.DENY > PermissionLevel.ALLOW
assert PermissionLevel.ALLOW <= PermissionLevel.ALLOW
assert PermissionLevel.DENY >= PermissionLevel.ASK

print('PermissionLevel comparison: OK')
"

# 4. Test PatternMatcher
python -c "
from opencode.permissions import PatternMatcher

# Tool pattern
assert PatternMatcher.match('tool:bash', 'bash', {}) == True
assert PatternMatcher.match('tool:bash', 'read', {}) == False

# Glob pattern
assert PatternMatcher.match('tool:bash*', 'bash_output', {}) == True

# Argument pattern
assert PatternMatcher.match('arg:command:*git*', 'bash', {'command': 'git status'}) == True
assert PatternMatcher.match('arg:command:*git*', 'bash', {'command': 'ls'}) == False

# Combined pattern
assert PatternMatcher.match('tool:bash,arg:command:*rm*', 'bash', {'command': 'rm file'}) == True
assert PatternMatcher.match('tool:bash,arg:command:*rm*', 'read', {'command': 'rm file'}) == False

print('PatternMatcher: OK')
"

# 5. Test RuleSet
python -c "
from opencode.permissions import RuleSet, PermissionRule, PermissionLevel

rules = RuleSet(default=PermissionLevel.ASK)
rules.add_rule(PermissionRule('tool:read', PermissionLevel.ALLOW))
rules.add_rule(PermissionRule('tool:bash,arg:command:*rm*', PermissionLevel.DENY, priority=10))
rules.add_rule(PermissionRule('tool:bash', PermissionLevel.ASK))

# Test evaluation
result = rules.evaluate('read', {})
assert result.level == PermissionLevel.ALLOW

result = rules.evaluate('bash', {'command': 'ls'})
assert result.level == PermissionLevel.ASK

result = rules.evaluate('bash', {'command': 'rm file'})
assert result.level == PermissionLevel.DENY

print('RuleSet: OK')
"

# 6. Test PermissionChecker
python -c "
from opencode.permissions import PermissionChecker, RuleSet, PermissionRule, PermissionLevel

global_rules = RuleSet()
global_rules.add_rule(PermissionRule('tool:bash', PermissionLevel.ASK))

checker = PermissionChecker(global_rules=global_rules)

# Should be ASK from global
result = checker.check('bash', {})
assert result.level == PermissionLevel.ASK

# Add session rule
checker.allow_always('bash', {})

# Should now be ALLOW from session
result = checker.check('bash', {})
assert result.level == PermissionLevel.ALLOW

# Clear session
checker.clear_session_rules()

# Back to ASK
result = checker.check('bash', {})
assert result.level == PermissionLevel.ASK

print('PermissionChecker: OK')
"

# 7. Test PermissionResult
python -c "
from opencode.permissions import PermissionResult, PermissionLevel

result_allow = PermissionResult(level=PermissionLevel.ALLOW)
assert result_allow.allowed == True
assert result_allow.needs_confirmation == False
assert result_allow.denied == False

result_ask = PermissionResult(level=PermissionLevel.ASK)
assert result_ask.allowed == False
assert result_ask.needs_confirmation == True
assert result_ask.denied == False

result_deny = PermissionResult(level=PermissionLevel.DENY)
assert result_deny.allowed == False
assert result_deny.needs_confirmation == False
assert result_deny.denied == True

print('PermissionResult: OK')
"

# 8. Test confirmation choice parsing
python -c "
from opencode.permissions import PermissionPrompt, ConfirmationChoice

prompt = PermissionPrompt()

assert prompt._parse_response('a') == ConfirmationChoice.ALLOW
assert prompt._parse_response('A') == ConfirmationChoice.ALLOW_ALWAYS
assert prompt._parse_response('d') == ConfirmationChoice.DENY
assert prompt._parse_response('D') == ConfirmationChoice.DENY_ALWAYS
assert prompt._parse_response('') == ConfirmationChoice.DENY
assert prompt._parse_response('x') == ConfirmationChoice.DENY

print('Confirmation parsing: OK')
"

# 9. Test create_rule_from_choice
python -c "
from opencode.permissions import (
    create_rule_from_choice, ConfirmationChoice, PermissionLevel
)

rule = create_rule_from_choice(ConfirmationChoice.ALLOW_ALWAYS, 'bash', {})
assert rule is not None
assert rule.pattern == 'tool:bash'
assert rule.permission == PermissionLevel.ALLOW

rule = create_rule_from_choice(ConfirmationChoice.DENY_ALWAYS, 'bash', {})
assert rule is not None
assert rule.permission == PermissionLevel.DENY

rule = create_rule_from_choice(ConfirmationChoice.ALLOW, 'bash', {})
assert rule is None

print('create_rule_from_choice: OK')
"

# 10. Test rule serialization
python -c "
from opencode.permissions import PermissionRule, PermissionLevel

rule = PermissionRule(
    pattern='tool:bash',
    permission=PermissionLevel.ASK,
    description='Confirm bash',
)

data = rule.to_dict()
assert data['pattern'] == 'tool:bash'
assert data['permission'] == 'ask'
assert data['description'] == 'Confirm bash'

rule2 = PermissionRule.from_dict(data)
assert rule2.pattern == rule.pattern
assert rule2.permission == rule.permission

print('Rule serialization: OK')
"

# 11. Test RuleSet serialization
python -c "
from opencode.permissions import RuleSet, PermissionRule, PermissionLevel

rules = RuleSet(default=PermissionLevel.ASK)
rules.add_rule(PermissionRule('tool:read', PermissionLevel.ALLOW))

data = rules.to_dict()
assert data['default'] == 'ask'
assert len(data['rules']) == 1

rules2 = RuleSet.from_dict(data)
assert rules2.default == PermissionLevel.ASK
assert len(rules2.rules) == 1

print('RuleSet serialization: OK')
"

# 12. Test default rules
python -c "
from opencode.permissions import PermissionConfig, PermissionLevel

defaults = PermissionConfig.get_default_rules()

# Check read is allowed
result = defaults.evaluate('read', {})
assert result.level == PermissionLevel.ALLOW

# Check bash is ask
result = defaults.evaluate('bash', {'command': 'ls'})
assert result.level == PermissionLevel.ASK

# Check dangerous is deny
result = defaults.evaluate('bash', {'command': 'rm -rf /'})
assert result.level == PermissionLevel.DENY

print('Default rules: OK')
"

# 13. Test tool categories
python -c "
from opencode.permissions import get_tool_category, PermissionCategory

assert get_tool_category('read') == PermissionCategory.READ
assert get_tool_category('write') == PermissionCategory.WRITE
assert get_tool_category('bash') == PermissionCategory.EXECUTE
assert get_tool_category('unknown') == PermissionCategory.OTHER

print('Tool categories: OK')
"

# 14. Test prompt formatting
python -c "
from opencode.permissions import PermissionPrompt, ConfirmationRequest

prompt = PermissionPrompt()
request = ConfirmationRequest(
    tool_name='bash',
    arguments={'command': 'ls -la'},
    description='List directory',
)

formatted = prompt.format_request(request)
assert 'Permission Required' in formatted
assert 'bash' in formatted
assert 'ls -la' in formatted

print('Prompt formatting: OK')
"

# 15. Run all unit tests
pytest tests/unit/permissions/ -v --cov=opencode.permissions --cov-report=term-missing

# Expected: All tests pass, coverage ≥ 90%

# 16. Type checking
mypy src/opencode/permissions/ --strict
# Expected: No errors

# 17. Linting
ruff check src/opencode/permissions/
# Expected: No errors
```

---

## Quality Gates

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Test Coverage | ≥ 90% | `pytest --cov` |
| Type Hints | 100% public APIs | `mypy --strict` |
| Lint Errors | 0 | `ruff check` |
| McCabe Complexity | ≤ 10 | `ruff check --select=C901` |

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/opencode/permissions/__init__.py` | Package exports |
| `src/opencode/permissions/models.py` | Permission data models |
| `src/opencode/permissions/rules.py` | Rule definition and matching |
| `src/opencode/permissions/checker.py` | Permission checker |
| `src/opencode/permissions/prompt.py` | User confirmation prompts |
| `src/opencode/permissions/config.py` | Permission configuration |
| `tests/unit/permissions/__init__.py` | Test package |
| `tests/unit/permissions/test_models.py` | Model tests |
| `tests/unit/permissions/test_rules.py` | Pattern matching tests |
| `tests/unit/permissions/test_checker.py` | Checker tests |
| `tests/unit/permissions/test_prompt.py` | Prompt tests |
| `tests/unit/permissions/test_config.py` | Config tests |

---

## Dependencies to Verify

No additional dependencies required beyond Python standard library.

---

## Manual Testing Checklist

- [ ] Create permission rule via code
- [ ] Pattern matching works for various patterns
- [ ] RuleSet evaluation returns correct results
- [ ] PermissionChecker respects priority order
- [ ] Session rules override other rules
- [ ] Confirmation prompt displays correctly
- [ ] User input parsed correctly
- [ ] "Allow Always" creates session rule
- [ ] "Deny Always" creates session rule
- [ ] Config saves and loads correctly
- [ ] Default rules provide expected behavior

---

## Integration Points

Phase 4.1 provides the permission system for:

| Consumer | What It Uses |
|----------|--------------|
| Phase 2.1 (Tools) | ToolExecutor uses PermissionChecker |
| Phase 4.2 (Hooks) | Permission events trigger hooks |
| Phase 5.1 (Sessions) | Session rules persist |
| Phase 6.2 (Modes) | Headless mode permission handling |

---

## Sign-Off

Phase 4.1 is complete when:

1. [ ] All checklist items above are checked
2. [ ] All verification commands pass
3. [ ] All quality gates are met
4. [ ] Manual testing completed
5. [ ] Code has been reviewed (if applicable)
6. [ ] No TODO comments remain in Phase 4.1 code

---

## Next Phase

After completing Phase 4.1, proceed to:
- **Phase 4.2: Hooks System**

Phase 4.2 will implement:
- Hook events and types
- Hook registration and execution
- Pre/post execution hooks
- Permission hooks
- Hook configuration
