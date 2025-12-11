# Phase 7.2: Skills System - Implementation Plan

**Phase:** 7.2
**Name:** Skills System
**Dependencies:** Phase 6.1 (Slash Commands), Phase 2.1 (Tool System)

---

## Implementation Order

1. `base.py` - Skill base classes
2. `parser.py` - Skill file parser
3. `loader.py` - Skill loading
4. `registry.py` - Skill registry
5. `builtin/` - Built-in skills
6. `commands.py` - Skill commands
7. `__init__.py` - Package exports
8. Integration with REPL

---

## Step 1: Skill Base Classes (base.py)

```python
"""
Base classes for the skills system.

Skills provide domain-specific capabilities that modify
assistant behavior through specialized prompts and tools.
"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import re


@dataclass
class SkillConfig:
    """Configuration option for a skill.

    Attributes:
        name: Option name
        type: Value type (string, int, bool, choice)
        default: Default value
        description: Help text
        choices: Valid choices for 'choice' type
        required: Whether option must be provided
    """
    name: str
    type: str = "string"
    default: Any = None
    description: str = ""
    choices: list[str] | None = None
    required: bool = False

    def validate(self, value: Any) -> tuple[bool, str]:
        """Validate a value against this config.

        Returns:
            (is_valid, error_message)
        """
        if value is None:
            if self.required:
                return False, f"Required option '{self.name}' not provided"
            return True, ""

        if self.type == "string":
            if not isinstance(value, str):
                return False, f"'{self.name}' must be a string"

        elif self.type == "int":
            if not isinstance(value, int):
                return False, f"'{self.name}' must be an integer"

        elif self.type == "bool":
            if not isinstance(value, bool):
                return False, f"'{self.name}' must be a boolean"

        elif self.type == "choice":
            if self.choices and value not in self.choices:
                return False, f"'{self.name}' must be one of: {self.choices}"

        return True, ""


@dataclass
class SkillMetadata:
    """Metadata for a skill.

    Attributes:
        name: Unique skill identifier
        description: Human-readable description
        author: Skill author
        version: Version string
        tags: Categorization tags
        aliases: Alternative names
        examples: Usage examples
    """
    name: str
    description: str
    author: str = ""
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)

    def matches_query(self, query: str) -> bool:
        """Check if skill matches a search query."""
        query = query.lower()
        if query in self.name.lower():
            return True
        if query in self.description.lower():
            return True
        for tag in self.tags:
            if query in tag.lower():
                return True
        return False


@dataclass
class SkillDefinition:
    """Complete skill definition.

    Attributes:
        metadata: Skill metadata
        prompt: System prompt addition
        tools: Required tool names
        config: Configuration options
        source_path: Path to source file
        is_builtin: Whether this is a built-in skill
    """
    metadata: SkillMetadata
    prompt: str
    tools: list[str] = field(default_factory=list)
    config: list[SkillConfig] = field(default_factory=list)
    source_path: str | None = None
    is_builtin: bool = False

    def get_config_option(self, name: str) -> SkillConfig | None:
        """Get a config option by name."""
        for opt in self.config:
            if opt.name == name:
                return opt
        return None

    def validate_config(self, values: dict[str, Any]) -> list[str]:
        """Validate configuration values.

        Returns:
            List of error messages
        """
        errors = []
        for opt in self.config:
            value = values.get(opt.name, opt.default)
            valid, error = opt.validate(value)
            if not valid:
                errors.append(error)
        return errors


class Skill:
    """A skill that provides domain-specific capabilities.

    Skills modify assistant behavior by:
    - Adding specialized system prompts
    - Enabling specific tools
    - Maintaining skill-specific context
    """

    def __init__(self, definition: SkillDefinition):
        """Initialize skill.

        Args:
            definition: Skill definition
        """
        self.definition = definition
        self._active = False
        self._context: dict[str, Any] = {}
        self._activated_at: datetime | None = None

    @property
    def name(self) -> str:
        """Get skill name."""
        return self.definition.metadata.name

    @property
    def description(self) -> str:
        """Get skill description."""
        return self.definition.metadata.description

    @property
    def tags(self) -> list[str]:
        """Get skill tags."""
        return self.definition.metadata.tags

    @property
    def is_active(self) -> bool:
        """Check if skill is active."""
        return self._active

    @property
    def is_builtin(self) -> bool:
        """Check if this is a built-in skill."""
        return self.definition.is_builtin

    def activate(self, config: dict[str, Any] | None = None) -> list[str]:
        """Activate the skill.

        Args:
            config: Configuration values

        Returns:
            List of validation errors (empty if valid)
        """
        config = config or {}

        # Apply defaults
        for opt in self.definition.config:
            if opt.name not in config and opt.default is not None:
                config[opt.name] = opt.default

        # Validate config
        errors = self.definition.validate_config(config)
        if errors:
            return errors

        self._active = True
        self._context = config.copy()
        self._activated_at = datetime.now()
        return []

    def deactivate(self) -> None:
        """Deactivate the skill."""
        self._active = False
        self._context.clear()
        self._activated_at = None

    def get_prompt(self) -> str:
        """Get skill prompt with variable substitution.

        Variables in the format {{ name }} are replaced
        with values from the context.

        Security: Only allows alphanumeric values and common punctuation
        to prevent injection attacks through context values.
        """
        prompt = self.definition.prompt

        # Substitute variables with sanitized values
        def replace_var(match):
            var_name = match.group(1).strip()
            value = self._context.get(var_name)
            if value is None:
                return match.group(0)  # Keep original if not found

            # Sanitize value to prevent injection
            # Only allow safe characters: alphanumeric, spaces, common punctuation
            str_value = str(value)
            # Remove any potentially dangerous characters
            # Allow: letters, numbers, spaces, basic punctuation
            sanitized = re.sub(r'[^\w\s\-_.,:;!?@#$%&*()+=\[\]{}<>/\\|`~\'"]+', '', str_value)
            return sanitized

        prompt = re.sub(r'\{\{\s*(\w+)\s*\}\}', replace_var, prompt)
        return prompt

    def get_tools(self) -> list[str]:
        """Get required tools for this skill."""
        return self.definition.tools.copy()

    def get_context(self) -> dict[str, Any]:
        """Get current skill context."""
        return self._context.copy()

    def set_context(self, key: str, value: Any) -> None:
        """Set a context value."""
        self._context[key] = value

    def to_dict(self) -> dict:
        """Serialize skill state."""
        return {
            "name": self.name,
            "active": self._active,
            "context": self._context,
            "activated_at": (
                self._activated_at.isoformat()
                if self._activated_at else None
            ),
        }

    def get_help(self) -> str:
        """Get help text for this skill."""
        lines = [
            f"# {self.name}",
            "",
            self.description,
            "",
        ]

        if self.definition.metadata.author:
            lines.append(f"Author: {self.definition.metadata.author}")

        lines.append(f"Version: {self.definition.metadata.version}")

        if self.tags:
            lines.append(f"Tags: {', '.join(self.tags)}")

        if self.definition.tools:
            lines.extend([
                "",
                "## Required Tools",
                ", ".join(self.definition.tools),
            ])

        if self.definition.config:
            lines.extend([
                "",
                "## Configuration",
            ])
            for opt in self.definition.config:
                req = " (required)" if opt.required else ""
                default = f" [default: {opt.default}]" if opt.default else ""
                lines.append(f"- **{opt.name}**{req}: {opt.description}{default}")

        if self.definition.metadata.examples:
            lines.extend([
                "",
                "## Examples",
            ])
            for example in self.definition.metadata.examples:
                lines.append(f"- {example}")

        return "\n".join(lines)
