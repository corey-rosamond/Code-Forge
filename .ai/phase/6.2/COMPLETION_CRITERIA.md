# Phase 6.2: Operating Modes - Completion Criteria

**Phase:** 6.2
**Name:** Operating Modes
**Dependencies:** Phase 1.3 (Basic REPL Shell), Phase 3.2 (LangChain Integration)

---

## Completion Checklist

### 1. Mode Base Classes (base.py)

- [ ] `ModeName` enum implemented
  - [ ] NORMAL, PLAN, THINKING, HEADLESS values

- [ ] `ModeConfig` dataclass implemented
  - [ ] `name: ModeName`
  - [ ] `description: str`
  - [ ] `system_prompt_addition: str`
  - [ ] `enabled: bool = True`
  - [ ] `settings: dict`
  - [ ] `get_setting(key, default)` method
  - [ ] `set_setting(key, value)` method

- [ ] `ModeContext` dataclass implemented
  - [ ] `session: Any`
  - [ ] `config: Any`
  - [ ] `output: Callable`
  - [ ] `data: dict`
  - [ ] `get(key, default)` method
  - [ ] `set(key, value)` method

- [ ] `ModeState` dataclass implemented
  - [ ] `mode_name: ModeName`
  - [ ] `active: bool`
  - [ ] `data: dict`
  - [ ] `to_dict()` serialization
  - [ ] `from_dict()` deserialization

- [ ] `Mode` abstract base class implemented
  - [ ] `name` abstract property
  - [ ] `config` property
  - [ ] `state` property
  - [ ] `is_active` property
  - [ ] `_default_config()` abstract method
  - [ ] `activate(context)` abstract method
  - [ ] `deactivate(context)` abstract method
  - [ ] `modify_prompt(base)` method
  - [ ] `modify_response(response)` method
  - [ ] `should_auto_activate(message)` method
  - [ ] `save_state()` method
  - [ ] `restore_state(data)` method

- [ ] `NormalMode` implemented
  - [ ] Returns unchanged prompts
  - [ ] Returns unchanged responses

### 2. Mode Prompts (prompts.py)

- [ ] `PLAN_MODE_PROMPT` constant defined
  - [ ] Includes planning instructions
  - [ ] Specifies output format
  - [ ] Lists commands

- [ ] `THINKING_MODE_PROMPT` constant defined
  - [ ] Includes thinking instructions
  - [ ] Specifies `<thinking>` tag format

- [ ] `THINKING_MODE_DEEP_PROMPT` constant defined
  - [ ] More detailed analysis structure

- [ ] `HEADLESS_MODE_PROMPT` constant defined
  - [ ] Non-interactive constraints
  - [ ] Output format specifications

- [ ] `get_mode_prompt(name, variant)` function

### 3. Mode Manager (manager.py)

- [ ] `ModeManager` singleton implemented
  - [ ] `_instance` class variable
  - [ ] `get_instance()` class method
  - [ ] `reset_instance()` class method

- [ ] Mode registration
  - [ ] `register_mode(mode)` method
  - [ ] Raises ValueError on duplicate
  - [ ] `unregister_mode(name)` method
  - [ ] Cannot unregister NORMAL

- [ ] Mode queries
  - [ ] `get_mode(name)` returns mode or None
  - [ ] `get_current_mode()` returns active mode
  - [ ] `current_mode_name` property
  - [ ] `list_modes()` returns all modes
  - [ ] `list_enabled_modes()` returns enabled only

- [ ] Mode switching
  - [ ] `switch_mode(name, context, push)` method
  - [ ] Deactivates old mode
  - [ ] Activates new mode
  - [ ] Updates current mode
  - [ ] Supports push to stack
  - [ ] `pop_mode(context)` pops stack
  - [ ] `reset_mode(context)` clears to normal

- [ ] Prompt and response handling
  - [ ] `get_system_prompt(base)` applies mode
  - [ ] `process_response(response)` applies mode

- [ ] Auto-activation
  - [ ] `check_auto_activation(message)` method
  - [ ] Returns matching mode or None

- [ ] Event callbacks
  - [ ] `on_mode_change(callback)` registers listener
  - [ ] Callbacks called on switch

- [ ] State persistence
  - [ ] `save_state()` serializes all state
  - [ ] `restore_state(data, context)` restores

### 4. Plan Mode (plan.py)

- [ ] `PlanStep` dataclass implemented
  - [ ] `number: int`
  - [ ] `description: str`
  - [ ] `substeps: list[PlanStep]`
  - [ ] `completed: bool`
  - [ ] `files: list[str]`
  - [ ] `dependencies: list[int]`
  - [ ] `complexity: str`
  - [ ] `to_markdown(indent)` method
  - [ ] `to_dict()` / `from_dict()` methods

- [ ] `Plan` dataclass implemented
  - [ ] `title: str`
  - [ ] `summary: str`
  - [ ] `steps: list[PlanStep]`
  - [ ] `considerations: list[str]`
  - [ ] `success_criteria: list[str]`
  - [ ] `created_at` / `updated_at` timestamps
  - [ ] `to_markdown()` method
  - [ ] `to_todos()` conversion method
  - [ ] `progress` property (completed, total)
  - [ ] `progress_percentage` property
  - [ ] `mark_step_complete(number)` method
  - [ ] `to_dict()` / `from_dict()` methods

