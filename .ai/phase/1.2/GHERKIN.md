# Phase 1.2: Configuration System - Gherkin Specifications

**Phase:** 1.2
**Name:** Configuration System
**Dependencies:** Phase 1.1

---

## Feature: Configuration File Loading

```gherkin
Feature: Configuration File Loading
  As a user
  I want to configure OpenCode via files
  So that I can customize behavior

  Background:
    Given the opencode package is installed

  @phase1.2 @config @json
  Scenario: Load JSON configuration file
    Given a file ".src/opencode/settings.json" with content:
      """json
      {
        "model": {
          "default": "claude-4"
        }
      }
      """
    When I create a ConfigLoader
    And I call load_all()
    Then the config model.default should be "claude-4"

  @phase1.2 @config @yaml
  Scenario: Load YAML configuration file
    Given a file ".src/opencode/settings.yaml" with content:
      """yaml
      model:
        default: gemini-2.5-pro
      """
    When I create a ConfigLoader
    And I call load_all()
    Then the config model.default should be "gemini-2.5-pro"

  @phase1.2 @config @json
  Scenario: JSON takes precedence over YAML in same directory
    Given a file ".src/opencode/settings.json" with model.default "from-json"
    And a file ".src/opencode/settings.yaml" with model.default "from-yaml"
    When I call load_all()
    Then the config model.default should be "from-json"

  @phase1.2 @config @missing
  Scenario: Handle missing configuration file
    Given no configuration files exist
    When I call load_all()
    Then the config should use default values
    And model.default should be "gpt-5"

  @phase1.2 @config @invalid
  Scenario: Handle invalid JSON syntax
    Given a file ".src/opencode/settings.json" with invalid JSON
    When I call load_all()
    Then a ConfigError should be logged
    And the config should use default values
```

---

## Feature: Configuration Hierarchy

```gherkin
Feature: Configuration Hierarchy
  As a user
  I want configuration hierarchy
  So that different scopes can have different settings

  @phase1.2 @hierarchy @user
  Scenario: User settings are loaded
    Given a file "~/.src/opencode/settings.json" with:
      """json
      {"model": {"default": "user-model"}}
      """
    When I call load_all()
    Then the config model.default should be "user-model"

  @phase1.2 @hierarchy @project
  Scenario: Project settings override user settings
    Given a file "~/.src/opencode/settings.json" with model.default "user-model"
    And a file ".src/opencode/settings.json" with model.default "project-model"
    When I call load_all()
    Then the config model.default should be "project-model"

  @phase1.2 @hierarchy @local
  Scenario: Local settings override project settings
    Given a file ".src/opencode/settings.json" with model.default "project-model"
    And a file ".src/opencode/settings.local.json" with model.default "local-model"
    When I call load_all()
    Then the config model.default should be "local-model"

  @phase1.2 @hierarchy @enterprise
  Scenario: Enterprise settings have highest file priority
    Given a file "/etc/src/opencode/settings.json" with model.default "enterprise-model"
    And a file "~/.src/opencode/settings.json" with model.default "user-model"
    And a file ".src/opencode/settings.json" with model.default "project-model"
    When I call load_all()
    Then the config model.default should be "enterprise-model"

  @phase1.2 @hierarchy @merge
  Scenario: Deep merge preserves nested values
    Given a file "~/.src/opencode/settings.json" with:
      """json
      {
        "model": {"default": "user-model", "max_tokens": 4096},
        "display": {"theme": "dark"}
      }
      """
    And a file ".src/opencode/settings.json" with:
      """json
      {
        "model": {"default": "project-model"}
      }
      """
    When I call load_all()
    Then the config model.default should be "project-model"
    And the config model.max_tokens should be 4096
    And the config display.theme should be "dark"
```

---

## Feature: Environment Variables

```gherkin
Feature: Environment Variable Configuration
  As a user
  I want to configure via environment variables
  So that I can use secrets without files

  Background:
    Given the opencode package is installed

  @phase1.2 @env @api-key
  Scenario: API key from environment
    Given environment variable OPENCODE_API_KEY is set to "sk-test-123"
    When I call load_all()
    Then the config api_key should be "sk-test-123"

  @phase1.2 @env @model
  Scenario: Model from environment
    Given environment variable OPENCODE_MODEL is set to "gpt-5"
    When I call load_all()
    Then the config model.default should be "gpt-5"

  @phase1.2 @env @override
  Scenario: Environment overrides file config
    Given a file ".src/opencode/settings.json" with model.default "file-model"
    And environment variable OPENCODE_MODEL is set to "env-model"
    When I call load_all()
    Then the config model.default should be "env-model"

  @phase1.2 @env @precedence
  Scenario: Environment has highest precedence
    Given a file "/etc/src/opencode/settings.json" with model.default "enterprise"
    And a file "~/.src/opencode/settings.json" with model.default "user"
    And a file ".src/opencode/settings.json" with model.default "project"
    And environment variable OPENCODE_MODEL is set to "env-model"
    When I call load_all()
    Then the config model.default should be "env-model"
```

---

## Feature: Configuration Validation