```

---

## Step 2: Skill Parser (parser.py)

```python
"""
Skill file parser.

Parses skill definitions from YAML and Markdown files.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml
import re

from .base import SkillDefinition, SkillMetadata, SkillConfig


class SkillParseError(Exception):
    """Error parsing skill file."""
    pass


@dataclass
class ParseResult:
    """Result of parsing a skill file."""
    definition: SkillDefinition | None
    errors: list[str]
    warnings: list[str]


class SkillParser:
    """Parses skill definition files."""

    # Required fields in skill definition
    REQUIRED_FIELDS = ["name", "description"]

    def parse_file(self, path: Path) -> ParseResult:
        """Parse a skill file.

        Args:
            path: Path to skill file

        Returns:
            ParseResult with definition or errors
        """
        content = path.read_text()

        if path.suffix in (".yaml", ".yml"):
            return self.parse_yaml(content, str(path))
        elif path.suffix == ".md":
            return self.parse_markdown(content, str(path))
        else:
            return ParseResult(
                definition=None,
                errors=[f"Unknown file type: {path.suffix}"],
                warnings=[],
            )

    def parse_yaml(
        self,
        content: str,
        source_path: str = ""
    ) -> ParseResult:
        """Parse YAML skill file.

        Args:
            content: YAML content
            source_path: Source file path

        Returns:
            ParseResult
        """
        errors = []
        warnings = []

        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            return ParseResult(
                definition=None,
                errors=[f"YAML parse error: {e}"],
                warnings=[],
            )

        if not isinstance(data, dict):
            return ParseResult(
                definition=None,
                errors=["Skill file must be a YAML mapping"],
                warnings=[],
            )

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if errors:
            return ParseResult(None, errors, warnings)

        # Parse metadata
        metadata = SkillMetadata(
            name=data.get("name", ""),
            description=data.get("description", ""),
            author=data.get("author", ""),
            version=str(data.get("version", "1.0.0")),
            tags=data.get("tags", []),
            aliases=data.get("aliases", []),
            examples=data.get("examples", []),
        )

        # Parse config options
        config = []
        for opt_data in data.get("config", []):
            if isinstance(opt_data, dict):
                config.append(SkillConfig(
                    name=opt_data.get("name", ""),
                    type=opt_data.get("type", "string"),
                    default=opt_data.get("default"),
                    description=opt_data.get("description", ""),
                    choices=opt_data.get("choices"),
                    required=opt_data.get("required", False),
                ))

        # Build definition
        definition = SkillDefinition(
            metadata=metadata,
            prompt=data.get("prompt", ""),
            tools=data.get("tools", []),
            config=config,
            source_path=source_path,
        )

        # Validate
        validation_errors = self.validate(definition)
        errors.extend(validation_errors)

        if errors:
            return ParseResult(None, errors, warnings)

        return ParseResult(definition, [], warnings)

    def parse_markdown(
        self,
        content: str,
        source_path: str = ""
    ) -> ParseResult:
        """Parse Markdown skill file with YAML frontmatter.

        Args:
            content: Markdown content
            source_path: Source file path

        Returns:
            ParseResult
        """
        # Extract YAML frontmatter
        frontmatter_match = re.match(
            r'^---\s*\n(.*?)\n---\s*\n(.*)$',
            content,
            re.DOTALL
        )

        if not frontmatter_match:
            return ParseResult(
                definition=None,
                errors=["Markdown skill must have YAML frontmatter"],
                warnings=[],
            )

        yaml_content = frontmatter_match.group(1)
        markdown_body = frontmatter_match.group(2).strip()

        # Parse YAML part
        result = self.parse_yaml(yaml_content, source_path)

        if result.definition is None:
            return result

        # Use markdown body as prompt if not in frontmatter
        if not result.definition.prompt and markdown_body:
            result.definition.prompt = markdown_body

        return result

    def validate(self, definition: SkillDefinition) -> list[str]:
        """Validate skill definition.

        Args:
            definition: Definition to validate

        Returns:
            List of error messages
        """
        errors = []

        # Name validation
        if not definition.metadata.name:
            errors.append("Skill name cannot be empty")
        elif not re.match(r'^[a-z][a-z0-9-]*$', definition.metadata.name):
            errors.append(
                "Skill name must start with letter and contain "
                "only lowercase letters, numbers, and hyphens"
            )

        # Description validation
        if not definition.metadata.description:
            errors.append("Skill description cannot be empty")

        # Prompt validation
        if not definition.prompt:
            errors.append("Skill must have a prompt")

        # Config validation
        config_names = set()
        for opt in definition.config:
            if not opt.name:
                errors.append("Config option name cannot be empty")
            elif opt.name in config_names:
                errors.append(f"Duplicate config option: {opt.name}")
            else:
                config_names.add(opt.name)

            if opt.type not in ("string", "int", "bool", "choice"):
                errors.append(f"Invalid config type: {opt.type}")

            if opt.type == "choice" and not opt.choices:
                errors.append(
                    f"Config '{opt.name}' is type 'choice' but has no choices"
                )

        return errors
```

---

## Step 3: Skill Loader (loader.py)

```python
"""
Skill loading from files and directories.