- [ ] `PlanMode` class implemented
  - [ ] `name = ModeName.PLAN`
  - [ ] `current_plan` attribute
  - [ ] `activate(context)` shows entry message
  - [ ] `deactivate(context)` saves plan
  - [ ] `should_auto_activate(message)` detects planning
  - [ ] `set_plan(plan)` stores plan
  - [ ] `get_plan()` retrieves plan
  - [ ] `show_plan()` formats for display
  - [ ] `execute_plan()` converts to todos
  - [ ] `cancel_plan()` clears plan
  - [ ] State persistence works

### 5. Thinking Mode (thinking.py)

- [ ] `ThinkingConfig` dataclass implemented
  - [ ] `max_thinking_tokens: int`
  - [ ] `show_thinking: bool`
  - [ ] `thinking_style: str`
  - [ ] `deep_mode: bool`

- [ ] `ThinkingResult` dataclass implemented
  - [ ] `thinking: str`
  - [ ] `response: str`
  - [ ] `thinking_tokens: int`
  - [ ] `response_tokens: int`
  - [ ] `time_seconds: float`
  - [ ] `timestamp: datetime`
  - [ ] `to_dict()` method

- [ ] `ThinkingMode` class implemented
  - [ ] `name = ModeName.THINKING`
  - [ ] `thinking_config` attribute
  - [ ] `activate(context)` starts timer
  - [ ] `deactivate(context)` cleans up
  - [ ] `set_deep_mode(enabled)` toggles deep
  - [ ] `set_thinking_budget(tokens)` sets limit
  - [ ] `modify_response(response)` extracts sections
  - [ ] `format_thinking_output(result)` formats display
  - [ ] `get_last_thinking()` retrieves result

- [ ] Thinking extraction pattern works
  - [ ] Matches `<thinking>...</thinking>`
  - [ ] Matches `<response>...</response>`
  - [ ] Handles missing tags gracefully

### 6. Headless Mode (headless.py)

- [ ] `OutputFormat` enum implemented
  - [ ] TEXT, JSON values

- [ ] `HeadlessConfig` dataclass implemented
  - [ ] `input_file: str | None`
  - [ ] `output_file: str | None`
  - [ ] `output_format: OutputFormat`
  - [ ] `timeout: int`
  - [ ] `auto_approve_safe: bool`
  - [ ] `fail_on_unsafe: bool`
  - [ ] `exit_on_complete: bool`

- [ ] `HeadlessResult` dataclass implemented
  - [ ] `success: bool`
  - [ ] `message: str`
  - [ ] `output: str`
  - [ ] `error: str | None`
  - [ ] `exit_code: int`
  - [ ] `execution_time: float`
  - [ ] `details: dict`
  - [ ] `timestamp: datetime`
  - [ ] `to_json()` method
  - [ ] `to_text()` method

- [ ] `HeadlessMode` class implemented
  - [ ] `name = ModeName.HEADLESS`
  - [ ] `headless_config` attribute
  - [ ] `activate(context)` opens streams
  - [ ] `deactivate(context)` closes streams
  - [ ] `read_input()` reads from source
  - [ ] `write_output(result)` writes formatted
  - [ ] `handle_permission_request(op, safe)` returns bool
  - [ ] `create_result(...)` creates HeadlessResult
  - [ ] `modify_response(response)` formats for output
  - [ ] `check_timeout()` checks elapsed

- [ ] `create_headless_config_from_args()` helper

### 7. Package Exports (__init__.py)

- [ ] All public classes exported
- [ ] `setup_modes(manager)` function
  - [ ] Registers PlanMode
  - [ ] Registers ThinkingMode
  - [ ] Registers HeadlessMode

### 8. Mode Commands

- [ ] `/mode` shows current mode
- [ ] `/mode <name>` switches mode
- [ ] `/mode list` lists all modes
- [ ] `/plan` enters plan mode
- [ ] `/plan show` displays plan
- [ ] `/plan execute` converts to todos
- [ ] `/plan cancel` clears and exits
- [ ] `/think` enters thinking mode
- [ ] `/think deep` enables deep mode
- [ ] `/normal` returns to normal

### 9. Integration

- [ ] REPL creates ModeContext
- [ ] REPL uses modified system prompt
- [ ] REPL processes responses through mode
- [ ] Mode state saved in session
- [ ] Mode restored on session resume
- [ ] CLI --headless flag works
- [ ] CLI --input and --output work
- [ ] CLI --json flag works

### 10. Testing

- [ ] Unit tests for Mode base class
- [ ] Unit tests for ModeManager
- [ ] Unit tests for PlanMode
- [ ] Unit tests for ThinkingMode
- [ ] Unit tests for HeadlessMode
- [ ] Unit tests for Plan/PlanStep
- [ ] Integration tests with REPL
- [ ] E2E tests for headless mode
- [ ] Test coverage ≥ 90%

