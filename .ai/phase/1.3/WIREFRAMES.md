# Phase 1.3: Basic REPL Shell - Wireframes

**Phase:** 1.3
**Name:** Basic REPL Shell
**Dependencies:** Phase 1.1, Phase 1.2

---

## 1. Welcome Screen

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  Code-Forge v0.1.0                                                    │
│  AI-powered CLI Development Assistant                               │
│                                                                     │
│  Directory: /home/user/my-project                                   │
│  Type /help for commands, ? for shortcuts                           │
│                                                                     │
│  >                                                                  │
│                                                                     │
│                                                                     │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ gpt-5                  Tokens: 0/128,000               Normal │ Ready│
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Input States

### Empty Prompt
```
│  > _                                                                │
```

### Single Line Input
```
│  > Hello, how can you help me?_                                     │
```

### Multiline Input (Shift+Enter)
```
│  > Here is my code:                                                 │
│    def hello():                                                     │
│        print("hello")                                               │
│    _                                                                │
```

---

## 3. Response Display

### Plain Text Response
```
│  > What is Python?                                                  │
│                                                                     │
│  Python is a high-level, interpreted programming language known     │
│  for its simplicity and readability. It supports multiple           │
│  programming paradigms including procedural, object-oriented,       │
│  and functional programming.                                        │
│                                                                     │
│  > _                                                                │
```

### Response with Code Block
```
│  > Show me a hello world in Python                                  │
│                                                                     │
│  Here's a simple Hello World program:                               │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │   1 │ def main():                                            │   │
│  │   2 │     print("Hello, World!")                             │   │
│  │   3 │                                                        │   │
│  │   4 │ if __name__ == "__main__":                             │   │
│  │   5 │     main()                                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  > _                                                                │
```

### Response with Markdown
```
│  > List the SOLID principles                                        │
│                                                                     │
│  # SOLID Principles                                                 │
│                                                                     │
│  • **S**ingle Responsibility - A class should have one reason to    │
│    change                                                           │
│  • **O**pen/Closed - Open for extension, closed for modification    │
│  • **L**iskov Substitution - Subtypes must be substitutable         │
│  • **I**nterface Segregation - Many specific interfaces are better  │
│  • **D**ependency Inversion - Depend on abstractions                │
│                                                                     │
│  > _                                                                │
```

---

## 4. Keyboard Shortcuts Help

```
│  > ?                                                                │
│                                                                     │
│  Keyboard Shortcuts                                                 │
│  ──────────────────                                                 │
│                                                                     │
│  Esc           Cancel current input                                 │
│  Ctrl+C        Interrupt operation                                  │
│  Ctrl+D        Exit (on empty input)                                │
│  Ctrl+L        Clear screen                                         │
│  Ctrl+R        Search history                                       │
│  Ctrl+U        Clear input line                                     │
│  ↑/↓           Navigate history                                     │
│  Shift+Enter   New line (multiline input)                           │
│                                                                     │
│  > _                                                                │
```

---

## 5. Status Bar Variants

### Ready State
```
├─────────────────────────────────────────────────────────────────────┤
│ gpt-5                  Tokens: 0/128,000               Normal │ Ready│
└─────────────────────────────────────────────────────────────────────┘
```

### Processing State (Future)
```
├─────────────────────────────────────────────────────────────────────┤
│ gpt-5                  Tokens: 1,234/128,000       Normal │ Thinking│
└─────────────────────────────────────────────────────────────────────┘
```

### Different Model
```
├─────────────────────────────────────────────────────────────────────┤
│ claude-4               Tokens: 5,678/200,000       Normal │ Ready   │
└─────────────────────────────────────────────────────────────────────┘
```

### Plan Mode (Future)
```
├─────────────────────────────────────────────────────────────────────┤
│ gpt-5                  Tokens: 2,000/128,000          Plan │ Ready  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Error Display

### Error Message
```
│  > problematic command                                              │
│                                                                     │
│  Error: Something went wrong with the operation                     │
│                                                                     │
│  > _                                                                │
```

### Warning Message
```
│  > some command                                                     │
│                                                                     │
│  Warning: Configuration value out of range, using default           │
│                                                                     │
│  Response continues here...                                         │
│                                                                     │
│  > _                                                                │
```

---

## 7. Interrupt Handling

### Ctrl+C Interrupt
```
│  > long operation                                                   │
│                                                                     │
│  Processing...                                                      │
│  ^C                                                                 │
│  Interrupted                                                        │
│                                                                     │
│  > _                                                                │
```

---

## 8. Exit Sequence

### Normal Exit (Ctrl+D)
```
│  > _                                                                │
│  ^D                                                                 │
│                                                                     │
│  Goodbye!                                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
$
```

---

## 9. Theme Comparison

### Dark Theme (Default)
```
┌─────────────────────────────────────────────────────────────────────┐
│ Background: #1a1b26                                                 │
│ ┌───────────────────────────────────────────────────────────────┐   │
│ │  Code-Forge v0.1.0        (Blue: #7aa2f7)                       │   │
│ │                                                               │   │
│ │  > Hello                (White: #c0caf5)                      │   │
│ │                                                               │   │
│ │  Response here          (White: #c0caf5)                      │   │
│ │                                                               │   │
│ │  Error: Something       (Red: #f7768e)                        │   │
│ │  Warning: Note          (Yellow: #e0af68)                     │   │
│ │  Success!               (Green: #9ece6a)                      │   │
│ └───────────────────────────────────────────────────────────────┘   │
│ Status bar background: #24283b                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Light Theme
```
┌─────────────────────────────────────────────────────────────────────┐
│ Background: #f5f5f5                                                 │
│ ┌───────────────────────────────────────────────────────────────┐   │
│ │  Code-Forge v0.1.0        (Blue: #2563eb)                       │   │
│ │                                                               │   │
│ │  > Hello                (Black: #1a1b26)                      │   │
│ │                                                               │   │
│ │  Response here          (Black: #1a1b26)                      │   │
│ │                                                               │   │
│ │  Error: Something       (Red: #ef4444)                        │   │
│ │  Warning: Note          (Yellow: #eab308)                     │   │
│ │  Success!               (Green: #22c55e)                      │   │
│ └───────────────────────────────────────────────────────────────┘   │
│ Status bar background: #e5e7eb                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 10. Narrow Terminal (80 columns)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  Code-Forge v0.1.0                                                             │
│  AI-powered CLI Development Assistant                                        │
│                                                                              │
│  Directory: /home/user/my-project                                            │
│  Type /help for commands, ? for shortcuts                                    │
│                                                                              │
│  > _                                                                         │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│ gpt-5              Tokens: 0/128,000                         Normal │ Ready  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Wide Terminal (120 columns)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                          │
│  Code-Forge v0.1.0                                                                                                         │
│  AI-powered CLI Development Assistant                                                                                    │
│                                                                                                                          │
│  Directory: /home/user/my-project                                                                                        │
│  Type /help for commands, ? for shortcuts                                                                                │
│                                                                                                                          │
│  > _                                                                                                                     │
│                                                                                                                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ gpt-5                                        Tokens: 0/128,000                                          Normal │ Ready  │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. History Search (Ctrl+R)

```
│  (reverse-i-search)`python': find all python files_                 │
```

---

## Notes

- Wireframes show ASCII representation; actual terminal uses ANSI colors
- Status bar uses Rich panel for consistent styling
- Code blocks use Rich Syntax for highlighting
- Markdown rendering handled by Rich Markdown