Discovers and loads skills from various sources.
"""

from pathlib import Path
import logging
from typing import Callable

from .base import SkillDefinition, Skill
from .parser import SkillParser, ParseResult


logger = logging.getLogger(__name__)


class SkillLoadError(Exception):
    """Error loading skill."""
    pass


class SkillLoader:
    """Loads skills from files and directories."""

    # Supported file extensions
    SKILL_EXTENSIONS = {".yaml", ".yml", ".md"}

    def __init__(
        self,
        search_paths: list[Path] | None = None,
        parser: SkillParser | None = None,
    ):
        """Initialize loader.

        Args:
            search_paths: Directories to search for skills
            parser: Parser instance (created if None)
        """
        self.search_paths = search_paths or []
        self.parser = parser or SkillParser()
        self._on_error: list[Callable[[str, list[str]], None]] = []

    def add_search_path(self, path: Path) -> None:
        """Add a search path.

        Args:
            path: Directory to search
        """
        if path not in self.search_paths:
            self.search_paths.append(path)

    def on_error(
        self,
        callback: Callable[[str, list[str]], None]
    ) -> None:
        """Register error callback.

        Callback receives (file_path, errors).
        """
        self._on_error.append(callback)

    def load_from_file(self, path: Path) -> Skill | None:
        """Load a skill from a file.

        Args:
            path: Path to skill file

        Returns:
            Skill instance or None if failed
        """
        if not path.exists():
            self._report_error(str(path), [f"File not found: {path}"])
            return None

        if path.suffix not in self.SKILL_EXTENSIONS:
            self._report_error(
                str(path),
                [f"Unsupported file type: {path.suffix}"]
            )
            return None

        result = self.parser.parse_file(path)

        if result.errors:
            self._report_error(str(path), result.errors)
            return None

        if result.warnings:
            for warning in result.warnings:
                logger.warning(f"{path}: {warning}")

        if result.definition:
            return Skill(result.definition)

        return None

    def load_from_directory(self, directory: Path) -> list[Skill]:
        """Load all skills from a directory.

        Args:
            directory: Directory to load from

        Returns:
            List of loaded skills
        """
        skills = []

        if not directory.exists():
            logger.debug(f"Skill directory not found: {directory}")
            return skills

        if not directory.is_dir():
            self._report_error(
                str(directory),
                [f"Not a directory: {directory}"]
            )
            return skills

        for ext in self.SKILL_EXTENSIONS:
            for path in directory.glob(f"*{ext}"):
                skill = self.load_from_file(path)
                if skill:
                    skills.append(skill)

        return skills

    def discover_skills(self) -> list[Skill]:
        """Discover all skills in search paths.

        Returns:
            List of all discovered skills
        """
        skills = []
        seen_names = set()

        for search_path in self.search_paths:
            directory_skills = self.load_from_directory(search_path)

            for skill in directory_skills:
                if skill.name in seen_names:
                    logger.warning(
                        f"Duplicate skill '{skill.name}' in {search_path}, "
                        "using first found"
                    )
                    continue

                seen_names.add(skill.name)
                skills.append(skill)

        return skills

    def reload_skill(self, name: str) -> Skill | None:
        """Reload a skill by name.

        Searches for the skill file and reloads it.

        Args:
            name: Skill name

        Returns:
            Reloaded skill or None if not found
        """
        for search_path in self.search_paths:
            for ext in self.SKILL_EXTENSIONS:
                path = search_path / f"{name}{ext}"
                if path.exists():
                    return self.load_from_file(path)

        return None

    def _report_error(self, path: str, errors: list[str]) -> None:
        """Report loading errors."""
        for error in errors:
            logger.error(f"Skill load error ({path}): {error}")

        for callback in self._on_error:
            try:
                callback(path, errors)
            except Exception as e:
                logger.error(f"Error callback failed: {e}")


def get_default_search_paths() -> list[Path]:
    """Get default skill search paths.

    Returns:
        List of paths to search for skills
    """
    paths = []

    # User skills directory
    user_dir = Path.home() / ".forge" / "skills"
    if user_dir.exists():
        paths.append(user_dir)

    # Project skills directory
    project_dir = Path.cwd() / ".forge" / "skills"
    if project_dir.exists():
        paths.append(project_dir)

    return paths
```

---

## Step 4: Skill Registry (registry.py)

```python
"""
Skill registry for managing available skills.

