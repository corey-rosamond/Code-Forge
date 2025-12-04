# Phase 7.2: Skills System - Gherkin Specifications

**Phase:** 7.2
**Name:** Skills System
**Dependencies:** Phase 6.1 (Slash Commands), Phase 2.1 (Tool System)

---

## Feature: Skill Definition

### Scenario: Create skill with required fields
```gherkin
Given a SkillMetadata with name="pdf" and description="PDF analysis"
And a prompt "You are specialized in PDF documents"
When I create a SkillDefinition with these values
Then definition.metadata.name should be "pdf"
And definition.metadata.description should be "PDF analysis"
And definition.prompt should contain "PDF documents"
```

### Scenario: Create skill with optional fields
```gherkin
Given a SkillMetadata with author="OpenCode Team"
And version="1.0.0"
And tags=["documents", "analysis"]
When I create a SkillDefinition
Then definition.metadata.author should be "OpenCode Team"
And definition.metadata.version should be "1.0.0"
And definition.metadata.tags should contain "documents"
```

### Scenario: Skill with tool requirements
```gherkin
Given a SkillDefinition with tools=["read", "bash", "glob"]
When I call definition.tools
Then it should return ["read", "bash", "glob"]
```

### Scenario: Skill with configuration options
```gherkin
Given a SkillConfig with name="output_format"
And type="choice"
And choices=["text", "json", "markdown"]
And default="text"
When I add it to a SkillDefinition
Then definition.config should contain the option
And option.choices should have 3 items
```

---

## Feature: Skill Parsing

### Scenario: Parse YAML skill file
```gherkin
Given a YAML file with valid skill definition:
  """
  name: pdf
  description: Analyze PDF documents
  tools:
    - read
    - bash
  prompt: |
    You are specialized in PDF analysis.
  """
When I call parser.parse_yaml(content)
Then result should be a SkillDefinition
And result.metadata.name should be "pdf"
And result.tools should contain "read"
```

### Scenario: Parse Markdown skill file
```gherkin
Given a Markdown file with YAML frontmatter:
  """
  ---
  name: excel
  description: Work with spreadsheets
  ---

  You are specialized in spreadsheet analysis.
  """
When I call parser.parse_markdown(content)
Then result should be a SkillDefinition
And result.metadata.name should be "excel"
And result.prompt should contain "spreadsheet analysis"
```

### Scenario: Parse file with variable templates
```gherkin
Given a skill file with prompt containing "{{ file_path }}"
When I parse the file
Then definition.prompt should contain "{{ file_path }}"
And variable substitution should happen on activation
```

### Scenario: Validate skill definition - missing name
```gherkin
Given a skill definition without a name
When I call parser.validate(definition)
Then result should contain error "name is required"
```

### Scenario: Validate skill definition - empty prompt
```gherkin
Given a skill definition with empty prompt
When I call parser.validate(definition)
Then result should contain error "prompt is required"
```

### Scenario: Validate skill definition - invalid tool
```gherkin
Given a skill definition with tools=["nonexistent_tool"]
When I call parser.validate(definition)
Then result should contain warning "unknown tool: nonexistent_tool"
```

---

## Feature: Skill Loading

### Scenario: Load skill from YAML file
```gherkin
Given a file at ~/.src/opencode/skills/custom.yaml
And the file contains valid skill YAML
When I call loader.load_from_file(path)
Then result should be a SkillDefinition
And result.source_path should be the file path
```

### Scenario: Load skill from Markdown file
```gherkin
Given a file at ~/.src/opencode/skills/custom.md
And the file has YAML frontmatter and markdown body
When I call loader.load_from_file(path)
Then result should be a SkillDefinition
And prompt should come from markdown body
```

### Scenario: Load all skills from directory
```gherkin
Given a directory with 3 skill files
When I call loader.load_from_directory(path)
Then result should have 3 SkillDefinitions
```

### Scenario: Discover skills from search paths
```gherkin
Given search_paths = [user_dir, project_dir]
And user_dir has 2 skills
And project_dir has 1 skill
When I call loader.discover_skills()
Then result should have 3 skills total
```

### Scenario: Project skill overrides user skill
```gherkin
Given user skill "custom" in ~/.src/opencode/skills/
And project skill "custom" in .src/opencode/skills/
When I load both directories
Then project skill should take precedence
```

### Scenario: Handle invalid skill file gracefully
```gherkin
Given a skill file with invalid YAML
When I call loader.load_from_file(path)
Then it should raise SkillParseError
And error should contain file path
And error should contain parse error details
```

---

## Feature: Skill Registry

### Scenario: Get singleton instance
```gherkin
When I call SkillRegistry.get_instance() twice
Then I should get the same instance both times
```

