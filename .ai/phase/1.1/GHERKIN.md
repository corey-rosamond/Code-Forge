# Phase 1.1: Project Foundation - Gherkin Specifications

**Phase:** 1.1
**Name:** Project Foundation
**Scope:** Project structure, interfaces, types, and CLI basics

---

## Feature: Project Installation

```gherkin
Feature: Project Installation and Setup
  As a developer
  I want to install OpenCode as a Python package
  So that I can use it as a development tool

  @phase1.1 @installation
  Scenario: Install package with Poetry
    Given I have cloned the OpenCode repository
    And Python 3.10 or higher is installed
    When I run "pip install -e ".[dev]""
    Then the installation should complete without errors
    And all dependencies should be installed
    And the "opencode" command should be available

  @phase1.1 @installation
  Scenario: Install package with uv
    Given I have cloned the OpenCode repository
    And Python 3.10 or higher is installed
    When I run "uv sync"
    Then the installation should complete without errors
    And all dependencies should be installed

  @phase1.1 @installation
  Scenario: Verify Python version requirement
    Given I have Python 3.9 installed
    When I attempt to install OpenCode
    Then the installation should fail
    And I should see an error about Python version requirement
```

---

## Feature: CLI Entry Point

```gherkin
Feature: CLI Entry Point
  As a user
  I want basic CLI functionality
  So that I can verify the installation works

  Background:
    Given OpenCode is installed

  @phase1.1 @cli @smoke
  Scenario: Display version
    When I run "opencode --version"
    Then I should see the version number "0.1.0"
    And the exit code should be 0

  @phase1.1 @cli @smoke
  Scenario: Display version with short flag
    When I run "opencode -v"
    Then I should see the version number "0.1.0"
    And the exit code should be 0

  @phase1.1 @cli @smoke
  Scenario: Display help
    When I run "opencode --help"
    Then I should see usage information
    And I should see available options listed
    And the exit code should be 0

  @phase1.1 @cli @smoke
  Scenario: Display help with short flag
    When I run "opencode -h"
    Then I should see usage information
    And the exit code should be 0

  @phase1.1 @cli
  Scenario: Run without arguments
    When I run "opencode"
    Then I should see a welcome message
    And I should see instructions for help
    And the exit code should be 0

  @phase1.1 @cli
  Scenario: Run as Python module
    When I run "python -m OpenCode --version"
    Then I should see the version number
    And the exit code should be 0
```

---

## Feature: Core Types

```gherkin
Feature: Core Value Objects
  As a developer
  I want well-defined value objects
  So that I can work with type-safe data structures

  @phase1.1 @types
  Scenario: Create AgentId
    When I create an AgentId without arguments
    Then it should have a UUID value
    And it should be convertible to string
    And it should be hashable

  @phase1.1 @types
  Scenario: Create SessionId
    When I create a SessionId with value "session-123"
    Then its string representation should be "session-123"

  @phase1.1 @types
  Scenario: Create ProjectId from path
    When I create a ProjectId from path "/home/user/project"
    Then it should have a hashed value
    And it should store the original path

  @phase1.1 @types
  Scenario: Create Message
    When I create a Message with role "user" and content "Hello"
    Then the role should be "user"
    And the content should be "Hello"
    And name should be None
    And tool_calls should be None

  @phase1.1 @types
  Scenario: Create CompletionRequest
    Given I have a list of Messages
    When I create a CompletionRequest with model "gpt-5"
    Then the model should be "gpt-5"
    And temperature should default to 1.0
    And stream should default to False
```

---

## Feature: Exception Hierarchy

```gherkin
Feature: Exception Hierarchy
  As a developer
  I want a clear exception hierarchy
  So that I can handle errors appropriately

  @phase1.1 @errors
  Scenario: OpenCodeError is base exception
    When I raise an OpenCodeError with message "test error"
    Then it should be catchable as Exception
    And its string should be "test error"

  @phase1.1 @errors
  Scenario: OpenCodeError with cause
    Given I have an original exception
    When I raise an OpenCodeError with that cause
    Then the cause should be accessible
    And the string should include "caused by"

  @phase1.1 @errors
  Scenario: ConfigError inheritance
    When I raise a ConfigError
    Then it should be catchable as OpenCodeError
    And it should be catchable as Exception

  @phase1.1 @errors
  Scenario: ToolError includes tool name
    When I raise a ToolError for tool "Read" with message "file not found"
    Then the tool_name should be "Read"
    And the string should include "Tool 'Read'"

  @phase1.1 @errors
  Scenario: ProviderError includes provider name
    When I raise a ProviderError for provider "openrouter" with message "rate limited"
    Then the provider should be "openrouter"
    And the string should include "Provider 'openrouter'"

  @phase1.1 @errors
  Scenario: PermissionError includes action and reason
    When I raise a PermissionError for action "file_write" with reason "denied by policy"
    Then the action should be "file_write"
    And the reason should be "denied by policy"
    And the string should include both
```

---