Provides discovery, activation, and lifecycle management.
"""

import logging
from pathlib import Path
from typing import Callable

from .base import Skill, SkillDefinition
from .loader import SkillLoader, get_default_search_paths


logger = logging.getLogger(__name__)


class SkillRegistry:
    """Registry of available skills.

    Singleton that manages skill registration, discovery,
    and activation.
    """

    _instance: "SkillRegistry | None" = None

    def __init__(self):
        """Initialize registry."""
        self._skills: dict[str, Skill] = {}
        self._aliases: dict[str, str] = {}
        self._active_skill: Skill | None = None
        self._loader: SkillLoader | None = None
        self._on_activate: list[Callable[[Skill], None]] = []
        self._on_deactivate: list[Callable[[Skill], None]] = []

    @classmethod
    def get_instance(cls) -> "SkillRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None

    def set_loader(self, loader: SkillLoader) -> None:
        """Set the skill loader."""
        self._loader = loader

    def register(self, skill: Skill) -> None:
        """Register a skill.

        Args:
            skill: Skill to register

        Raises:
            ValueError: If skill name already registered
        """
        if skill.name in self._skills:
            raise ValueError(f"Skill already registered: {skill.name}")

        self._skills[skill.name] = skill

        # Register aliases
        for alias in skill.definition.metadata.aliases:
            if alias not in self._aliases:
                self._aliases[alias] = skill.name

        logger.debug(f"Registered skill: {skill.name}")

    def unregister(self, name: str) -> bool:
        """Unregister a skill.

        Args:
            name: Skill name

        Returns:
            True if unregistered, False if not found
        """
        skill = self._skills.get(name)
        if skill is None:
            return False

        # Deactivate if active
        if self._active_skill and self._active_skill.name == name:
            self.deactivate()

        # Remove aliases
        aliases_to_remove = [
            alias for alias, target in self._aliases.items()
            if target == name
        ]
        for alias in aliases_to_remove:
            del self._aliases[alias]

        del self._skills[name]
        logger.debug(f"Unregistered skill: {name}")
        return True

    def get(self, name: str) -> Skill | None:
        """Get skill by name or alias.

        Args:
            name: Skill name or alias

        Returns:
            Skill or None if not found
        """
        # Direct lookup
        if name in self._skills:
            return self._skills[name]

        # Alias lookup
        if name in self._aliases:
            return self._skills.get(self._aliases[name])

        return None

    def list_skills(self, tag: str | None = None) -> list[Skill]:
        """List skills, optionally filtered by tag.

        Args:
            tag: Filter by tag (None = all)

        Returns:
            List of matching skills
        """
        skills = list(self._skills.values())

        if tag:
            skills = [s for s in skills if tag in s.tags]

        return sorted(skills, key=lambda s: s.name)

    def list_builtin(self) -> list[Skill]:
        """List built-in skills."""
        return [s for s in self._skills.values() if s.is_builtin]

    def list_custom(self) -> list[Skill]:
        """List custom (non-builtin) skills."""
        return [s for s in self._skills.values() if not s.is_builtin]

    def search(self, query: str) -> list[Skill]:
        """Search skills by name or description.

        Args:
            query: Search query

        Returns:
            List of matching skills
        """
        matches = []
        for skill in self._skills.values():
            if skill.definition.metadata.matches_query(query):
                matches.append(skill)
        return sorted(matches, key=lambda s: s.name)

    def get_tags(self) -> list[str]:
        """Get all unique tags across skills."""
        tags = set()
        for skill in self._skills.values():
            tags.update(skill.tags)
        return sorted(tags)

    def activate(
        self,
        name: str,
        config: dict | None = None
    ) -> tuple[Skill | None, list[str]]:
        """Activate a skill.

        Args:
            name: Skill name or alias
            config: Configuration values

        Returns:
            (Skill, errors) - Skill is None if errors
        """
        skill = self.get(name)
        if skill is None:
            return None, [f"Skill not found: {name}"]

        # Deactivate current skill
        if self._active_skill:
            self.deactivate()

        # Activate new skill
        errors = skill.activate(config)
        if errors:
            return None, errors

        self._active_skill = skill

        # Notify listeners
        for callback in self._on_activate:
            try:
                callback(skill)
            except Exception as e:
                logger.error(f"Activate callback error: {e}")

        logger.info(f"Activated skill: {skill.name}")
        return skill, []

    def deactivate(self) -> Skill | None:
        """Deactivate current skill.

        Returns:
            Previously active skill, or None
        """
        if self._active_skill is None:
            return None

        skill = self._active_skill
        skill.deactivate()
        self._active_skill = None

        # Notify listeners
        for callback in self._on_deactivate:
            try:
                callback(skill)
            except Exception as e:
                logger.error(f"Deactivate callback error: {e}")

        logger.info(f"Deactivated skill: {skill.name}")
        return skill

    @property
    def active_skill(self) -> Skill | None:
        """Get currently active skill."""
        return self._active_skill

    def on_activate(self, callback: Callable[[Skill], None]) -> None:
        """Register activation callback."""
        self._on_activate.append(callback)

    def on_deactivate(self, callback: Callable[[Skill], None]) -> None:
        """Register deactivation callback."""
        self._on_deactivate.append(callback)

    def load_skills(self, search_paths: list[Path] | None = None) -> int:
        """Load skills from search paths.

        Args:
            search_paths: Paths to search (uses defaults if None)

        Returns:
            Number of skills loaded
        """
        if self._loader is None:
            paths = search_paths or get_default_search_paths()
            self._loader = SkillLoader(paths)

        skills = self._loader.discover_skills()

        count = 0
        for skill in skills:
            try:
                self.register(skill)
                count += 1
            except ValueError as e:
                logger.warning(f"Could not register skill: {e}")

        return count

    def reload_skill(self, name: str) -> Skill | None:
        """Reload a skill from disk.

        Args:
            name: Skill name

        Returns:
            Reloaded skill or None
        """
        if self._loader is None:
            return None

        skill = self._loader.reload_skill(name)
        if skill is None:
            return None

        # Replace in registry
        if name in self._skills:
            was_active = (
                self._active_skill and
                self._active_skill.name == name
            )
            self.unregister(name)
            self.register(skill)

            if was_active:
                self.activate(name)

        return skill

    def get_stats(self) -> dict:
        """Get skill statistics."""
        return {
            "total": len(self._skills),
            "builtin": len(self.list_builtin()),
            "custom": len(self.list_custom()),
            "active": self._active_skill.name if self._active_skill else None,
            "tags": self.get_tags(),
        }
```

---

## Step 5: Built-in Skills (builtin/)

### builtin/__init__.py

```python
"""
Built-in skills bundled with Code-Forge.
"""

from pathlib import Path

from ..base import Skill, SkillDefinition, SkillMetadata
from ..registry import SkillRegistry


def create_builtin_skill(
    name: str,
    description: str,
    prompt: str,
    tools: list[str] | None = None,
    tags: list[str] | None = None,
) -> Skill:
    """Create a built-in skill.

    Args:
        name: Skill name
        description: Skill description
        prompt: System prompt addition
        tools: Required tools
        tags: Categorization tags

    Returns:
        Skill instance
    """
    definition = SkillDefinition(
        metadata=SkillMetadata(
            name=name,
            description=description,
            author="Code-Forge",
            version="1.0.0",
            tags=tags or [],
        ),
        prompt=prompt,
        tools=tools or [],
        is_builtin=True,
    )
    return Skill(definition)


# PDF Skill
PDF_SKILL = create_builtin_skill(
    name="pdf",
    description="Analyze and extract information from PDF documents",
    tags=["documents", "analysis"],
    tools=["read", "bash"],
    prompt="""
