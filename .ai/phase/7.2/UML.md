# Phase 7.2: Skills System - UML Diagrams

**Phase:** 7.2
**Name:** Skills System
**Dependencies:** Phase 6.1 (Slash Commands), Phase 2.1 (Tool System)

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SKILLS SYSTEM                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐
│     SkillConfig         │
├─────────────────────────┤
│ + name: str             │
│ + type: str             │
│ + default: Any          │
│ + description: str      │
│ + choices: list | None  │
├─────────────────────────┤
│ + validate(value): bool │
│ + to_dict(): dict       │
└─────────────────────────┘

┌─────────────────────────┐
│    SkillMetadata        │
├─────────────────────────┤
│ + name: str             │
│ + description: str      │
│ + author: str           │
│ + version: str          │
│ + tags: list[str]       │
│ + aliases: list[str]    │
│ + examples: list[str]   │
├─────────────────────────┤
│ + to_dict(): dict       │
│ + from_dict(): cls      │
└─────────────────────────┘

┌─────────────────────────────────────┐
│        SkillDefinition              │
├─────────────────────────────────────┤
│ + metadata: SkillMetadata           │
│ + prompt: str                       │
│ + tools: list[str]                  │
│ + config: list[SkillConfig]         │
│ + source_path: str | None           │
├─────────────────────────────────────┤
│ + to_dict(): dict                   │
│ + from_dict(data): cls              │
│ + validate(): list[str]             │
└─────────────────────────────────────┘
         │
         │ contains
         ▼
┌─────────────────────────────────────┐
│           Skill                     │
├─────────────────────────────────────┤
│ + definition: SkillDefinition       │
│ - _active: bool                     │
│ - _context: dict[str, Any]          │
├─────────────────────────────────────┤
│ + name: str <<property>>            │
│ + description: str <<property>>     │
│ + is_active: bool <<property>>      │
│ + activate(config): None            │
│ + deactivate(): None                │
│ + get_prompt(): str                 │
│ + get_tools(): list[str]            │
│ + to_dict(): dict                   │
└─────────────────────────────────────┘
         △
         │ extends
         │
    ┌────┴────┬──────────┬──────────┬──────────┐
    │         │          │          │          │
┌───┴───┐ ┌───┴───┐ ┌────┴────┐ ┌───┴───┐ ┌───┴───┐
│PDFSkill│ │ExcelSk│ │DatabaseS│ │APISkil│ │TestSk │
└───────┘ └───────┘ └─────────┘ └───────┘ └───────┘


┌─────────────────────────────────────┐
│         SkillParser                 │
├─────────────────────────────────────┤
│ (no instance state)                 │
├─────────────────────────────────────┤
│ + parse_yaml(content): Definition   │
│ + parse_markdown(content): Def      │
│ + parse(content, ext): Definition   │
│ + validate(definition): list[str]   │
│ - _parse_frontmatter(): dict        │
│ - _extract_config(): list[Config]   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         SkillLoader                 │
├─────────────────────────────────────┤
│ + search_paths: list[Path]          │
│ - _parser: SkillParser              │
├─────────────────────────────────────┤
│ + load_from_file(path): Definition  │
│ + load_from_directory(dir): list    │
│ + discover_skills(): list[Def]      │
│ + reload_skill(path): Definition    │
│ - _get_skill_files(dir): list[Path] │
└─────────────────────────────────────┘
         │
         │ uses
         ▼
┌─────────────────────────────────────┐
│    SkillRegistry <<singleton>>      │
├─────────────────────────────────────┤
│ - _instance: SkillRegistry | None   │
│ - _skills: dict[str, Skill]         │
│ - _aliases: dict[str, str]          │
│ - _active_skill: Skill | None       │
│ - _loader: SkillLoader              │
├─────────────────────────────────────┤
│ + get_instance(): SkillRegistry     │
│ + reset_instance(): None            │
│ + register(skill): None             │
│ + unregister(name): bool            │
│ + get(name): Skill | None           │
│ + list_skills(tag): list[Skill]     │
│ + search(query): list[Skill]        │
│ + activate(name, config): Skill     │
│ + deactivate(): None                │
│ + active_skill: Skill <<property>>  │
│ + reload(): None                    │
└─────────────────────────────────────┘


