# Phase 1.2: Configuration System - Completion Criteria

**Phase:** 1.2
**Name:** Configuration System
**Dependencies:** Phase 1.1 (Project Foundation)

---

## Definition of Done

All of the following criteria must be met before Phase 1.2 is considered complete.

---

## Checklist

### Configuration Models (src/forge/config/models.py)
- [ ] `Code-ForgeConfig` root model defined
- [ ] `ModelConfig` with validation (max_tokens range, temperature range)
- [ ] `PermissionConfig` with allow/ask/deny lists
- [ ] `HooksConfig` with all hook event types
- [ ] `HookConfig` with type enum, matcher, command, prompt, timeout
- [ ] `MCPServerConfig` with transport enum
- [ ] `DisplayConfig` with all display options
- [ ] `SessionConfig` with all session options
- [ ] `RoutingVariant` enum (nitro, floor, exacto, thinking, online)
- [ ] `TransportType` enum (stdio, streamable-http)
- [ ] `HookType` enum (command, prompt)
- [ ] All models have sensible defaults
- [ ] API key uses `SecretStr` type

### Configuration Sources (src/forge/config/sources.py)
- [ ] `IConfigSource` interface defined
- [ ] `JsonFileSource` implementation
- [ ] `YamlFileSource` implementation
- [ ] `EnvironmentSource` implementation
- [ ] All sources handle missing files gracefully
- [ ] All sources handle malformed content gracefully

### Configuration Loader (src/forge/config/loader.py)
- [ ] `ConfigLoader` implements `IConfigLoader` from Phase 1.1
- [ ] `load_all()` loads and merges all sources
- [ ] `load(path)` loads single file
- [ ] `merge(base, override)` performs deep merge
- [ ] `validate(config)` validates against schema
- [ ] `reload()` reloads configuration
- [ ] `watch()` starts file watcher
- [ ] `stop_watching()` stops file watcher
- [ ] `add_observer()` registers callback
- [ ] `remove_observer()` unregisters callback
- [ ] `config` property provides cached access

### Hierarchy Implementation
- [ ] Defaults are loaded first
- [ ] Enterprise settings (`/etc/src/forge/settings.json`) loaded
- [ ] User settings (`~/.src/forge/settings.json`) loaded
- [ ] Project settings (`.src/forge/settings.json`) loaded
- [ ] Local overrides (`.src/forge/settings.local.json`) loaded
- [ ] Environment variables applied last
- [ ] Later sources override earlier sources
- [ ] Deep merge preserves nested values

### Environment Variables
- [ ] `FORGE_API_KEY` sets api_key
- [ ] `FORGE_MODEL` sets model.default
- [ ] `FORGE_MAX_TOKENS` sets model.max_tokens
- [ ] `FORGE_THEME` sets display.theme
- [ ] Environment has highest precedence

### Live Reload
- [ ] File watcher detects JSON file changes
- [ ] File watcher detects YAML file changes
- [ ] Reload validates new configuration
- [ ] Invalid config keeps old configuration
- [ ] Observers are notified on successful reload
- [ ] Watcher can be stopped cleanly

### Security
- [ ] API key never appears in logs (any level)
- [ ] API key never appears in `str()` representation
- [ ] API key never appears in JSON serialization (without explicit flag)

### Testing
- [ ] Unit tests for all configuration models
- [ ] Unit tests for all source implementations
- [ ] Unit tests for ConfigLoader
- [ ] Unit tests for merge algorithm
- [ ] Unit tests for validation
- [ ] Unit tests for live reload
- [ ] Integration tests for full hierarchy loading
- [ ] Test coverage ≥ 90%

---

## Verification Commands

```bash
# 1. Test model validation
python -c "
from forge.config.models import forgeConfig, ModelConfig
# Valid config
c = Code-ForgeConfig(model=ModelConfig(default='gpt-5', max_tokens=8192))
print(f'Valid config: {c.model.default}')

# Invalid max_tokens should fail
try:
    ModelConfig(max_tokens=500000)
    print('ERROR: Should have failed')
except Exception as e:
    print(f'Validation works: {e}')
"

# 2. Test JSON loading
mkdir -p .forge
echo '{"model": {"default": "test-model"}}' > .src/forge/settings.json
python -c "
from forge.config import ConfigLoader
c = ConfigLoader().load_all()
print(f'Loaded model: {c.model.default}')
assert c.model.default == 'test-model', 'JSON loading failed'
print('JSON loading works!')
"

# 3. Test environment override
FORGE_MODEL=env-model python -c "
from forge.config import ConfigLoader
c = ConfigLoader().load_all()
print(f'Model from env: {c.model.default}')
assert c.model.default == 'env-model', 'Env override failed'
print('Environment override works!')
"

# 4. Test hierarchy merge
echo '{"model": {"default": "user-model", "max_tokens": 4096}}' > ~/.src/forge/settings.json
echo '{"model": {"default": "project-model"}}' > .src/forge/settings.json
python -c "
from forge.config import ConfigLoader
c = ConfigLoader().load_all()
print(f'Model: {c.model.default}, Tokens: {c.model.max_tokens}')
assert c.model.default == 'project-model', 'Hierarchy failed'
assert c.model.max_tokens == 4096, 'Merge failed'
print('Hierarchy merge works!')
"

# 5. Test API key security
python -c "
from forge.config.models import forgeConfig
import logging
logging.basicConfig(level=logging.DEBUG)

c = Code-ForgeConfig(api_key='sk-secret-123')
s = str(c)
assert 'sk-secret-123' not in s, 'API key in string!'
print(f'String repr: {s[:100]}...')
print('API key is secure!')
"

# 6. Run all tests
pytest tests/unit/config/ -v --cov=forge.config --cov-report=term-missing

# 7. Type checking
mypy src/forge/config/ --strict

# 8. Linting
ruff check src/forge/config/
```

---

## Quality Gates

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Test Coverage | ≥ 90% | `pytest --cov` |
| Type Hints | 100% public APIs | `mypy --strict` |
| Lint Errors | 0 | `ruff check` |
| McCabe Complexity | ≤ 8 | `ruff check --select=C901` |
| API Key Security | Never logged | Manual test |

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/forge/config/__init__.py` | Package exports |
| `src/forge/config/models.py` | Pydantic configuration models |
| `src/forge/config/sources.py` | IConfigSource implementations |
| `src/forge/config/loader.py` | ConfigLoader implementation |
| `tests/unit/config/__init__.py` | Test package |
| `tests/unit/config/test_models.py` | Model tests |
| `tests/unit/config/test_sources.py` | Source tests |
| `tests/unit/config/test_loader.py` | Loader tests |

---

## Dependencies to Add

Update `pyproject.toml`:
```toml
[tool.poetry.dependencies]
pyyaml = "^6.0"
watchdog = "^3.0"
```

---

## Sign-Off

Phase 1.2 is complete when:

1. [ ] All checklist items above are checked
2. [ ] All verification commands pass
3. [ ] All quality gates are met
4. [ ] Code has been reviewed (if applicable)
5. [ ] No TODO comments remain in Phase 1.2 code

---

## Next Phase

After completing Phase 1.2, proceed to:
- **Phase 1.3: Basic REPL Shell**

Phase 1.3 depends on:
- Configuration system from Phase 1.2 (for display settings)
- Core interfaces from Phase 1.1
- Logging from Phase 1.1