You are specialized in working with PDF documents.

When working with PDFs:
1. Use appropriate tools to read PDF content
2. Analyze document structure (sections, headings, tables)
3. Extract relevant text and data
4. Summarize key information
5. Quote specific sections when relevant

Capabilities:
- Extract text from PDF pages
- Identify document structure
- Find specific information
- Summarize document contents
- Answer questions about PDF content

Always provide page numbers when referencing content.
""".strip(),
)


# Excel/CSV Skill
EXCEL_SKILL = create_builtin_skill(
    name="excel",
    description="Work with Excel and CSV spreadsheet files",
    tags=["data", "spreadsheets", "analysis"],
    tools=["read", "write", "bash"],
    prompt="""
You are specialized in working with spreadsheet data.

When working with spreadsheets:
1. First examine the structure (columns, rows, sheets)
2. Identify data types for each column
3. Look for patterns and relationships
4. Calculate relevant statistics
5. Provide data-driven insights

Capabilities:
- Read Excel (.xlsx, .xls) and CSV files
- Analyze column types and distributions
- Calculate statistics (mean, median, etc.)
- Identify trends and outliers
- Generate data summaries

Format data clearly using tables when appropriate.
""".strip(),
)


# Database Skill
DATABASE_SKILL = create_builtin_skill(
    name="database",
    description="Query and analyze databases",
    tags=["data", "sql", "databases"],
    tools=["read", "bash"],
    prompt="""
