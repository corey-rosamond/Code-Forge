# Phase 4.1: Permission System - Gherkin Specifications

**Phase:** 4.1
**Name:** Permission System
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## Feature: Permission Levels

### Scenario: Permission level comparison
```gherkin
Given the permission levels ALLOW, ASK, DENY
Then ALLOW should be less than ASK
And ASK should be less than DENY
And DENY should be the most restrictive
```

### Scenario: Permission level ordering
```gherkin
When I sort permission levels by restrictiveness
Then the order should be: ALLOW, ASK, DENY
And ALLOW < ASK should be True
And ASK < DENY should be True
And DENY > ALLOW should be True
```

---

## Feature: Permission Rules

### Scenario: Create permission rule
```gherkin
Given I need to create a permission rule
When I create PermissionRule with:
  | pattern     | tool:bash           |
  | permission  | ask                 |
  | description | Confirm shell usage |
Then the rule pattern should be "tool:bash"
And the rule permission should be ASK
And the rule should be enabled by default
```

### Scenario: Rule serialization
```gherkin
Given a PermissionRule with pattern "tool:read" and permission ALLOW
When I call to_dict()
Then I should get:
  """json
  {
    "pattern": "tool:read",
    "permission": "allow",
    "description": "",
    "enabled": true,
    "priority": 0
  }
  """
```

### Scenario: Rule deserialization
```gherkin
Given JSON data:
  """json
  {
    "pattern": "tool:write",
    "permission": "deny",
    "description": "Block writing"
  }
  """
When I call PermissionRule.from_dict(data)
Then the rule pattern should be "tool:write"
And the rule permission should be DENY
And the description should be "Block writing"
```

---

## Feature: Pattern Matching

### Scenario: Match exact tool name
```gherkin
Given pattern "tool:bash"
And tool_name "bash"
And arguments {}
When I call PatternMatcher.match(pattern, tool_name, arguments)
Then the result should be True
```

### Scenario: Match tool glob pattern
```gherkin
Given pattern "tool:bash*"
And tool_name "bash_output"
And arguments {}
When I call PatternMatcher.match(pattern, tool_name, arguments)
Then the result should be True
```

### Scenario: Match argument value
```gherkin
Given pattern "arg:command:*git*"
And tool_name "bash"
And arguments {"command": "git status"}
When I call PatternMatcher.match(pattern, tool_name, arguments)
Then the result should be True
```

### Scenario: Match argument with glob
```gherkin
Given pattern "arg:file_path:*.py"
And tool_name "read"
And arguments {"file_path": "/tmp/test.py"}
When I call PatternMatcher.match(pattern, tool_name, arguments)
Then the result should be True
```

### Scenario: Match argument with regex
```gherkin
Given pattern "arg:file_path:^/etc/.*"
And tool_name "write"
And arguments {"file_path": "/etc/passwd"}
When I call PatternMatcher.match(pattern, tool_name, arguments)
Then the result should be True
```

### Scenario: Match combined tool and argument
```gherkin
Given pattern "tool:bash,arg:command:*rm*"
And tool_name "bash"
And arguments {"command": "rm -rf /tmp/test"}
When I call PatternMatcher.match(pattern, tool_name, arguments)
Then the result should be True
```

### Scenario: No match when tool differs
```gherkin
Given pattern "tool:bash"
And tool_name "read"
And arguments {}
When I call PatternMatcher.match(pattern, tool_name, arguments)
Then the result should be False
```

### Scenario: No match when argument missing
```gherkin
Given pattern "arg:command:*git*"
And tool_name "bash"
And arguments {}
When I call PatternMatcher.match(pattern, tool_name, arguments)
Then the result should be False
```

### Scenario: No match when argument value differs
```gherkin
Given pattern "arg:command:*git*"
And tool_name "bash"
And arguments {"command": "ls -la"}
When I call PatternMatcher.match(pattern, tool_name, arguments)
Then the result should be False
```

### Scenario: Match category
```gherkin
Given pattern "category:read_operations"
And tool_name "read"
And arguments {}
When I call PatternMatcher.match(pattern, tool_name, arguments)
Then the result should be True
```

---

## Feature: Pattern Specificity

### Scenario: Tool pattern specificity
```gherkin
Given pattern "tool:bash"
When I calculate specificity
Then the specificity should be greater than pattern "tool:*"
```

### Scenario: Argument pattern specificity
```gherkin
Given pattern "tool:bash,arg:command:git status"
When I calculate specificity
Then it should be more specific than "tool:bash"
And it should be more specific than "arg:command:*"
```

### Scenario: Category vs tool specificity
```gherkin
Given pattern "tool:read"
When I compare specificity to "category:read_operations"
Then tool pattern should be more specific than category pattern
```

---

## Feature: Rule Set Evaluation

### Scenario: Evaluate with matching rule
```gherkin
Given a RuleSet with rule "tool:read" → ALLOW
When I evaluate("read", {})
Then the result level should be ALLOW
And the result rule should be the matching rule
```