┌─────────────────────────────────────┐
│       SkillCommand                  │
├─────────────────────────────────────┤
│ + name = "skill"                    │
│ + aliases = ["sk"]                  │
│ - _registry: SkillRegistry          │
├─────────────────────────────────────┤
│ + execute(args, ctx): Result        │
│ - _handle_list(): str               │
│ - _handle_activate(name): str       │
│ - _handle_deactivate(): str         │
│ - _handle_info(name): str           │
│ - _handle_search(query): str        │
└─────────────────────────────────────┘
```

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SKILLS SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐    │
│  │   Built-in       │     │   User Skills    │     │  Project Skills  │    │
│  │   Skills         │     │                  │     │                  │    │
│  │                  │     │  ~/.src/forge/    │     │  .src/forge/      │    │
│  │  - PDF           │     │  skills/*.yaml   │     │  skills/*.yaml   │    │
│  │  - Excel         │     │  skills/*.md     │     │  skills/*.md     │    │
│  │  - Database      │     │                  │     │                  │    │
│  │  - API           │     │                  │     │                  │    │
│  │  - Testing       │     │                  │     │                  │    │
│  └────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘    │
│           │                        │                        │               │
│           └────────────────────────┼────────────────────────┘               │
│                                    │                                        │
│                                    ▼                                        │
│                         ┌──────────────────┐                                │
│                         │   SkillLoader    │                                │
│                         │                  │                                │
│                         │  Discovers and   │                                │
│                         │  loads skills    │                                │
│                         └────────┬─────────┘                                │
│                                  │                                          │
│                                  ▼                                          │
│                         ┌──────────────────┐                                │
│                         │   SkillParser    │                                │
│                         │                  │                                │
│                         │  Parses YAML     │                                │
│                         │  and Markdown    │                                │
│                         └────────┬─────────┘                                │
│                                  │                                          │
│                                  ▼                                          │
│                         ┌──────────────────┐                                │
│                         │  SkillRegistry   │                                │
│                         │                  │                                │
│                         │  Singleton       │                                │
│                         │  manages all     │                                │
│                         │  skills          │                                │
│                         └────────┬─────────┘                                │
│                                  │                                          │
│           ┌──────────────────────┼──────────────────────┐                   │
│           │                      │                      │                   │
│           ▼                      ▼                      ▼                   │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐            │
│  │ Skill Command  │    │ Tool System    │    │ Session Mgmt   │            │
│  │ /skill <name>  │    │ Tool Filtering │    │ Skill Persist  │            │
│  └────────────────┘    └────────────────┘    └────────────────┘            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sequence Diagram: Skill Activation

```
┌──────┐    ┌─────────────┐    ┌──────────────┐    ┌───────┐    ┌─────────┐
│ User │    │ SkillCommand│    │SkillRegistry │    │ Skill │    │ Session │
└──┬───┘    └──────┬──────┘    └──────┬───────┘    └───┬───┘    └────┬────┘
   │               │                  │                │             │
   │ /skill pdf    │                  │                │             │
   │──────────────>│                  │                │             │
   │               │                  │                │             │
   │               │ get("pdf")       │                │             │
   │               │─────────────────>│                │             │
   │               │                  │                │             │
   │               │                  │ lookup in      │             │
   │               │                  │ _skills        │             │
   │               │                  │────────┐       │             │
   │               │                  │        │       │             │
   │               │                  │<───────┘       │             │
   │               │                  │                │             │
   │               │      skill       │                │             │
   │               │<─────────────────│                │             │
   │               │                  │                │             │
   │               │ activate("pdf")  │                │             │
   │               │─────────────────>│                │             │
   │               │                  │                │             │
   │               │                  │ deactivate()   │             │
   │               │                  │ (if active)    │             │
   │               │                  │───────────────>│             │
   │               │                  │                │             │
   │               │                  │ activate()     │             │
   │               │                  │───────────────>│             │
   │               │                  │                │             │
   │               │                  │ _active=True   │             │
   │               │                  │                │────────┐    │
   │               │                  │                │        │    │
   │               │                  │                │<───────┘    │
   │               │                  │                │             │
   │               │                  │ save_active()  │             │
   │               │                  │────────────────────────────>│
   │               │                  │                │             │
   │               │  active skill    │                │             │
   │               │<─────────────────│                │             │
   │               │                  │                │             │
   │ "PDF skill    │                  │                │             │
   │  activated"   │                  │                │             │
   │<──────────────│                  │                │             │
   │               │                  │                │             │