You are specialized in database operations.

When working with databases:
1. First understand the schema structure
2. Identify relationships between tables
3. Write safe, efficient queries
4. Use proper indexing considerations
5. Always use parameterized queries for safety

Capabilities:
- Analyze database schemas
- Write SQL queries (SELECT, INSERT, UPDATE, DELETE)
- Optimize query performance
- Generate migrations
- Design table structures

IMPORTANT: Never execute destructive queries without confirmation.
Always suggest EXPLAIN for complex queries.
""".strip(),
)


# API Skill
API_SKILL = create_builtin_skill(
    name="api",
    description="Work with REST and GraphQL APIs",
    tags=["api", "http", "integration"],
    tools=["read", "write", "bash"],
    prompt="""
You are specialized in API development and testing.

When working with APIs:
1. Analyze API structure and endpoints
2. Test endpoints with appropriate tools
3. Validate request/response formats
4. Handle authentication properly
5. Document API behavior

Capabilities:
- Test REST and GraphQL APIs
- Generate API documentation
- Create mock responses
- Debug API issues
- Validate schemas

Always be careful with authentication tokens and secrets.
Never expose sensitive data in logs or output.
""".strip(),
)


# Testing Skill
TESTING_SKILL = create_builtin_skill(
    name="testing",
    description="Write and run tests",
    tags=["testing", "quality", "automation"],
    tools=["read", "write", "bash", "glob", "grep"],
    prompt="""
