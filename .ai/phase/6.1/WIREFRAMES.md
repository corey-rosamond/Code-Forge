# Phase 6.1: Slash Commands - Wireframes & Usage Examples

**Phase:** 6.1
**Name:** Slash Commands
**Dependencies:** Phase 1.3 (Basic REPL Shell), Phase 5.1 (Session Management)

---

## 1. Basic Command Usage

### Help Commands

```
You: /help

OpenCode Commands
========================================

General:
  /help             Show help for commands
  /commands         List all available commands

Session:
  /session          Session management
  /session list     List all sessions
  /session new      Create new session
  /session resume   Resume a session
  /session delete   Delete a session
  /session title    Set session title

Context:
  /context          Show context status
  /context compact  Compact context
  /context reset    Reset context
  /context mode     Set truncation mode

Control:
  /clear            Clear the screen
  /exit             Exit the application
  /reset            Reset to fresh state
  /stop             Stop current operation

Config:
  /config           Show configuration
  /config get       Get config value
  /config set       Set config value
  /model            Show/set current model

Debug:
  /debug            Toggle debug mode
  /tokens           Show token usage
  /history          Show message history
  /tools            List available tools

Type "/help <command>" for detailed help.
```

### Command-Specific Help

```
You: /help session

/session - Session Management

Usage:
  /session              Show current session info
  /session list         List all sessions
  /session new          Create new session
  /session resume [id]  Resume session by ID
  /session delete <id>  Delete a session
  /session title <text> Set session title
  /session tag <name>   Add tag to session
  /session untag <name> Remove tag from session

Aliases: sess, s

Examples:
  /session
  /session list --limit 10
  /session resume abc123
  /session title "Refactoring the API"
  /session new --title "Bug Fix"
```

---

## 2. Session Commands

### Show Current Session

```
You: /session

Session: 550e8400-e29b-41d4-a716-446655440000
Title: Refactoring the API client
Messages: 15
Tokens: 12,450 (prompt: 8,230, completion: 4,220)
Created: 2024-01-15 10:30:00
Updated: 2024-01-15 11:45:00
Tags: python, api, refactoring
```

### List Sessions

```
You: /session list

Sessions (5):

  550e8400... | Refactoring the API client
             15 msgs | 12,450 tokens
             Updated: 2 hours ago

  a1b2c3d4... | Implementing authentication
             32 msgs | 45,230 tokens
             Updated: 1 day ago

  e5f6g7h8... | Bug fix in parser
             8 msgs | 5,120 tokens
             Updated: 3 days ago

  i9j0k1l2... | Database optimization
             22 msgs | 28,900 tokens
             Updated: 1 week ago

  m3n4o5p6... | Adding new feature
             45 msgs | 67,800 tokens
             Updated: 2 weeks ago
```

### Create New Session

```
You: /session new --title "Code Review"

Created new session: 7q8r9s0t...
Title: Code Review
```

### Resume Session

```
You: /session resume 550e

Resumed session: Refactoring the API client
(15 messages, 12,450 tokens)
```

### Delete Session

```
You: /session delete a1b2

Deleted session: a1b2c3d4...
```

---

## 3. Context Commands

### Show Context Status

```
You: /context

Context Status:
  Model: claude-3-opus
  Mode: smart
  Messages: 15
  Token Usage: 12,450 / 200,000 (6.2%)
  Available: 187,550 tokens
  System Prompt: 450 tokens
  Tools: 2,100 tokens
```

### Compact Context

```
You: /context compact

Compacting context...
Summarized 10 old messages into 1 summary.
Before: 15 messages (12,450 tokens)
After: 6 messages (5,230 tokens)
Savings: 7,220 tokens (58%)
```

### Reset Context

```
You: /context reset

Context cleared.
Messages: 0
Tokens: 0
```

### Set Truncation Mode

```
You: /context mode summarize

Truncation mode set to: summarize
```

---

## 4. Control Commands

### Clear Screen

```
You: /clear

[Screen cleared - cursor at top]
```

### Exit Application

```
You: /exit

Session saved.
Goodbye!
```

### Reset State

```
You: /reset

Reset complete.
Previous session closed and saved.
Started new session: x9y8z7w6...
```

---