```

---

## Sequence Diagram: Skill Loading

```
┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│ Startup │    │ SkillLoader │    │ SkillParser │    │SkillRegistry │
└────┬────┘    └──────┬──────┘    └──────┬──────┘    └──────┬───────┘
     │                │                  │                  │
     │ initialize()   │                  │                  │
     │───────────────>│                  │                  │
     │                │                  │                  │
     │                │ load built-in    │                  │
     │                │─────────┐        │                  │
     │                │         │        │                  │
     │                │<────────┘        │                  │
     │                │                  │                  │
     │                │                  │  register()      │
     │                │──────────────────────────────────>│
     │                │                  │                  │
     │                │ discover_skills()│                  │
     │                │─────────┐        │                  │
     │                │ scan dirs│        │                  │
     │                │<────────┘        │                  │
     │                │                  │                  │
     │                │ load_from_file() │                  │
     │                │─────────┐        │                  │
     │                │         │        │                  │
     │                │<────────┘        │                  │
     │                │                  │                  │
     │                │ parse(content)   │                  │
     │                │─────────────────>│                  │
     │                │                  │                  │
     │                │                  │ parse_yaml()     │
     │                │                  │─────────┐        │
     │                │                  │         │        │
     │                │                  │<────────┘        │
     │                │                  │                  │
     │                │  SkillDefinition │                  │
     │                │<─────────────────│                  │
     │                │                  │                  │
     │                │ validate()       │                  │
     │                │─────────────────>│                  │
     │                │                  │                  │
     │                │    errors[]      │                  │
     │                │<─────────────────│                  │
     │                │                  │                  │
     │                │                  │  register()      │
     │                │──────────────────────────────────>│
     │                │                  │                  │
     │   ready        │                  │                  │
     │<───────────────│                  │                  │
     │                │                  │                  │
```

---

## Sequence Diagram: Skill Prompt Integration

```
┌──────┐    ┌──────┐    ┌──────────────┐    ┌───────┐    ┌─────┐
│ User │    │ REPL │    │SkillRegistry │    │ Skill │    │ LLM │
└──┬───┘    └──┬───┘    └──────┬───────┘    └───┬───┘    └──┬──┘
   │           │               │                │           │
   │  message  │               │                │           │
   │──────────>│               │                │           │
   │           │               │                │           │
   │           │ active_skill  │                │           │
   │           │──────────────>│                │           │
   │           │               │                │           │
   │           │    skill      │                │           │
   │           │<──────────────│                │           │
   │           │               │                │           │
   │           │               │  get_prompt()  │           │
   │           │               │───────────────>│           │
   │           │               │                │           │
   │           │               │ substitute     │           │
   │           │               │ variables      │           │
   │           │               │                │───┐       │
   │           │               │                │   │       │
   │           │               │                │<──┘       │
   │           │               │                │           │
   │           │               │   prompt       │           │
   │           │               │<───────────────│           │
   │           │               │                │           │
   │           │  skill_prompt │                │           │
   │           │<──────────────│                │           │
   │           │               │                │           │
   │           │ build system prompt            │           │
   │           │ (base + skill)                 │           │
   │           │─────────┐                      │           │
   │           │         │                      │           │
   │           │<────────┘                      │           │
   │           │               │                │           │
   │           │ get_tools()   │                │           │
   │           │──────────────>│───────────────>│           │
   │           │               │                │           │
   │           │               │   tools[]      │           │
   │           │<──────────────│<───────────────│           │
   │           │               │                │           │
   │           │        call LLM with           │           │
   │           │        skill context           │           │
   │           │───────────────────────────────────────────>│
   │           │               │                │           │
   │           │               │                │  response │
   │           │<───────────────────────────────────────────│
   │           │               │                │           │
   │ response  │               │                │           │
   │<──────────│               │                │           │
   │           │               │                │           │
```

---

## State Diagram: Skill Lifecycle

```
                    ┌─────────────────┐
                    │                 │
                    │    LOADED       │
                    │  (registered)   │
                    │                 │
                    └────────┬────────┘
                             │
                             │ activate()
                             ▼
                    ┌─────────────────┐
          ┌─────────│                 │─────────┐
          │         │     ACTIVE      │         │
          │         │                 │         │
          │         └────────┬────────┘         │
          │                  │                  │
          │ deactivate()     │ switch to        │ reload()
          │                  │ another          │
          ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│                 │  │                 │  │                 │
│    INACTIVE     │  │   SWITCHING     │  │   RELOADING     │
│                 │  │                 │  │                 │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         │ activate()         │ complete           │ complete
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │                 │
                    │     ACTIVE      │
                    │   (new skill)   │
                    │                 │
                    └─────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SKILL DATA FLOW                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Skill File  │     │  Skill File  │     │  Skill File  │