You are specialized in software testing.

When working with tests:
1. Understand the code being tested
2. Identify edge cases and boundaries
3. Write clear, maintainable tests
4. Follow testing best practices
5. Aim for meaningful coverage

Capabilities:
- Write unit tests
- Write integration tests
- Run test suites
- Analyze coverage reports
- Debug failing tests

Testing principles:
- Each test should test one thing
- Use descriptive test names
- Arrange-Act-Assert pattern
- Mock external dependencies
- Test edge cases and errors
""".strip(),
)


# All built-in skills
BUILTIN_SKILLS = [
    PDF_SKILL,
    EXCEL_SKILL,
    DATABASE_SKILL,
    API_SKILL,
    TESTING_SKILL,
]


def register_builtin_skills(registry: SkillRegistry | None = None) -> int:
    """Register all built-in skills.

    Args:
        registry: Registry to use (singleton if None)

    Returns:
        Number of skills registered
    """
    if registry is None:
        registry = SkillRegistry.get_instance()

    count = 0
    for skill in BUILTIN_SKILLS:
        try:
            registry.register(skill)
            count += 1
        except ValueError:
            pass  # Already registered

    return count


__all__ = [
    "PDF_SKILL",
    "EXCEL_SKILL",
    "DATABASE_SKILL",
    "API_SKILL",
    "TESTING_SKILL",
    "BUILTIN_SKILLS",
    "register_builtin_skills",
    "create_builtin_skill",
]
```

---

## Step 6: Skill Commands (commands.py)

```python
"""
Slash commands for skill management.
"""

from ..commands.base import (
    Command,
    CommandCategory,
    CommandResult,
    SubcommandHandler,
)
from ..commands.parser import ParsedCommand
from ..commands.executor import CommandContext

from .registry import SkillRegistry


class SkillCommand(SubcommandHandler):
    """Skill management command."""

    name = "skill"
    aliases = ["sk"]
    description = "Manage skills"
    usage = "/skill [subcommand] [args]"
    category = CommandCategory.GENERAL

    def __init__(self):
        super().__init__()
        self._registry = SkillRegistry.get_instance()

    async def execute_default(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Show active skill or activate by name."""
        if parsed.args:
            # Activate skill by name
            name = parsed.args[0]
            return await self._activate(name, context)

        # Show active skill
        active = self._registry.active_skill
        if active:
            return CommandResult.ok(
                f"Active skill: {active.name}\n\n"
                f"{active.description}\n\n"
                f"Use /skill off to deactivate."
            )
        else:
            return CommandResult.ok(
                "No skill active.\n\n"
                "Use /skill <name> to activate a skill.\n"
                "Use /skill list to see available skills."
            )

    async def _activate(
        self,
        name: str,
        context: CommandContext,
    ) -> CommandResult:
        """Activate a skill."""
        if name == "off":
            skill = self._registry.deactivate()
            if skill:
                return CommandResult.ok(f"Deactivated skill: {skill.name}")
            return CommandResult.ok("No skill was active.")

        skill, errors = self._registry.activate(name)
        if errors:
            return CommandResult.fail("\n".join(errors))

        return CommandResult.ok(
            f"Activated skill: {skill.name}\n\n"
            f"{skill.description}"
        )


