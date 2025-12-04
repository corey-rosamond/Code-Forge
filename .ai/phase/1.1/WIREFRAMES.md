# Phase 1.1: Project Foundation - Wireframes

**Phase:** 1.1
**Name:** Project Foundation
**Scope:** CLI basic output only (no interactive UI)

---

## Overview

Phase 1.1 has minimal UI - only CLI output for `--version` and `--help`. No interactive REPL or TUI components are implemented in this phase.

---

## 1. Version Output

```
┌─────────────────────────────────────────────────────────────────┐
│ $ opencode --version                                            │
│ opencode 0.1.0                                                  │
│ $                                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Specification
- Single line output
- Format: `opencode X.Y.Z`
- No color formatting required
- Exit immediately after output

---

## 2. Help Output

```
┌─────────────────────────────────────────────────────────────────┐
│ $ opencode --help                                               │
│                                                                 │
│ OpenCode - AI-powered CLI Development Assistant                 │
│                                                                 │
│ Usage: opencode [OPTIONS] [PROMPT]                              │
│                                                                 │
│ Options:                                                        │
│   -v, --version     Show version and exit                       │
│   -h, --help        Show this help message                      │
│   --continue        Resume most recent session                  │
│   --resume          Select session to resume                    │
│   -p, --print       Run in headless mode with prompt            │
│                                                                 │
│ For more information, visit: https://github.com/opencode        │
│                                                                 │
│ $                                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Specification
- Plain text output (no Rich formatting yet)
- Clear section headers
- Aligned option descriptions
- URL for more information
- Exit immediately after output

---

## 3. Default Output (No Arguments)

```
┌─────────────────────────────────────────────────────────────────┐
│ $ opencode                                                      │
│ OpenCode - AI Development Assistant                             │
│ Run with --help for usage information                           │
│ $                                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Specification
- Brief welcome message
- Point user to --help for more information
- Exit immediately (no REPL in Phase 1.1)

---

## 4. Error Output

```
┌─────────────────────────────────────────────────────────────────┐
│ $ opencode --invalid-flag                                       │
│ Error: Unknown option '--invalid-flag'                          │
│ Run 'opencode --help' for usage information                     │
│ $                                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Specification
- Error message to stderr
- Clear indication of what went wrong
- Point user to help
- Exit code 1

---

## 5. Terminal Compatibility

### Minimum Requirements
- Any terminal supporting basic text output
- No color requirements
- No Unicode requirements
- Works over SSH
- Works in CI/CD environments

### Tested Environments
- Linux terminals (bash, zsh)
- macOS Terminal.app
- Windows Terminal (WSL)
- VS Code integrated terminal
- Basic TTY

---

## Future Phase Preview

The following UI elements are NOT part of Phase 1.1 but will be added in later phases:

### Phase 1.3: Basic REPL
```
┌─────────────────────────────────────────────────────────────────┐
│ $ opencode                                                      │
│ OpenCode v0.1.0 - AI Development Assistant                      │
│ Type /help for commands, Ctrl+D to exit                         │
│                                                                 │
│ > _                                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 6.1+: Full TUI
```
┌─────────────────────────────────────────────────────────────────┐
│ OpenCode v0.1.0          gpt-5         Tokens: 1.2k/128k   Ready│
├─────────────────────────────────────────────────────────────────┤
│ You: How do I implement a binary search?                        │
│                                                                 │
│ Assistant: Here's how to implement binary search...             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ > _                                                             │
│                                                     [? for help]│
└─────────────────────────────────────────────────────────────────┘
```

---

## Design Tokens (For Future Reference)

These are not used in Phase 1.1 but establish the design language:

### Colors (Phase 1.3+)
| Element | Dark Mode | Light Mode |
|---------|-----------|------------|
| Background | #1a1b26 | #f5f5f5 |
| Text | #c0caf5 | #1a1b26 |
| Accent | #7aa2f7 | #2563eb |
| Success | #9ece6a | #22c55e |
| Warning | #e0af68 | #eab308 |
| Error | #f7768e | #ef4444 |

### Typography
| Element | Style |
|---------|-------|
| Headers | Bold |
| Code | Monospace |
| Normal | Regular |

---

## Notes

Phase 1.1 intentionally has minimal UI because:
1. Focus is on project structure and interfaces
2. No dependencies on Rich/Textual features yet
3. Ensures basic functionality works in any environment
4. Provides foundation for richer UI in later phases

All wireframes in this phase are simple text output with no formatting.
