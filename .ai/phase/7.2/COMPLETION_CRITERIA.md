# Phase 7.2: Skills System - Completion Criteria

**Phase:** 7.2
**Name:** Skills System
**Dependencies:** Phase 6.1 (Slash Commands), Phase 2.1 (Tool System)

---

## Completion Checklist

### 1. Skill Base Classes (base.py)

- [ ] `SkillConfig` dataclass implemented
  - [ ] `name: str`
  - [ ] `type: str` (string, int, bool, choice)
  - [ ] `default: Any`
  - [ ] `description: str`
  - [ ] `choices: list[str] | None`
  - [ ] `validate(value)` method

- [ ] `SkillMetadata` dataclass implemented
  - [ ] `name: str`
  - [ ] `description: str`
  - [ ] `author: str`
  - [ ] `version: str`
  - [ ] `tags: list[str]`
  - [ ] `aliases: list[str]`
  - [ ] `examples: list[str]`
  - [ ] `to_dict()` method
  - [ ] `from_dict()` class method

- [ ] `SkillDefinition` dataclass implemented
  - [ ] `metadata: SkillMetadata`
  - [ ] `prompt: str`
  - [ ] `tools: list[str]`
  - [ ] `config: list[SkillConfig]`
  - [ ] `source_path: str | None`
  - [ ] `to_dict()` method
  - [ ] `from_dict()` class method
  - [ ] `validate()` method returns errors list

- [ ] `Skill` class implemented
  - [ ] `definition: SkillDefinition`
  - [ ] `_active: bool` private state
  - [ ] `_context: dict[str, Any]` private state
  - [ ] `name` property
  - [ ] `description` property
  - [ ] `is_active` property
  - [ ] `activate(config)` method
  - [ ] `deactivate()` method
  - [ ] `get_prompt()` method with variable substitution
  - [ ] `get_tools()` method
  - [ ] `to_dict()` method

### 2. Skill Parser (parser.py)

- [ ] `SkillParser` class implemented
  - [ ] `parse_yaml(content)` method
  - [ ] `parse_markdown(content)` method
  - [ ] `parse(content, extension)` method
  - [ ] `validate(definition)` method returns errors list
  - [ ] `_parse_frontmatter()` helper method
  - [ ] `_extract_config()` helper method

- [ ] YAML parsing
  - [ ] Handles all skill fields
  - [ ] Proper error messages for invalid YAML

- [ ] Markdown parsing
  - [ ] Extracts YAML frontmatter
  - [ ] Uses markdown body as prompt
  - [ ] Handles missing frontmatter gracefully

- [ ] Validation
  - [ ] Checks required fields (name, description, prompt)
  - [ ] Validates config option types
  - [ ] Warns on unknown tools

### 3. Skill Loader (loader.py)

- [ ] `SkillLoader` class implemented
  - [ ] `search_paths: list[Path]`
  - [ ] `_parser: SkillParser` instance
  - [ ] `load_from_file(path)` method
  - [ ] `load_from_directory(directory)` method
  - [ ] `discover_skills()` method
  - [ ] `reload_skill(path)` method
  - [ ] `_get_skill_files(directory)` helper

- [ ] File loading
  - [ ] Loads .yaml files
  - [ ] Loads .md files
  - [ ] Sets source_path on definitions
  - [ ] Handles file read errors gracefully

- [ ] Discovery
  - [ ] Searches user directory (~/.src/opencode/skills/)
  - [ ] Searches project directory (.src/opencode/skills/)
  - [ ] Project skills override user skills
  - [ ] Ignores non-skill files

### 4. Skill Registry (registry.py)

- [ ] `SkillRegistry` singleton implemented
  - [ ] `_instance: SkillRegistry | None` class variable
  - [ ] `_skills: dict[str, Skill]`
  - [ ] `_aliases: dict[str, str]`
  - [ ] `_active_skill: Skill | None`
  - [ ] `_loader: SkillLoader`
  - [ ] `get_instance()` class method
  - [ ] `reset_instance()` class method

- [ ] Registration
  - [ ] `register(skill)` method
  - [ ] `unregister(name)` method
  - [ ] Registers aliases automatically
  - [ ] Prevents duplicate names
  - [ ] Raises ValueError on conflict

- [ ] Lookup
  - [ ] `get(name)` method
  - [ ] Returns skill by name
  - [ ] Returns skill by alias
  - [ ] Returns None for unknown

- [ ] Listing
  - [ ] `list_skills(tag)` method
  - [ ] Optional tag filtering
  - [ ] Returns list of Skill objects