```gherkin
Feature: Configuration Validation
  As a user
  I want configuration validation
  So that I catch errors early

  Background:
    Given the opencode package is installed

  @phase1.2 @validation @model
  Scenario: Valid model configuration
    Given a configuration with model.max_tokens = 8192
    When I validate the configuration
    Then validation should succeed

  @phase1.2 @validation @invalid-type
  Scenario: Invalid type for max_tokens
    Given a configuration with model.max_tokens = "not-a-number"
    When I validate the configuration
    Then validation should fail
    And the error should mention "max_tokens"

  @phase1.2 @validation @range
  Scenario: Max tokens out of range
    Given a configuration with model.max_tokens = 500000
    When I validate the configuration
    Then validation should fail
    And the error should mention "max_tokens"

  @phase1.2 @validation @temperature
  Scenario: Temperature out of range
    Given a configuration with model.temperature = 3.0
    When I validate the configuration
    Then validation should fail
    And the error should mention "temperature"

  @phase1.2 @validation @enum
  Scenario: Invalid routing variant
    Given a configuration with model.routing_variant = "invalid"
    When I validate the configuration
    Then validation should fail
    And the error should mention "routing_variant"

  @phase1.2 @validation @partial
  Scenario: Partial configuration is valid
    Given a configuration with only model.default set
    When I validate the configuration
    Then validation should succeed
    And other fields should have default values
```

---

## Feature: Live Reload

```gherkin
Feature: Configuration Live Reload
  As a user
  I want configuration to reload on change
  So that I don't need to restart

  Background:
    Given the opencode package is installed
    And a ConfigLoader is created

  @phase1.2 @reload @watch
  Scenario: Start watching configuration files
    When I call watch()
    Then the file watcher should be running
    And it should watch ".src/opencode/" directory
    And it should watch "~/.src/opencode/" directory

  @phase1.2 @reload @detect
  Scenario: Detect configuration file change
    Given I am watching configuration files
    And the current config has model.default = "old-model"
    When I modify ".src/opencode/settings.json" to set model.default = "new-model"
    Then reload should be triggered
    And the config model.default should be "new-model"

  @phase1.2 @reload @observer
  Scenario: Notify observers on reload
    Given I am watching configuration files
    And I have registered an observer callback
    When the configuration changes
    Then the observer callback should be called
    And it should receive the new configuration

  @phase1.2 @reload @invalid
  Scenario: Keep old config on invalid reload
    Given I am watching configuration files
    And the current config is valid
    When I modify settings to be invalid JSON
    Then the old configuration should be preserved
    And an error should be logged

  @phase1.2 @reload @stop
  Scenario: Stop watching configuration files
    Given I am watching configuration files
    When I call stop_watching()
    Then the file watcher should stop
    And file changes should not trigger reload
```

---

## Feature: Security

```gherkin
Feature: Configuration Security
  As a security-conscious user
  I want secure configuration handling
  So that my secrets are protected

  @phase1.2 @security @api-key
  Scenario: API key not logged at INFO level
    Given a configuration with api_key = "sk-secret-key"
    When I log the configuration at INFO level
    Then "sk-secret-key" should not appear in logs

  @phase1.2 @security @api-key-debug
  Scenario: API key not logged at DEBUG level
    Given a configuration with api_key = "sk-secret-key"
    When I log the configuration at DEBUG level
    Then "sk-secret-key" should not appear in logs

  @phase1.2 @security @repr
  Scenario: API key not in string representation
    Given a configuration with api_key = "sk-secret-key"
    When I convert the config to string
    Then "sk-secret-key" should not appear
    And "SecretStr" or "***" should appear instead

  @phase1.2 @security @serialize
  Scenario: API key not in JSON serialization
    Given a configuration with api_key = "sk-secret-key"
    When I serialize the config to JSON
    Then "sk-secret-key" should not appear
```

---

## Feature: Configuration Models

```gherkin
Feature: Configuration Model Defaults
  As a developer
  I want sensible default values
  So that minimal configuration works

  @phase1.2 @defaults @model
  Scenario: Model defaults
    When I create a ModelConfig with no arguments
    Then default should be "gpt-5"
    And fallback should include "claude-4"
    And max_tokens should be 8192
    And temperature should be 1.0

  @phase1.2 @defaults @permissions
  Scenario: Permission defaults
    When I create a PermissionConfig with no arguments
    Then allow should be an empty list
    And ask should be an empty list
    And deny should be an empty list

  @phase1.2 @defaults @display
  Scenario: Display defaults
    When I create a DisplayConfig with no arguments
    Then theme should be "dark"
    And show_tokens should be True
    And vim_mode should be False

  @phase1.2 @defaults @session
  Scenario: Session defaults
    When I create a SessionConfig with no arguments
    Then auto_save should be True
    And save_interval should be 60
    And max_history should be 100
```

---

## Test Data Requirements

### Sample Configuration Files

**Minimal config:**
```json
{}
```

**User config:**
```json
{
  "model": {"default": "claude-4"},
  "display": {"theme": "light"}
}
```

**Project config:**
```json
{
  "model": {"default": "gpt-5", "max_tokens": 16384},
  "permissions": {
    "allow": ["Read(*)", "Glob(*)"],
    "ask": ["Write(*)"]
  }
}
```

**Invalid config:**
```json
{
  "model": {"max_tokens": "invalid"}
}
```

### Environment Variables
- OPENCODE_API_KEY=sk-test-123
- OPENCODE_MODEL=gpt-5
- OPENCODE_THEME=dark

---

## Tag Reference

| Tag | Description |
|-----|-------------|
| @phase1.2 | All Phase 1.2 tests |
| @config | Configuration loading tests |
| @json | JSON file tests |
| @yaml | YAML file tests |
| @hierarchy | Hierarchy tests |
| @env | Environment variable tests |
| @validation | Validation tests |
| @reload | Live reload tests |
| @security | Security tests |
| @defaults | Default value tests |
