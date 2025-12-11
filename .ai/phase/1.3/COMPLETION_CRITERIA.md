# Phase 1.3: Basic REPL Shell - Completion Criteria

**Phase:** 1.3
**Name:** Basic REPL Shell
**Dependencies:** Phase 1.1 (Project Foundation), Phase 1.2 (Configuration System)

---

## Definition of Done

All of the following criteria must be met before Phase 1.3 is considered complete.

---

## Checklist

### REPL Core (src/forge/cli/repl.py)
- [ ] `Code-ForgeREPL` class implemented
- [ ] `run()` async method starts REPL loop
- [ ] `stop()` method stops REPL loop
- [ ] `on_input()` method registers callbacks for input processing
- [ ] Welcome message displays on startup
- [ ] Prompt appears and accepts input
- [ ] Empty input is ignored (returns to prompt)
- [ ] Input is passed to registered callbacks
- [ ] REPL continues after each input
- [ ] Clean exit on EOF (Ctrl+D)
- [ ] Graceful interrupt on Ctrl+C (returns to prompt)

### Input Handler (src/forge/cli/repl.py or separate file)
- [ ] `InputHandler` class implemented
- [ ] Single-line input with Enter to submit
- [ ] Multiline input with Shift+Enter
- [ ] History navigation with Up/Down arrows
- [ ] Reverse search with Ctrl+R
- [ ] History persists to `~/.src/forge/history`
- [ ] History file created if not exists
- [ ] Directory created if not exists

### Output Renderer (src/forge/cli/repl.py or separate file)
- [ ] `OutputRenderer` class implemented
- [ ] `print()` method for plain text
- [ ] `print_markdown()` method for markdown
- [ ] `print_code()` method for syntax-highlighted code
- [ ] `print_panel()` method for boxed content
- [ ] `print_error()` method for errors (red)
- [ ] `print_warning()` method for warnings (yellow)
- [ ] `clear()` method for screen clearing

### Status Bar (src/forge/cli/status.py)
- [ ] `StatusBar` class implemented
- [ ] `set_model()` updates displayed model
- [ ] `set_tokens()` updates token display
- [ ] `set_mode()` updates mode display
- [ ] `set_status()` updates status text
- [ ] `render()` produces formatted status bar string
- [ ] Status bar respects terminal width
- [ ] Status bar hidden when `display.status_line` is false

### Themes (src/forge/cli/themes.py)
- [ ] `DARK_THEME` dictionary defined
- [ ] `LIGHT_THEME` dictionary defined
- [ ] Theme includes: background, foreground, accent, success, warning, error, dim
- [ ] Theme selection based on config `display.theme`

### Keyboard Shortcuts
- [ ] Escape: Cancel/clear current input
- [ ] Ctrl+C: Interrupt and return to prompt
- [ ] Ctrl+D: Exit on empty input
- [ ] Ctrl+L: Clear screen
- [ ] Ctrl+U: Clear input line
- [ ] Ctrl+R: Reverse history search
- [ ] "?": Show shortcuts (on empty input + Enter)
- [ ] Up/Down: Navigate history

### CLI Integration (src/forge/cli/main.py)
- [ ] `main()` updated to start REPL when no arguments
- [ ] Configuration loaded before REPL starts
- [ ] Async event loop properly handled
- [ ] Exit code returned correctly

### Testing
- [ ] Unit tests for `Code-ForgeREPL`
- [ ] Unit tests for `InputHandler`
- [ ] Unit tests for `OutputRenderer`
- [ ] Unit tests for `StatusBar`
- [ ] Unit tests for themes
- [ ] Integration test for REPL startup and exit
- [ ] Test coverage ≥ 90%

---

## Verification Commands

```bash
# 1. Start REPL
forge
# Expected: Welcome screen appears, prompt ready

# 2. Test basic input
> Hello world
# Expected: "Received: Hello world" (placeholder response)

# 3. Test multiline (type line, Shift+Enter, type more, Enter)
> Line 1
  Line 2
# Expected: Both lines processed as one input

# 4. Test history
# Type a command, press Enter
# Press Up arrow
# Expected: Previous command appears

# 5. Test Ctrl+L
# Press Ctrl+L
# Expected: Screen clears, prompt at top

# 6. Test Ctrl+C
> some input
# Press Ctrl+C
# Expected: "Interrupted", prompt returns

# 7. Test Ctrl+D
# On empty prompt, press Ctrl+D
# Expected: "Goodbye!", clean exit with code 0

# 8. Test shortcuts help
> ?
# Expected: List of keyboard shortcuts displayed

# 9. Verify history file
ls -la ~/.src/forge/history
# Expected: File exists

# 10. Test theme via config
echo '{"display": {"theme": "light"}}' > .src/forge/settings.json
forge
# Expected: Light theme colors

# 11. Run tests
pytest tests/unit/cli/ -v --cov=forge.cli --cov-report=term-missing
# Expected: All pass, coverage ≥ 90%

# 12. Type checking
mypy src/forge/cli/ --strict
# Expected: No errors

# 13. Linting
ruff check src/forge/cli/
# Expected: No errors
```

---

## Quality Gates

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Test Coverage | ≥ 90% | `pytest --cov` |
| Type Hints | 100% public APIs | `mypy --strict` |
| Lint Errors | 0 | `ruff check` |
| McCabe Complexity | ≤ 8 | `ruff check --select=C901` |
| Input Latency | < 10ms | Manual testing |
| Startup Time | < 500ms | `time forge --version` |

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/forge/cli/repl.py` | Code-ForgeREPL, InputHandler, OutputRenderer |
| `src/forge/cli/status.py` | StatusBar class |
| `src/forge/cli/themes.py` | Theme definitions |
| `src/forge/cli/__init__.py` | Updated exports |
| `src/forge/cli/main.py` | Updated entry point |
| `tests/unit/cli/test_repl.py` | REPL tests |
| `tests/unit/cli/test_status.py` | Status bar tests |
| `tests/unit/cli/test_themes.py` | Theme tests |

---

## Dependencies to Verify

Ensure these are in `pyproject.toml`:
```toml
[tool.poetry.dependencies]
rich = "^13.7"
textual = "^0.47"
prompt-toolkit = "^3.0"
```

---

## Manual Testing Checklist

- [ ] REPL starts without errors
- [ ] Welcome message is clear and informative
- [ ] Typing feels responsive (no lag)
- [ ] Cursor behaves correctly
- [ ] History Up/Down works
- [ ] History Ctrl+R search works
- [ ] Multiline Shift+Enter works
- [ ] Escape clears input
- [ ] Ctrl+C shows "Interrupted", doesn't exit
- [ ] Ctrl+D on empty input exits cleanly
- [ ] Ctrl+L clears screen
- [ ] Status bar displays correctly
- [ ] Dark theme looks good
- [ ] Light theme looks good
- [ ] Works in standard terminal (bash/zsh)
- [ ] Works in VS Code integrated terminal
- [ ] Works over SSH connection

---

## Sign-Off

Phase 1.3 is complete when:

1. [ ] All checklist items above are checked
2. [ ] All verification commands pass
3. [ ] All quality gates are met
4. [ ] Manual testing checklist completed
5. [ ] Code has been reviewed (if applicable)
6. [ ] No TODO comments remain in Phase 1.3 code

---

## Next Phase

After completing Phase 1.3, proceed to:
- **Phase 2.1: Tool System Foundation**

Phase 2.1 depends on:
- REPL shell from Phase 1.3 (for displaying tool output)
- Configuration from Phase 1.2
- Core interfaces from Phase 1.1 (ITool interface)