class SkillListCommand(Command):
    """List available skills."""

    name = "list"
    description = "List available skills"
    usage = "/skill list [--tag <tag>]"

    def __init__(self):
        self._registry = SkillRegistry.get_instance()

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        tag = parsed.get_kwarg("tag")
        skills = self._registry.list_skills(tag)

        if not skills:
            if tag:
                return CommandResult.ok(f"No skills found with tag: {tag}")
            return CommandResult.ok("No skills available.")

        lines = ["Available Skills:", ""]

        active = self._registry.active_skill
        for skill in skills:
            marker = " (active)" if active and active.name == skill.name else ""
            builtin = " [builtin]" if skill.is_builtin else ""
            tags = f" [{', '.join(skill.tags)}]" if skill.tags else ""

            lines.append(f"  {skill.name}{marker}{builtin}")
            lines.append(f"    {skill.description}{tags}")
            lines.append("")

        return CommandResult.ok("\n".join(lines))


class SkillInfoCommand(Command):
    """Show skill details."""

    name = "info"
    description = "Show skill details"
    usage = "/skill info <name>"

    def __init__(self):
        self._registry = SkillRegistry.get_instance()

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        name = parsed.get_arg(0)
        if not name:
            return CommandResult.fail("Usage: /skill info <name>")

        skill = self._registry.get(name)
        if not skill:
            return CommandResult.fail(f"Skill not found: {name}")

        return CommandResult.ok(skill.get_help())


class SkillSearchCommand(Command):
    """Search for skills."""

    name = "search"
    description = "Search for skills"
    usage = "/skill search <query>"

    def __init__(self):
        self._registry = SkillRegistry.get_instance()

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        query = " ".join(parsed.args) if parsed.args else ""
        if not query:
            return CommandResult.fail("Usage: /skill search <query>")

        skills = self._registry.search(query)

        if not skills:
            return CommandResult.ok(f"No skills matching: {query}")

        lines = [f"Skills matching '{query}':", ""]
        for skill in skills:
            lines.append(f"  {skill.name}")
            lines.append(f"    {skill.description}")
            lines.append("")

        return CommandResult.ok("\n".join(lines))


def register_skill_commands(registry) -> None:
    """Register skill commands with command registry."""
    skill_cmd = SkillCommand()
    skill_cmd.subcommands = {
        "list": SkillListCommand(),
        "info": SkillInfoCommand(),
        "search": SkillSearchCommand(),
    }
    registry.register(skill_cmd)
```

---

## Step 7: Package Exports (__init__.py)

```python
"""
Skills system package.

Provides domain-specific capabilities through reusable skills.
"""

from .base import (
    Skill,
    SkillConfig,
    SkillDefinition,
    SkillMetadata,
)
from .parser import (
    SkillParser,
    SkillParseError,
    ParseResult,
)
from .loader import (
    SkillLoader,
    SkillLoadError,
    get_default_search_paths,
)
from .registry import (
    SkillRegistry,
)
from .builtin import (
    PDF_SKILL,
    EXCEL_SKILL,
    DATABASE_SKILL,
    API_SKILL,
    TESTING_SKILL,
    BUILTIN_SKILLS,
    register_builtin_skills,
)


__all__ = [
    # Base
    "Skill",
    "SkillConfig",
    "SkillDefinition",
    "SkillMetadata",
    # Parser
    "SkillParser",
    "SkillParseError",
    "ParseResult",
    # Loader
    "SkillLoader",
    "SkillLoadError",
    "get_default_search_paths",
    # Registry
    "SkillRegistry",
    # Built-in
    "PDF_SKILL",
    "EXCEL_SKILL",
    "DATABASE_SKILL",
    "API_SKILL",
    "TESTING_SKILL",
    "BUILTIN_SKILLS",
    "register_builtin_skills",
]


def setup_skills() -> SkillRegistry:
    """Set up the skills system.

    Returns:
        Configured skill registry
    """
    registry = SkillRegistry.get_instance()

    # Register built-in skills
    register_builtin_skills(registry)

    # Load user/project skills
    registry.load_skills()

    return registry
```

---

## Testing Strategy

1. Unit test Skill base class
2. Unit test SkillParser (YAML and Markdown)
3. Unit test SkillLoader
4. Unit test SkillRegistry
5. Test built-in skills
6. Integration test with commands
7. Test skill file hot reload
