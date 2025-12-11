# Code-Forge Documentation

Welcome to Code-Forge, an AI-powered coding assistant that provides access to 400+ models via OpenRouter API.

## What is Code-Forge?

Code-Forge is a command-line interface (CLI) tool that brings AI assistance directly to your terminal. It's designed to help developers with:

- **Code editing** - Read, write, and edit files with intelligent assistance
- **Code search** - Find files and search content with glob and grep patterns
- **Git operations** - Safe git operations with built-in guardrails
- **Shell commands** - Execute bash commands with permission controls
- **Session management** - Persistent sessions with context management
- **Extensibility** - Plugin system for custom tools and commands

## Key Features

### Multi-Model Support
Access 400+ AI models through OpenRouter, including Claude, GPT-4, Llama, and more.

### Powerful Tool System
Built-in tools for file operations, code search, and shell execution.

### Session Persistence
Save and resume conversations with automatic context management.

### Safety Guards
Permission system and git safety checks prevent dangerous operations.

### Plugin Architecture
Extend functionality with custom plugins for tools, commands, and hooks.

## Quick Links

- [Installation Guide](getting-started/installation.md)
- [Quick Start Tutorial](getting-started/quickstart.md)
- [Configuration Reference](reference/configuration.md)
- [Tool Reference](reference/tools.md)

## Getting Help

- Use `/help` in the CLI for command help
- Check the [User Guide](user-guide/commands.md) for detailed usage
- Report issues at [GitHub Issues](https://github.com/anthropics/forge/issues)

## Architecture Overview

```
                    ┌─────────────┐
                    │   User      │
                    │   Input     │
                    └──────┬──────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│                    Code-Forge CLI                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   Session   │  │    Tool     │  │  Permission │  │
│  │   Manager   │  │   System    │  │   System    │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
│         │                │                │          │
│         └────────────────┼────────────────┘          │
│                          │                           │
│                          ▼                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  LangChain  │  │    Hooks    │  │   Plugin    │  │
│  │  Middleware │  │   System    │  │   System    │  │
│  └──────┬──────┘  └─────────────┘  └─────────────┘  │
│         │                                            │
│         ▼                                            │
│  ┌─────────────┐                                     │
│  │  OpenRouter │                                     │
│  │    Client   │                                     │
│  └─────────────┘                                     │
└──────────────────────────────────────────────────────┘
```