## Feature: Result Type

```gherkin
Feature: Result Type
  As a developer
  I want a Result type for operations that can fail
  So that I can handle success and failure explicitly

  @phase1.1 @result
  Scenario: Create successful result
    When I create a Result.ok with value "success"
    Then success should be True
    And value should be "success"
    And error should be None

  @phase1.1 @result
  Scenario: Create failed result
    When I create a Result.fail with error "something went wrong"
    Then success should be False
    And value should be None
    And error should be "something went wrong"

  @phase1.1 @result
  Scenario: Unwrap successful result
    Given a successful Result with value 42
    When I call unwrap()
    Then I should get 42

  @phase1.1 @result
  Scenario: Unwrap failed result
    Given a failed Result with error "failed"
    When I call unwrap()
    Then a ValueError should be raised
    And the message should include "failed"

  @phase1.1 @result
  Scenario: Unwrap_or with successful result
    Given a successful Result with value "actual"
    When I call unwrap_or with default "default"
    Then I should get "actual"

  @phase1.1 @result
  Scenario: Unwrap_or with failed result
    Given a failed Result
    When I call unwrap_or with default "default"
    Then I should get "default"
```

---

## Feature: Interfaces Definition

```gherkin
Feature: Interface Definitions
  As a developer
  I want clearly defined interfaces
  So that I can implement components with clear contracts

  @phase1.1 @interfaces
  Scenario: ITool interface is abstract
    When I try to instantiate ITool directly
    Then a TypeError should be raised
    And the message should indicate it's abstract

  @phase1.1 @interfaces
  Scenario: ITool has required properties
    Given a class implementing ITool
    When I check required properties
    Then "name" should be required
    And "description" should be required
    And "parameters" should be required

  @phase1.1 @interfaces
  Scenario: ITool has execute method
    Given a class implementing ITool
    When I check required methods
    Then "execute" should be an async method
    And it should return ToolResult

  @phase1.1 @interfaces
  Scenario: IModelProvider is abstract
    When I try to instantiate IModelProvider directly
    Then a TypeError should be raised

  @phase1.1 @interfaces
  Scenario: IModelProvider has required methods
    Given a class implementing IModelProvider
    When I check required methods
    Then "complete" should be an async method
    And "stream" should be an async generator
    And "list_models" should be an async method

  @phase1.1 @interfaces
  Scenario: IConfigLoader is abstract
    When I try to instantiate IConfigLoader directly
    Then a TypeError should be raised

  @phase1.1 @interfaces
  Scenario: ISessionRepository is abstract
    When I try to instantiate ISessionRepository directly
    Then a TypeError should be raised
```

---

## Feature: Logging Infrastructure

```gherkin
Feature: Logging Infrastructure
  As a developer
  I want structured logging
  So that I can debug and monitor the application

  @phase1.1 @logging
  Scenario: Setup default logging
    When I call setup_logging without arguments
    Then logging should be configured at INFO level
    And Rich console handler should be active

  @phase1.1 @logging
  Scenario: Setup logging with file output
    Given a temporary log file path
    When I call setup_logging with that file path
    Then logs should also write to the file

  @phase1.1 @logging
  Scenario: Get named logger
    When I call get_logger with name "test"
    Then I should get a Logger instance
    And its name should be "opencode.test"

  @phase1.1 @logging
  Scenario: Log messages at different levels
    Given logging is configured
    When I log at DEBUG, INFO, WARNING, ERROR levels
    Then messages should be formatted correctly
    And levels should be distinguishable
```

---

## Feature: Code Quality

```gherkin
Feature: Code Quality Standards
  As a developer
  I want high code quality standards
  So that the codebase remains maintainable

  @phase1.1 @quality
  Scenario: Type checking passes
    When I run "mypy src/opencode/"
    Then there should be no errors
    And all public functions should have type hints

  @phase1.1 @quality
  Scenario: Linting passes
    When I run "ruff check src/opencode/"
    Then there should be no errors
    And code should follow PEP 8

  @phase1.1 @quality
  Scenario: Test coverage is adequate
    When I run "pytest --cov=opencode"
    Then coverage should be at least 90%
    And all core modules should be covered

  @phase1.1 @quality
  Scenario: No circular imports
    When I import any module
    Then no circular import errors should occur
```

---

## Test Data Requirements

### Sample Values
- AgentId: Auto-generated UUID
- SessionId: "session-abc123"
- ProjectId: Generated from "/test/project"
- Message: role="user", content="test message"

### Mock Objects
None required for Phase 1.1 (all interfaces, no implementations)

---

## Tag Reference

| Tag | Description |
|-----|-------------|
| @phase1.1 | All Phase 1.1 tests |
| @installation | Package installation tests |
| @cli | CLI entry point tests |
| @smoke | Critical path tests |
| @types | Value object tests |
| @errors | Exception tests |
| @result | Result type tests |
| @interfaces | Interface definition tests |
| @logging | Logging infrastructure tests |
| @quality | Code quality tests |