│  (.yaml)     │     │  (.md)       │     │  (builtin)   │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       │ read               │ read               │ import
       ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│                     SkillParser                         │
│                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │ YAML Parser │    │ Frontmatter │    │  Validator  │ │
│  │             │    │   Parser    │    │             │ │
│  └─────────────┘    └─────────────┘    └─────────────┘ │
└─────────────────────────────┬───────────────────────────┘
                              │
                              │ SkillDefinition
                              ▼
┌─────────────────────────────────────────────────────────┐
│                     SkillLoader                         │
│                                                         │
│  - Discovers files from search paths                    │
│  - Creates Skill instances from definitions             │
│  - Handles hot reload                                   │
└─────────────────────────────┬───────────────────────────┘
                              │
                              │ Skill[]
                              ▼
┌─────────────────────────────────────────────────────────┐
│                    SkillRegistry                        │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  _skills: dict[str, Skill]                       │  │
│  │                                                  │  │
│  │  "pdf"      -> PDFSkill                          │  │
│  │  "excel"    -> ExcelSkill                        │  │
│  │  "database" -> DatabaseSkill                     │  │
│  │  "custom"   -> CustomSkill                       │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  _aliases: dict[str, str]                        │  │
│  │                                                  │  │
│  │  "xlsx" -> "excel"                               │  │
│  │  "csv"  -> "excel"                               │  │
│  │  "db"   -> "database"                            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  _active_skill: Skill | None                           │
└─────────────────────────────┬───────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  /skill cmd   │     │  REPL Loop    │     │   Session     │
│               │     │               │     │               │
│ activate/     │     │ get_prompt()  │     │ save/restore  │
│ deactivate    │     │ get_tools()   │     │ active skill  │
└───────────────┘     └───────────────┘     └───────────────┘
```

---

## Package Structure Diagram

```
src/forge/skills/
├── __init__.py
│   ├── Skill
│   ├── SkillConfig
│   ├── SkillMetadata
│   ├── SkillDefinition
│   ├── SkillParser
│   ├── SkillLoader
│   └── SkillRegistry
│
├── base.py
│   ├── SkillConfig          # Configuration option dataclass
│   ├── SkillMetadata        # Metadata dataclass
│   ├── SkillDefinition      # Complete definition dataclass
│   └── Skill                # Base skill class
│
├── parser.py
│   └── SkillParser          # YAML/Markdown parser
│
├── loader.py
│   └── SkillLoader          # File loader with discovery
│
├── registry.py
│   └── SkillRegistry        # Singleton registry
│
├── commands.py
│   └── SkillCommand         # /skill command handler
│
└── builtin/
    ├── __init__.py
    │   ├── PDF_SKILL
    │   ├── EXCEL_SKILL
    │   ├── DATABASE_SKILL
    │   ├── API_SKILL
    │   ├── TESTING_SKILL
    │   └── get_builtin_skills()
    │
    ├── pdf.py               # PDF skill definition
    ├── excel.py             # Excel/CSV skill definition
    ├── database.py          # Database skill definition
    ├── api.py               # API skill definition
    └── testing.py           # Testing skill definition
```

---

## Integration Points Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INTEGRATION POINTS                                    │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌────────────────────┐
                    │   Skills System    │
                    │   (Phase 7.2)      │
                    └─────────┬──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│Slash Commands │     │ Tool System   │     │   Session     │
│ (Phase 6.1)   │     │ (Phase 2.1)   │     │ (Phase 5.1)   │
├───────────────┤     ├───────────────┤     ├───────────────┤
│               │     │               │     │               │
│ /skill <name> │     │ Tool filter   │     │ Skill state   │
│ /skill list   │     │ per skill     │     │ persistence   │
│ /skill off    │     │               │     │               │
│ /skill info   │     │ Skills define │     │ Restore on    │
│ /skill search │     │ required      │     │ session       │
│               │     │ tools list    │     │ resume        │
└───────────────┘     └───────────────┘     └───────────────┘

                              │
                              │
                              ▼
                    ┌────────────────────┐
                    │   REPL / Agent     │
                    │                    │
                    │ - System prompt    │
                    │   augmented with   │
                    │   skill prompt     │
                    │                    │
                    │ - Tools filtered   │
                    │   to skill needs   │
                    └────────────────────┘
```

---

## Notes

- Skills are self-contained capability bundles
- Registry follows singleton pattern for global access
- Skills modify system prompts when activated
- Tool filtering enables skill-specific capabilities
- Session integration allows skill persistence
- Hot reload supports development workflow