- [ ] Search
  - [ ] `search(query)` method
  - [ ] Searches name and description
  - [ ] Case-insensitive matching

- [ ] Activation
  - [ ] `activate(name, config)` method
  - [ ] `deactivate()` method
  - [ ] `active_skill` property
  - [ ] Deactivates previous skill on switch
  - [ ] Raises KeyError for unknown skill

- [ ] Reload
  - [ ] `reload()` method
  - [ ] Preserves active skill if still valid

### 5. Built-in Skills (builtin/)

- [ ] PDF skill implemented
  - [ ] Name: "pdf"
  - [ ] Description mentions PDF documents
  - [ ] Tools: read, bash
  - [ ] Appropriate prompt for PDF analysis

- [ ] Excel skill implemented
  - [ ] Name: "excel"
  - [ ] Aliases: xlsx, csv
  - [ ] Tags: data, spreadsheets
  - [ ] Tools: read, write, bash
  - [ ] Appropriate prompt for spreadsheet analysis

- [ ] Database skill implemented
  - [ ] Name: "database"
  - [ ] Aliases: db
  - [ ] Tags: data, sql
  - [ ] Tools: read, bash
  - [ ] Appropriate prompt for database work

- [ ] API skill implemented
  - [ ] Name: "api"
  - [ ] Tags: api, testing
  - [ ] Tools: read, bash
  - [ ] Appropriate prompt for API work

- [ ] Testing skill implemented
  - [ ] Name: "testing"
  - [ ] Aliases: test
  - [ ] Tags: testing, quality
  - [ ] Tools: read, write, bash
  - [ ] Appropriate prompt for testing

- [ ] `get_builtin_skills()` function
  - [ ] Returns list of built-in SkillDefinitions
  - [ ] Used by registry initialization

### 6. Skill Commands (commands.py)

- [ ] `SkillCommand` class implemented
  - [ ] Inherits from Command base class
  - [ ] `name = "skill"`
  - [ ] `aliases = ["sk"]`
  - [ ] `description` provided
  - [ ] `execute(args, context)` method

- [ ] Subcommand handling
  - [ ] No args: show active or list
  - [ ] `<name>`: activate skill
  - [ ] `off`: deactivate skill
  - [ ] `list`: list all skills
  - [ ] `list --tag <tag>`: filter by tag
  - [ ] `info <name>`: show skill details
  - [ ] `search <query>`: search skills
  - [ ] `reload`: reload all skills

- [ ] Output formatting
  - [ ] Clear activation messages
  - [ ] Formatted skill lists
  - [ ] Detailed skill info display
  - [ ] Search results formatting

### 7. Package Exports (__init__.py)

- [ ] All public classes exported
  - [ ] Skill
  - [ ] SkillConfig
  - [ ] SkillMetadata
  - [ ] SkillDefinition
  - [ ] SkillParser
  - [ ] SkillLoader
  - [ ] SkillRegistry
- [ ] `__all__` list complete

### 8. Integration Points

- [ ] Slash command integration
  - [ ] SkillCommand registered with CommandRegistry
  - [ ] /skill commands functional

- [ ] Tool system integration
  - [ ] Active skill filters available tools
  - [ ] Tools returned from skill.get_tools()

- [ ] Session integration
  - [ ] Active skill saved in session
  - [ ] Active skill restored on resume

- [ ] REPL integration
  - [ ] Skill prompt added to system prompt
  - [ ] Skill indicator in REPL (optional)

### 9. Testing

- [ ] Unit tests for SkillConfig
- [ ] Unit tests for SkillMetadata
- [ ] Unit tests for SkillDefinition
- [ ] Unit tests for Skill
- [ ] Unit tests for SkillParser
- [ ] Unit tests for SkillLoader
- [ ] Unit tests for SkillRegistry
- [ ] Unit tests for SkillCommand
- [ ] Tests for built-in skills
- [ ] Integration tests with commands
- [ ] Test coverage ≥ 90%

### 10. Code Quality

- [ ] McCabe complexity ≤ 10 for all functions
- [ ] Type hints on all public methods
- [ ] Docstrings on all public classes/methods
- [ ] No circular imports
- [ ] Follows project code style

---

## Verification Commands

```bash
# Run unit tests
pytest tests/skills/ -v

# Run with coverage
pytest tests/skills/ --cov=src/opencode/skills --cov-report=term-missing

# Check coverage threshold
pytest tests/skills/ --cov=src/opencode/skills --cov-fail-under=90

# Type checking
mypy src/opencode/skills/

# Complexity check
flake8 src/opencode/skills/ --max-complexity=10
```