### Scenario: Evaluate with no matching rules
```gherkin
Given a RuleSet with default ASK and no matching rules
When I evaluate("unknown_tool", {})
Then the result level should be ASK
And the result rule should be None
And the reason should mention "default"
```

### Scenario: Most specific rule wins
```gherkin
Given a RuleSet with rules:
  | pattern              | permission |
  | tool:bash            | ask        |
  | tool:bash,arg:cmd:ls | allow      |
When I evaluate("bash", {"cmd": "ls"})
Then the result level should be ALLOW
And the matched rule pattern should be "tool:bash,arg:cmd:ls"
```

### Scenario: More restrictive rule wins on tie
```gherkin
Given a RuleSet with rules of equal specificity:
  | pattern    | permission |
  | tool:bash  | allow      |
  | tool:bash  | deny       |
When I evaluate("bash", {})
Then the result level should be DENY
```

### Scenario: Higher priority wins
```gherkin
Given a RuleSet with rules:
  | pattern   | permission | priority |
  | tool:bash | allow      | 0        |
  | tool:bash | deny       | 10       |
When I evaluate("bash", {})
Then the result level should be DENY (higher priority)
```

---

## Feature: Permission Checker

### Scenario: Check with session rule
```gherkin
Given a PermissionChecker with session rule "tool:bash" → ALLOW
And global rule "tool:bash" → ASK
When I check("bash", {})
Then the result should be ALLOW (session takes priority)
```

### Scenario: Check with project rule
```gherkin
Given a PermissionChecker with project rule "tool:bash" → DENY
And global rule "tool:bash" → ASK
When I check("bash", {})
Then the result should be DENY (project overrides global)
```

### Scenario: Check falls through to global
```gherkin
Given a PermissionChecker with only global rule "tool:bash" → ASK
When I check("bash", {})
Then the result should be ASK
```

### Scenario: Add session rule
```gherkin
Given a PermissionChecker
When I add_session_rule with pattern "tool:read" → ALLOW
Then get_session_rules() should contain the rule
And check("read", {}) should return ALLOW
```

### Scenario: Clear session rules
```gherkin
Given a PermissionChecker with session rules
When I call clear_session_rules()
Then get_session_rules() should be empty
And checks should fall through to other rule sources
```

### Scenario: Allow always
```gherkin
Given a PermissionChecker
When I call allow_always("bash", {"command": "ls"})
Then a session rule should be created for "tool:bash"
And subsequent checks for bash should return ALLOW
```

### Scenario: Deny always
```gherkin
Given a PermissionChecker
When I call deny_always("bash", {})
Then a session rule should be created for "tool:bash"
And subsequent checks for bash should return DENY
```

---

## Feature: User Confirmation

### Scenario: Format confirmation request
```gherkin
Given a ConfirmationRequest with:
  | tool_name   | bash              |
  | arguments   | {"command": "ls"} |
  | description | List directory    |
When I call format_request()
Then the output should contain "Permission Required"
And the output should contain "Tool: bash"
And the output should contain "command: ls"
And the output should show available choices
```

### Scenario: User chooses Allow
```gherkin
Given a confirmation prompt
When the user enters "a"
Then the result should be ConfirmationChoice.ALLOW
```

### Scenario: User chooses Allow Always
```gherkin
Given a confirmation prompt
When the user enters "A"
Then the result should be ConfirmationChoice.ALLOW_ALWAYS
```

### Scenario: User chooses Deny
```gherkin
Given a confirmation prompt
When the user enters "d"
Then the result should be ConfirmationChoice.DENY
```

### Scenario: User chooses Deny Always
```gherkin
Given a confirmation prompt
When the user enters "D"
Then the result should be ConfirmationChoice.DENY_ALWAYS
```

### Scenario: Invalid input defaults to Deny
```gherkin
Given a confirmation prompt
When the user enters "x" (invalid)
Then the result should be ConfirmationChoice.DENY
```

### Scenario: Empty input defaults to Deny
```gherkin
Given a confirmation prompt
When the user enters "" (empty)
Then the result should be ConfirmationChoice.DENY
```

### Scenario: Timeout results in Deny
```gherkin
Given a confirmation prompt with timeout=1.0
When the user doesn't respond within timeout
Then the result should be ConfirmationChoice.TIMEOUT
And execution should be blocked
```

---

## Feature: Create Rule from Choice

### Scenario: Allow Always creates rule
```gherkin
Given choice ALLOW_ALWAYS for tool "bash"
When I call create_rule_from_choice(choice, "bash", {})
Then I should get a PermissionRule
And the pattern should be "tool:bash"
And the permission should be ALLOW
And priority should be 100
```

### Scenario: Deny Always creates rule
```gherkin
Given choice DENY_ALWAYS for tool "bash"
When I call create_rule_from_choice(choice, "bash", {})
Then I should get a PermissionRule
And the pattern should be "tool:bash"
And the permission should be DENY
```

### Scenario: Allow does not create rule
```gherkin
Given choice ALLOW for tool "bash"
When I call create_rule_from_choice(choice, "bash", {})
Then I should get None
```