## 5. Config Commands

### Show Configuration

```
You: /config

Current Configuration:
  model: anthropic/claude-3-opus
  temperature: 1.0
  max_tokens: 4096
  context_mode: smart
  auto_save: true
  auto_save_interval: 60
  debug: false
```

### Get Config Value

```
You: /config get model

anthropic/claude-3-opus
```

### Set Config Value

```
You: /config set temperature 0.7

Configuration updated: temperature = 0.7
```

### Model Commands

```
You: /model

Current model: anthropic/claude-3-opus

You: /model gpt-4-turbo

Model changed to: gpt-4-turbo
Context limits updated: 128,000 tokens
```

---

## 6. Debug Commands

### Toggle Debug Mode

```
You: /debug

Debug mode enabled.
You will see detailed execution information.

You: /debug

Debug mode disabled.
```

### Show Token Usage

```
You: /tokens

Token Usage (Current Session):
  Prompt Tokens: 8,230
  Completion Tokens: 4,220
  Total Tokens: 12,450

Context Budget:
  System Prompt: 450 tokens
  Tools: 2,100 tokens
  Conversation: 9,900 tokens
  Available: 187,550 tokens
```

### Show Message History

```
You: /history

Message History (15 messages):

[1] system:
    You are a helpful coding assistant.

[2] user:
    Help me refactor the API client

[3] assistant:
    I'll help you refactor. Let me read the file...
    [Tool calls: read(api.py)]

[4] tool (read):
    class APIClient:
        def __init__(self): ...

[5] assistant:
    Here are my suggestions...

... (10 more messages)
```

### List Tools

```
You: /tools

Available Tools (12):

File Operations:
  read        Read file contents
  write       Write to file
  edit        Edit file with diff
  glob        Search for files
  grep        Search file contents

Execution:
  bash        Execute shell command
  bash_output Get output from background
  kill_shell  Kill background shell

Web:
  web_search  Search the web
  web_fetch   Fetch URL content

Other:
  ask_user    Ask user a question
  todo_write  Write to todo list
```

---

## 7. Error Handling

### Unknown Command

```
You: /unknwn

Unknown command: /unknwn. Did you mean /unknown?
Type /help for available commands.
```

### Missing Required Argument

```
You: /session delete

Missing required argument: <id>
Usage: /session delete <id>
```

### Invalid Argument

```
You: /context mode invalid

Invalid value for mode: "invalid"
Valid options: sliding_window, token_budget, smart, summarize
```

### Command Failed

```
You: /session resume nonexistent

Session not found: nonexistent
Use /session list to see available sessions.
```

---

## 8. Integration with REPL

### Command in Conversation

```
You: Help me refactor this function

Assistant: I see you want to refactor a function. Let me take a look...

[Assistant proceeds with refactoring task]

You: /tokens

Token Usage (Current Session):
  Prompt Tokens: 1,230
  Completion Tokens: 520
  Total Tokens: 1,750
```

### Mid-Task Command

```
You: Explain the difference between map and forEach

Assistant: The main differences are...

You: /session title JavaScript Array Methods

Session title updated: JavaScript Array Methods

You: Continue with your explanation

Assistant: As I was saying...
```

### Session Switch During Work

```
You: /session new --title "Quick Question"

Saved current session: JavaScript Array Methods
Created new session: Quick Question

You: What is the syntax for a Python list comprehension?

Assistant: The basic syntax is...

You: /session resume

Resumed session: JavaScript Array Methods
(Previous context restored)
```

---

## 9. Command Aliases

### Using Short Aliases

```
You: /s

Session: 550e8400...
Title: My Session
...

You: /s list

Sessions (3):
...

You: /q

Session saved.
Goodbye\!
```

### Alias Reference

```
You: /commands --aliases

Command Aliases:
  /help      -> /?, /h
  /session   -> /sess, /s
  /context   -> /ctx, /c
  /exit      -> /quit, /q
  /clear     -> /cls
  /config    -> /cfg
  /debug     -> /dbg
```

---

## Notes

- Commands start with `/` prefix
- Commands are case-insensitive
- Quoted strings preserve spaces
- Commands can be used mid-conversation
- Session state persists across commands
- Tab completion available where supported