### 11. Code Quality

- [ ] McCabe complexity ≤ 10 for all functions
- [ ] Type hints on all public methods
- [ ] Docstrings on all public classes/methods
- [ ] No circular imports
- [ ] Follows project code style

---

## Verification Commands

```bash
# Run unit tests
pytest tests/modes/ -v

# Run with coverage
pytest tests/modes/ --cov=src/opencode/modes --cov-report=term-missing

# Check coverage threshold
pytest tests/modes/ --cov=src/opencode/modes --cov-fail-under=90

# Type checking
mypy src/opencode/modes/

# Complexity check
flake8 src/opencode/modes/ --max-complexity=10

# Test headless mode
echo "Hello" | opencode --headless
opencode --headless --json "List files"
opencode --headless --input test.txt --output result.json
```

---

## Test Scenarios

### Mode Manager Tests

```python
def test_singleton():
    m1 = ModeManager.get_instance()
    m2 = ModeManager.get_instance()
    assert m1 is m2

def test_register_mode():
    manager = ModeManager()
    manager.register_mode(PlanMode())
    assert manager.get_mode(ModeName.PLAN) is not None

def test_switch_mode():
    manager = ModeManager()
    manager.register_mode(PlanMode())
    context = ModeContext(output=print)
    assert manager.switch_mode(ModeName.PLAN, context)
    assert manager.current_mode_name == ModeName.PLAN

def test_mode_stack():
    manager = ModeManager()
    manager.register_mode(PlanMode())
    context = ModeContext(output=print)

    manager.switch_mode(ModeName.PLAN, context, push=True)
    assert len(manager._mode_stack) == 1

    manager.pop_mode(context)
    assert manager.current_mode_name == ModeName.NORMAL
```

### Plan Mode Tests

```python
def test_plan_creation():
    plan = Plan(
        title="Test Plan",
        summary="Testing",
        steps=[
            PlanStep(number=1, description="Step 1"),
            PlanStep(number=2, description="Step 2"),
        ],
    )
    assert plan.progress == (0, 2)
    assert plan.progress_percentage == 0

def test_step_completion():
    plan = Plan(...)
    plan.mark_step_complete(1)
    assert plan.progress == (1, 2)
    assert plan.progress_percentage == 50

def test_plan_to_todos():
    plan = Plan(...)
    todos = plan.to_todos()
    assert len(todos) == 2
    assert todos[0]["status"] == "pending"

def test_auto_activation():
    mode = PlanMode()
    assert mode.should_auto_activate("Plan how to add auth")
    assert not mode.should_auto_activate("Hello world")
```

### Thinking Mode Tests

```python
def test_response_extraction():
    mode = ThinkingMode()
    response = "<thinking>Analysis</thinking><response>Answer</response>"
    result = mode.modify_response(response)
    assert "Analysis" in result
    assert "Answer" in result

def test_response_without_tags():
    mode = ThinkingMode()
    response = "Plain response"
    result = mode.modify_response(response)
    assert result == response

def test_deep_mode():
    mode = ThinkingMode()
    mode.set_deep_mode(True)
    assert mode.thinking_config.deep_mode
```

### Headless Mode Tests

```python
def test_safe_permission():
    config = HeadlessConfig(auto_approve_safe=True)
    mode = HeadlessMode(headless_config=config)
    assert mode.handle_permission_request("read", is_safe=True)

def test_unsafe_permission():
    config = HeadlessConfig(fail_on_unsafe=True)
    mode = HeadlessMode(headless_config=config)
    assert not mode.handle_permission_request("delete", is_safe=False)

def test_json_output():
    result = HeadlessResult(success=True, message="Done", output="Result")
    json_str = result.to_json()
    data = json.loads(json_str)
    assert data["status"] == "success"

def test_timeout():
    mode = HeadlessMode()
    mode._start_time = time.time() - 400
    mode.headless_config.timeout = 300
    assert mode.check_timeout()
```

---

## Definition of Done

Phase 6.2 is complete when:

1. All checklist items are checked off
2. All unit tests pass
3. Test coverage is ≥ 90%
4. Code complexity is ≤ 10
5. Type checking passes with no errors
6. All three modes function correctly
7. Mode switching works seamlessly
8. Plan mode creates structured plans
9. Thinking mode shows reasoning process
10. Headless mode works for automation
11. Mode state persists in sessions
12. CLI flags work correctly
13. Documentation is complete
14. Code review approved

---

## Dependencies Verification

Before starting Phase 6.2, verify:

- [ ] Phase 1.3 (Basic REPL Shell) is complete
  - [ ] REPL input loop functioning
  - [ ] Output display working
  - [ ] Commands can be processed

- [ ] Phase 3.2 (LangChain Integration) is complete
  - [ ] System prompts can be modified
  - [ ] Response processing works

---

## Notes

- Modes are the primary way to modify assistant behavior
- Plan mode helps ensure thorough analysis before coding
- Thinking mode aids in complex decision-making
- Headless mode enables automation and CI/CD
- All modes should be transparent about what they change
- Auto-activation should be opt-out configurable