### Scenario: Register a skill
```gherkin
Given a SkillRegistry
And a Skill with name "pdf"
When I call registry.register(skill)
Then registry.get("pdf") should return the skill
```

### Scenario: Register skill with aliases
```gherkin
Given a skill with aliases=["xlsx", "csv"]
When I register the skill
Then registry.get("xlsx") should return the skill
And registry.get("csv") should return the skill
```

### Scenario: Prevent duplicate registration
```gherkin
Given a registry with skill "pdf" registered
When I try to register another skill named "pdf"
Then it should raise ValueError
And error should mention "already registered"
```

### Scenario: Unregister skill
```gherkin
Given a registry with skill "custom" registered
When I call registry.unregister("custom")
Then it should return True
And registry.get("custom") should return None
```

### Scenario: Unregister nonexistent skill
```gherkin
Given a registry without skill "unknown"
When I call registry.unregister("unknown")
Then it should return False
```

### Scenario: List all skills
```gherkin
Given a registry with 5 skills registered
When I call registry.list_skills()
Then result should have 5 skills
```

### Scenario: List skills by tag
```gherkin
Given skills with various tags
And 2 skills have tag "data"
When I call registry.list_skills(tag="data")
Then result should have 2 skills
```

### Scenario: Search skills by name
```gherkin
Given skills: "pdf", "excel", "database"
When I call registry.search("data")
Then result should contain "database"
```

### Scenario: Search skills by description
```gherkin
Given skill with description "Work with spreadsheets"
When I call registry.search("spreadsheet")
Then result should contain that skill
```

---

## Feature: Skill Activation

### Scenario: Activate skill
```gherkin
Given a registered skill "pdf"
When I call registry.activate("pdf")
Then skill.is_active should be True
And registry.active_skill should be the pdf skill
```

### Scenario: Activate skill with config
```gherkin
Given a skill with config option "output_format"
When I call registry.activate("pdf", {"output_format": "json"})
Then skill._context["output_format"] should be "json"
```

### Scenario: Activation deactivates previous skill
```gherkin
Given active skill "pdf"
When I call registry.activate("excel")
Then pdf skill.is_active should be False
And excel skill.is_active should be True
```

### Scenario: Deactivate current skill
```gherkin
Given active skill "pdf"
When I call registry.deactivate()
Then registry.active_skill should be None
And pdf skill.is_active should be False
```

### Scenario: Activate unknown skill
```gherkin
Given a registry without skill "unknown"
When I call registry.activate("unknown")
Then it should raise KeyError
```

### Scenario: Get prompt from active skill
```gherkin
Given active skill with prompt "You are a PDF expert"
When I call skill.get_prompt()
Then result should contain "You are a PDF expert"
```

### Scenario: Variable substitution in prompt
```gherkin
Given skill prompt "Analyze {{ file_path }}"
And skill activated with {"file_path": "doc.pdf"}
When I call skill.get_prompt()
Then result should be "Analyze doc.pdf"
```

### Scenario: Get tools from active skill
```gherkin
Given skill with tools=["read", "bash"]
When I call skill.get_tools()
Then result should be ["read", "bash"]
```

---

## Feature: Built-in Skills

### Scenario: PDF skill available
```gherkin
Given a new SkillRegistry
When I check built-in skills
Then registry.get("pdf") should exist
And skill.description should mention "PDF"
```

### Scenario: Excel skill available
```gherkin
Given a new SkillRegistry
When I check built-in skills
Then registry.get("excel") should exist
And skill.metadata.tags should contain "data"
```

### Scenario: Database skill available
```gherkin
Given a new SkillRegistry
When I check built-in skills
Then registry.get("database") should exist
And skill.tools should contain "bash"
```

### Scenario: API skill available
```gherkin
Given a new SkillRegistry
Then registry.get("api") should exist
```

### Scenario: Testing skill available
```gherkin
Given a new SkillRegistry
Then registry.get("testing") should exist
And skill.tools should contain "bash"
```

---

## Feature: Skill Commands

### Scenario: List available skills
```gherkin
Given 5 registered skills
When user runs "/skill list"
Then output should show all 5 skills
And each skill should show name and description
```

### Scenario: Activate skill via command
```gherkin
Given registered skill "pdf"
When user runs "/skill pdf"
Then PDF skill should be activated
And confirmation message should be shown
```

### Scenario: Deactivate skill via command
```gherkin
Given active skill "pdf"
When user runs "/skill off"
Then skill should be deactivated
And confirmation message should be shown
```

### Scenario: Show skill info
```gherkin
Given registered skill "pdf"
When user runs "/skill info pdf"
Then output should show skill details
And should include name, description, author
And should include version and tags
And should include tools and config options
```

