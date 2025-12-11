# Phase 7.2: Skills System - Requirements

**Phase:** 7.2
**Name:** Skills System
**Dependencies:** Phase 6.1 (Slash Commands), Phase 2.1 (Tool System)

---

## Overview

Phase 7.2 implements the skills system for Code-Forge, providing reusable, domain-specific capabilities that can be invoked via slash commands. Skills bundle specialized prompts, tools, and behaviors for common tasks like working with specific file formats, frameworks, or workflows.

---

## Goals

1. Define skill interface and structure
2. Implement skill loader and registry
3. Create built-in skills (PDF, Excel, etc.)
4. Enable skill invocation via `/skill` command
5. Support custom user-defined skills
6. Provide skill discovery and help

---

## Non-Goals (This Phase)

- Skill marketplace/sharing
- Skill versioning
- Skill dependencies on other skills
- Skill sandboxing/isolation
- Visual skill builder

---

## Functional Requirements

### FR-1: Skill Definition

**FR-1.1:** Skill structure
- Unique skill name
- Human-readable description
- System prompt additions
- Required tools list
- Optional configuration

**FR-1.2:** Skill metadata
- Author information
- Version string
- Tags/categories
- Usage examples

**FR-1.3:** Skill prompts
- Main skill prompt
- Context-specific prompts
- Variable substitution

### FR-2: Skill Loading

**FR-2.1:** Built-in skills
- Bundled with application
- Always available
- Cannot be modified

**FR-2.2:** User skills
- Loaded from `.src/forge/skills/`
- YAML or Markdown format
- Hot reload support

**FR-2.3:** Project skills
- Loaded from project `.src/forge/skills/`
- Override user skills
- Project-specific behaviors

### FR-3: Skill Registry

**FR-3.1:** Registration
- Register skills at startup
- Dynamic registration
- Conflict resolution

**FR-3.2:** Discovery
- List available skills
- Search by name/tag
- Filter by category

**FR-3.3:** Resolution
- Find skill by name
- Find skill by alias
- Fuzzy matching

### FR-4: Skill Invocation

**FR-4.1:** Command invocation
- `/skill <name>` activates skill
- Skill modifies system prompt
- Skill enables required tools

**FR-4.2:** Automatic invocation
- Detect skill-relevant context
- Suggest appropriate skill
- Auto-activate option

**FR-4.3:** Skill context
- Skill-specific state
- Persists during session
- Cleared on skill switch

### FR-5: Built-in Skills

**FR-5.1:** PDF skill
- Read and analyze PDFs
- Extract text and images
- Summarize documents

**FR-5.2:** Excel/CSV skill
- Read spreadsheet data
- Analyze data patterns
- Generate insights

**FR-5.3:** Database skill
- Query databases
- Schema analysis
- SQL generation

**FR-5.4:** API skill
- Test API endpoints
- Generate documentation
- Mock responses

**FR-5.5:** Testing skill
- Write test cases
- Run tests
- Coverage analysis

### FR-6: Custom Skills

**FR-6.1:** Skill file format
- YAML frontmatter
- Markdown body
- Template variables

**FR-6.2:** Skill validation
- Validate structure
- Check required fields
- Report errors

**FR-6.3:** Skill installation
- Copy to skills directory
- Validate and register
- Confirmation message

---

## Non-Functional Requirements

### NFR-1: Performance
- Skill load < 50ms each
- Skill switch < 10ms
- Minimal memory per skill

### NFR-2: Usability
- Clear skill descriptions
- Helpful error messages
- Easy skill creation

### NFR-3: Extensibility
- Simple skill format
- Plugin skills supported
- Clear extension points

---

## Technical Specifications

### Package Structure

```
src/forge/skills/
├── __init__.py           # Package exports
├── base.py               # Skill base class
├── loader.py             # Skill loading
├── registry.py           # Skill registry
├── parser.py             # Skill file parser
└── builtin/              # Built-in skills
    ├── __init__.py
    ├── pdf.py
    ├── excel.py
    ├── database.py
    ├── api.py
    └── testing.py
```

### Skill File Format

```yaml
# .src/forge/skills/my-skill.yaml
name: my-skill
description: Description of what this skill does
author: Your Name
version: 1.0.0
tags:
  - category1
  - category2

# Required tools for this skill
tools:
  - read
  - write
  - bash

# Configuration options
config:
  option1:
    type: string
    default: "value"
    description: What this option does

# The skill prompt (can also use markdown body)
prompt: |
  You are now using the my-skill skill.

  When working with [specific domain]:
  1. First step
  2. Second step
  3. Third step

  Always [important behavior].
```

### Class Signatures