### Scenario: Deny does not create rule
```gherkin
Given choice DENY for tool "bash"
When I call create_rule_from_choice(choice, "bash", {})
Then I should get None
```

---

## Feature: Permission Configuration

### Scenario: Load default rules
```gherkin
Given no custom permission configuration
When I call PermissionConfig.load_global()
Then I should get a RuleSet with default rules
And "tool:read" should be ALLOW
And "tool:bash" should be ASK
And dangerous patterns should be DENY
```

### Scenario: Load global rules from file
```gherkin
Given a global permissions.json file with custom rules
When I call PermissionConfig.load_global()
Then I should get a RuleSet with the custom rules
```

### Scenario: Load project rules
```gherkin
Given a project with .src/forge/permissions.json
When I call PermissionConfig.load_project(project_root)
Then I should get a RuleSet with project-specific rules
```

### Scenario: Save global rules
```gherkin
Given a RuleSet with custom rules
When I call PermissionConfig.save_global(rules)
Then the rules should be persisted to global config
And subsequent load_global() should return the same rules
```

### Scenario: Handle corrupted permission file
```gherkin
Given a corrupted permissions.json file
When I call PermissionConfig.load_global()
Then I should get default rules (not crash)
And a warning should be logged
```

---

## Feature: Default Rules

### Scenario: Read operations allowed
```gherkin
Given default permission rules
When I check permission for "read" tool
Then it should be ALLOW
```

### Scenario: Write operations ask
```gherkin
Given default permission rules
When I check permission for "write" tool
Then it should be ASK
```

### Scenario: Dangerous commands denied
```gherkin
Given default permission rules
When I check "bash" with command "rm -rf /"
Then it should be DENY
```

### Scenario: System paths protected
```gherkin
Given default permission rules
When I check "write" with file_path "/etc/passwd"
Then it should be DENY
```

---

## Feature: Tool Executor Integration

### Scenario: Execute allowed tool
```gherkin
Given a ToolExecutor with PermissionChecker
And tool "read" is ALLOW
When I execute read tool
Then execution should proceed without confirmation
```

### Scenario: Execute tool requiring confirmation
```gherkin
Given a ToolExecutor with PermissionChecker
And tool "bash" is ASK
When I execute bash tool
Then user should be prompted for confirmation
And execution proceeds only if user allows
```

### Scenario: Execute denied tool
```gherkin
Given a ToolExecutor with PermissionChecker
And tool execution matches DENY rule
When I attempt to execute the tool
Then PermissionError should be raised
And tool should not execute
```

### Scenario: Allow Always creates persistent session rule
```gherkin
Given a ToolExecutor with PermissionChecker
And user chooses "Allow Always" for bash
When I execute bash again
Then no confirmation should be requested
And execution should proceed immediately
```

---

## Feature: Permission Error

### Scenario: PermissionError message
```gherkin
Given a PermissionResult with level DENY and reason "Blocked pattern"
When I create PermissionError(result, "bash", {})
Then the error message should contain "Permission denied"
And the error message should contain "bash"
And the error message should contain "Blocked pattern"
```

### Scenario: PermissionError attributes
```gherkin
Given a PermissionError
Then I should be able to access error.result
And I should be able to access error.tool_name
And I should be able to access error.arguments
```

---

## Feature: Permission Result Properties

### Scenario: Result allowed property
```gherkin
Given a PermissionResult with level ALLOW
Then result.allowed should be True
And result.needs_confirmation should be False
And result.denied should be False
```

### Scenario: Result needs_confirmation property
```gherkin
Given a PermissionResult with level ASK
Then result.allowed should be False
And result.needs_confirmation should be True
And result.denied should be False
```

### Scenario: Result denied property
```gherkin
Given a PermissionResult with level DENY
Then result.allowed should be False
And result.needs_confirmation should be False
And result.denied should be True
```

---

## Feature: Tool Categories

### Scenario: Read tool category
```gherkin
Given tool name "read"
When I get_tool_category("read")
Then the category should be PermissionCategory.READ
```

### Scenario: Write tool category
```gherkin
Given tool name "write"
When I get_tool_category("write")
Then the category should be PermissionCategory.WRITE
```

### Scenario: Bash tool category
```gherkin
Given tool name "bash"
When I get_tool_category("bash")
Then the category should be PermissionCategory.EXECUTE
```

### Scenario: Unknown tool category
```gherkin
Given tool name "unknown_tool"
When I get_tool_category("unknown_tool")
Then the category should be PermissionCategory.OTHER
```

---

## Feature: Multiple Rule Sources Priority

### Scenario: Session overrides project
```gherkin
Given:
  - Session rule: tool:bash → ALLOW
  - Project rule: tool:bash → DENY
  - Global rule: tool:bash → ASK
When I check("bash", {})
Then the result should be ALLOW (session wins)
```

### Scenario: Project overrides global
```gherkin
Given:
  - Project rule: tool:bash → DENY
  - Global rule: tool:bash → ALLOW
When I check("bash", {})
Then the result should be DENY (project wins)
```

### Scenario: Global used when no other rules
```gherkin
Given only global rules exist
When I check for a tool
Then global rules should be used
```