### Scenario: Search for skills
```gherkin
Given skills with various tags
When user runs "/skill search data"
Then output should show matching skills
```

### Scenario: Show active skill
```gherkin
Given active skill "pdf"
When user runs "/skill"
Then output should show "Active skill: pdf"
```

### Scenario: No active skill
```gherkin
Given no active skill
When user runs "/skill"
Then output should show "No skill active"
And should suggest "/skill list"
```

---

## Feature: Custom Skills

### Scenario: Create custom skill file
```gherkin
Given user creates ~/.src/opencode/skills/my-skill.yaml
With valid skill YAML content
When SkillLoader discovers skills
Then "my-skill" should be available
```

### Scenario: Hot reload custom skill
```gherkin
Given registered custom skill "my-skill"
When user modifies the skill file
And calls registry.reload()
Then skill should reflect new content
```

### Scenario: Skill validation on load
```gherkin
Given a skill file with missing required field
When loader tries to load the file
Then it should report validation error
And should not crash the application
```

---

## Feature: Skill Integration

### Scenario: Skill prompt added to system
```gherkin
Given active skill "pdf"
When REPL builds system prompt
Then system prompt should include skill prompt
```

### Scenario: Skill tools filter available tools
```gherkin
Given active skill with tools=["read", "glob"]
When REPL prepares tool list
Then only "read" and "glob" should be available
```

### Scenario: No skill means all tools available
```gherkin
Given no active skill
When REPL prepares tool list
Then all tools should be available
```

### Scenario: Skill persisted in session
```gherkin
Given active skill "pdf"
When session is saved
Then session data should include active_skill="pdf"
```

### Scenario: Skill restored from session
```gherkin
Given session with active_skill="pdf"
When session is resumed
Then registry.active_skill should be pdf skill
```

---

## Feature: Skill Error Handling

### Scenario: Invalid skill file syntax
```gherkin
Given a skill file with invalid YAML
When loader attempts to load it
Then it should log error with file path
And should continue loading other skills
```

### Scenario: Skill activation with missing tool
```gherkin
Given skill requires tool "special_tool"
And "special_tool" is not registered
When skill is activated
Then warning should be logged
And skill should still activate
```

### Scenario: Skill prompt template error
```gherkin
Given skill with invalid template "{{ invalid }"
When skill.get_prompt() is called
Then it should return prompt with error marker
Or raise descriptive error
```

---

## Feature: Skill Metadata

### Scenario: Version comparison
```gherkin
Given skill with version="1.0.0"
When checking version
Then it should be parseable as semantic version
```

### Scenario: Tags for categorization
```gherkin
Given skill with tags=["data", "analysis", "csv"]
When listing skills by tag "data"
Then this skill should be included
```

### Scenario: Examples in metadata
```gherkin
Given skill with examples=["Analyze this PDF", "Extract tables"]
When showing skill info
Then examples should be displayed
```

### Scenario: Author attribution
```gherkin
Given skill with author="Jane Doe"
When showing skill info
Then author should be displayed
```

---

## Feature: Skill Configuration

### Scenario: String configuration option
```gherkin
Given skill config with type="string" and default="value"
When skill is activated without config
Then option should use default "value"
```

### Scenario: Choice configuration option
```gherkin
Given skill config with type="choice" and choices=["a", "b", "c"]
When skill is activated with {"option": "b"}
Then option value should be "b"
```

### Scenario: Invalid choice value
```gherkin
Given skill config with choices=["a", "b", "c"]
When skill is activated with {"option": "invalid"}
Then it should raise ValueError
Or use default value with warning
```

### Scenario: Boolean configuration option
```gherkin
Given skill config with type="bool" and default=False
When skill is activated with {"option": True}
Then option value should be True
```

---

## Feature: Skill Discovery

### Scenario: Discover user skills
```gherkin
Given ~/.src/opencode/skills/ contains 2 skill files
When loader.discover_skills() is called
Then both skills should be discovered
```

### Scenario: Discover project skills
```gherkin
Given .src/opencode/skills/ contains 1 skill file
When loader.discover_skills() is called
Then project skill should be discovered
```

### Scenario: Skip non-skill files
```gherkin
Given skills directory contains "readme.txt"
When loader.discover_skills() is called
Then readme.txt should be ignored
And only .yaml and .md files should be loaded
```

### Scenario: Handle empty skills directory
```gherkin
Given empty ~/.src/opencode/skills/ directory
When loader.discover_skills() is called
Then result should be empty list
And no error should occur
```

### Scenario: Handle missing skills directory
```gherkin
Given ~/.src/opencode/skills/ does not exist
When loader.discover_skills() is called
Then result should be empty list
And no error should occur
```