---

## Test Scenarios

### Skill Parsing Tests

```python
def test_parse_yaml_skill():
    content = """
    name: test-skill
    description: A test skill
    prompt: You are a test assistant.
    """
    parser = SkillParser()
    definition = parser.parse_yaml(content)
    assert definition.metadata.name == "test-skill"
    assert "test assistant" in definition.prompt

def test_parse_markdown_skill():
    content = """---
    name: md-skill
    description: Markdown skill
    ---

    You are specialized in markdown.
    """
    parser = SkillParser()
    definition = parser.parse_markdown(content)
    assert definition.metadata.name == "md-skill"
    assert "markdown" in definition.prompt.lower()
```

### Skill Registry Tests

```python
def test_register_skill():
    registry = SkillRegistry()
    skill = create_test_skill("test")
    registry.register(skill)
    assert registry.get("test") is skill

def test_activate_skill():
    registry = SkillRegistry()
    skill = create_test_skill("pdf")
    registry.register(skill)

    registry.activate("pdf")
    assert registry.active_skill is skill
    assert skill.is_active

def test_switch_skill_deactivates_previous():
    registry = SkillRegistry()
    pdf_skill = create_test_skill("pdf")
    excel_skill = create_test_skill("excel")
    registry.register(pdf_skill)
    registry.register(excel_skill)

    registry.activate("pdf")
    registry.activate("excel")

    assert not pdf_skill.is_active
    assert excel_skill.is_active
```

### Skill Loader Tests

```python
def test_load_from_file(tmp_path):
    skill_file = tmp_path / "test.yaml"
    skill_file.write_text("""
    name: test
    description: Test skill
    prompt: Test prompt
    """)

    loader = SkillLoader()
    definition = loader.load_from_file(skill_file)
    assert definition.metadata.name == "test"
    assert definition.source_path == str(skill_file)

def test_discover_skills(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    (skills_dir / "skill1.yaml").write_text("name: skill1\n...")
    (skills_dir / "skill2.yaml").write_text("name: skill2\n...")

    loader = SkillLoader(search_paths=[skills_dir])
    definitions = loader.discover_skills()
    assert len(definitions) == 2
```

### Skill Command Tests

```python
def test_skill_list_command():
    registry = SkillRegistry.get_instance()
    # Register some skills

    command = SkillCommand()
    result = command.execute(["list"], context)

    assert "pdf" in result
    assert "excel" in result

def test_skill_activate_command():
    command = SkillCommand()
    result = command.execute(["pdf"], context)

    assert "Activated" in result
    registry = SkillRegistry.get_instance()
    assert registry.active_skill.name == "pdf"
```

### Variable Substitution Tests

```python
def test_variable_substitution():
    definition = SkillDefinition(
        metadata=SkillMetadata(name="test", description="Test"),
        prompt="Analyze {{ file_path }}"
    )
    skill = Skill(definition)
    skill.activate({"file_path": "doc.pdf"})

    prompt = skill.get_prompt()
    assert "Analyze doc.pdf" in prompt
```

---

## Definition of Done

Phase 7.2 is complete when:

1. All checklist items are checked off
2. All unit tests pass
3. Test coverage is ≥ 90%
4. Code complexity is ≤ 10
5. Type checking passes with no errors
6. All built-in skills work correctly
7. Custom skills can be loaded from files
8. Skill commands work properly
9. Skills integrate with session persistence
10. Skill prompts augment system prompt
11. Tool filtering works per skill
12. Hot reload functions correctly
13. Documentation is complete
14. Code review approved

---

## Dependencies Verification

Before starting Phase 7.2, verify:

- [ ] Phase 6.1 (Slash Commands) is complete
  - [ ] CommandRegistry available
  - [ ] Command base class available
  - [ ] Commands can be registered

- [ ] Phase 2.1 (Tool System) is complete
  - [ ] ToolRegistry available
  - [ ] Tools can be filtered by name

- [ ] Phase 5.1 (Session Management) is complete
  - [ ] Session can save/restore state
  - [ ] Session metadata accessible

---

## Notes

- Skills are capability bundles with prompts and tool lists
- Only one skill can be active at a time
- Skills augment (not replace) the base system prompt
- Tool filtering restricts available tools to skill needs
- Custom skills support both YAML and Markdown formats
- Project skills override user skills with same name
- Hot reload allows skill development iteration
- All validation errors should be user-friendly