```python
# base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillConfig:
    """Configuration option for a skill."""
    name: str
    type: str  # string, int, bool, choice
    default: Any = None
    description: str = ""
    choices: list[str] | None = None


@dataclass
class SkillMetadata:
    """Metadata for a skill."""
    name: str
    description: str
    author: str = ""
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)


@dataclass
class SkillDefinition:
    """Complete skill definition."""
    metadata: SkillMetadata
    prompt: str
    tools: list[str] = field(default_factory=list)
    config: list[SkillConfig] = field(default_factory=list)
    source_path: str | None = None


class Skill(ABC):
    """Base class for skills."""

    def __init__(self, definition: SkillDefinition):
        self.definition = definition
        self._active = False
        self._context: dict[str, Any] = {}

    @property
    def name(self) -> str:
        return self.definition.metadata.name

    @property
    def description(self) -> str:
        return self.definition.metadata.description

    @property
    def is_active(self) -> bool:
        return self._active

    def activate(self, config: dict[str, Any] | None = None) -> None:
        """Activate the skill."""
        self._active = True
        self._context = config or {}

    def deactivate(self) -> None:
        """Deactivate the skill."""
        self._active = False
        self._context.clear()

    def get_prompt(self) -> str:
        """Get skill prompt with variable substitution."""
        prompt = self.definition.prompt
        for key, value in self._context.items():
            prompt = prompt.replace(f"{{{{ {key} }}}}", str(value))
        return prompt

    def get_tools(self) -> list[str]:
        """Get required tools for this skill."""
        return self.definition.tools.copy()


# loader.py
from pathlib import Path


class SkillLoader:
    """Loads skills from files."""

    def __init__(self, search_paths: list[Path] | None = None):
        self.search_paths = search_paths or []

    def load_from_file(self, path: Path) -> SkillDefinition:
        """Load a skill from a file."""
        ...

    def load_from_directory(self, directory: Path) -> list[SkillDefinition]:
        """Load all skills from a directory."""
        ...

    def discover_skills(self) -> list[SkillDefinition]:
        """Discover all skills in search paths."""
        ...


# registry.py
class SkillRegistry:
    """Registry of available skills."""

    _instance: "SkillRegistry | None" = None

    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._aliases: dict[str, str] = {}
        self._active_skill: Skill | None = None

    @classmethod
    def get_instance(cls) -> "SkillRegistry":
        """Get singleton instance."""
        ...

    def register(self, skill: Skill) -> None:
        """Register a skill."""
        ...

    def unregister(self, name: str) -> bool:
        """Unregister a skill."""
        ...

    def get(self, name: str) -> Skill | None:
        """Get skill by name or alias."""
        ...

    def list_skills(self, tag: str | None = None) -> list[Skill]:
        """List skills, optionally filtered by tag."""
        ...

    def search(self, query: str) -> list[Skill]:
        """Search skills by name or description."""
        ...

    def activate(self, name: str, config: dict | None = None) -> Skill:
        """Activate a skill."""
        ...

    def deactivate(self) -> None:
        """Deactivate current skill."""
        ...

    @property
    def active_skill(self) -> Skill | None:
        """Get currently active skill."""
        ...


# parser.py
class SkillParser:
    """Parses skill definition files."""

    def parse_yaml(self, content: str) -> SkillDefinition:
        """Parse YAML skill file."""
        ...

    def parse_markdown(self, content: str) -> SkillDefinition:
        """Parse Markdown skill file with YAML frontmatter."""
        ...

    def validate(self, definition: SkillDefinition) -> list[str]:
        """Validate skill definition, return errors."""
        ...
```

---

## Built-in Skills Reference

### PDF Skill

```yaml
name: pdf
description: Analyze and extract information from PDF documents
tags: [documents, analysis]
tools: [read, bash]
prompt: |
  You are specialized in working with PDF documents.

  Capabilities:
  - Extract text from PDFs
  - Analyze document structure
  - Summarize content
  - Find specific information

  When working with PDFs:
  1. First read the PDF to understand its contents
  2. Provide structured analysis
  3. Quote relevant sections when answering
```

### Excel Skill

```yaml
name: excel
description: Work with Excel and CSV spreadsheet files
tags: [data, spreadsheets]
tools: [read, write, bash]
prompt: |
  You are specialized in working with spreadsheet data.

  Capabilities:
  - Read Excel (.xlsx) and CSV files
  - Analyze data patterns
  - Calculate statistics
  - Generate insights

  When working with spreadsheets:
  1. First examine the structure (columns, rows)
  2. Identify data types and patterns
  3. Provide data-driven insights
```

### Database Skill

```yaml
name: database
description: Query and analyze databases
tags: [data, sql]
tools: [read, bash]
prompt: |
  You are specialized in database operations.

  Capabilities:
  - Analyze database schemas
  - Write SQL queries
  - Optimize query performance
  - Generate migrations

  When working with databases:
  1. First understand the schema
  2. Write safe, efficient queries
  3. Always use parameterized queries
  4. Consider indexes and performance
```

---

## Skill Commands

| Command | Description |
|---------|-------------|
| `/skill` | Show active skill or list available |
| `/skill <name>` | Activate a skill |
| `/skill off` | Deactivate current skill |
| `/skill list` | List all available skills |
| `/skill info <name>` | Show skill details |
| `/skill search <query>` | Search for skills |

---

## Integration Points

### With Slash Commands (Phase 6.1)
- Skill commands registered
- `/skill` command handler
- Help integration

### With Tool System (Phase 2.1)
- Skills specify required tools
- Tools enabled on activation

### With Session (Phase 5.1)
- Active skill saved in session
- Skill restored on resume

---

## Testing Requirements

1. Unit tests for Skill base class
2. Unit tests for SkillLoader
3. Unit tests for SkillRegistry
4. Unit tests for SkillParser
5. Tests for built-in skills
6. Integration tests with commands
7. Test coverage ≥ 90%

---

## Acceptance Criteria

1. Skills load correctly from files
2. Built-in skills all functional
3. Skill activation modifies prompts
4. Skill commands work properly
5. Custom skills can be created
6. Skill discovery finds all skills
7. Skill help is comprehensive
8. Skills persist in session
9. Hot reload works
10. Error handling is graceful
