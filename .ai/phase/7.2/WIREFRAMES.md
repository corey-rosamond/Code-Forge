# Phase 7.2: Skills System - Wireframes & Usage Examples

**Phase:** 7.2
**Name:** Skills System
**Dependencies:** Phase 6.1 (Slash Commands), Phase 2.1 (Tool System)

---

## 1. Skill Activation

### Activate Skill via Command

```
You: /skill pdf

Activated skill: pdf
Description: Analyze and extract information from PDF documents

The assistant is now specialized for PDF analysis.
Capabilities:
  - Extract text from PDFs
  - Analyze document structure
  - Summarize content
  - Find specific information

Type /skill off to deactivate.
```

### Activate with Configuration

```
You: /skill excel --format json

Activated skill: excel
Configuration:
  output_format: json

The assistant is now specialized for spreadsheet analysis.
```

### Deactivate Skill

```
You: /skill off

Deactivated skill: excel
Returning to general assistant mode.
```

---

## 2. Skill Listing

### List All Available Skills

```
You: /skill list

Available Skills (8):

Built-in:
  pdf         Analyze and extract information from PDF documents
  excel       Work with Excel and CSV spreadsheet files
  database    Query and analyze databases
  api         Test API endpoints and generate documentation
  testing     Write and run tests with coverage analysis

User Skills:
  my-react    React component development assistance
  aws-deploy  AWS deployment and infrastructure

Project Skills:
  project-db  Project-specific database schema helpers
```

### List Skills by Tag

```
You: /skill list --tag data

Skills tagged "data" (3):

  excel       Work with Excel and CSV spreadsheet files
  database    Query and analyze databases
  project-db  Project-specific database schema helpers
```

---

## 3. Skill Information

### Show Skill Details

```
You: /skill info pdf

╭─ Skill: pdf ─────────────────────────────────────────╮
│                                                       │
│  Description: Analyze and extract information from    │
│               PDF documents                           │
│                                                       │
│  Author:      Code-Forge Team                          │
│  Version:     1.0.0                                  │
│  Tags:        documents, analysis, extraction        │
│                                                       │
│  Tools Required:                                      │
│    • read    - Read file contents                    │
│    • bash    - Execute shell commands                │
│                                                       │
│  Configuration Options:                               │
│    (none)                                            │
│                                                       │
│  Usage Examples:                                      │
│    "Summarize this PDF document"                     │
│    "Extract all tables from the PDF"                 │
│    "Find mentions of 'revenue' in doc.pdf"          │
│                                                       │
╰──────────────────────────────────────────────────────╯
```

### Show Skill with Config Options

```
You: /skill info excel

╭─ Skill: excel ───────────────────────────────────────╮
│                                                       │
│  Description: Work with Excel and CSV spreadsheet     │
│               files                                   │
│                                                       │
│  Author:      Code-Forge Team                          │
│  Version:     1.0.0                                  │
│  Tags:        data, spreadsheets, csv, xlsx          │
│  Aliases:     xlsx, csv                              │
│                                                       │
│  Tools Required:                                      │
│    • read    - Read file contents                    │
│    • write   - Write file contents                   │
│    • bash    - Execute shell commands                │
│                                                       │
│  Configuration Options:                               │
│    output_format                                      │
│      Type: choice                                    │
│      Options: text, json, markdown                   │
│      Default: text                                   │
│      Description: Format for data output             │
│                                                       │
╰──────────────────────────────────────────────────────╯
```

---

## 4. Skill Search

### Search by Keyword

```
You: /skill search data

Search Results for "data" (4):

  excel      Work with Excel and CSV spreadsheet files
             Tags: data, spreadsheets

  database   Query and analyze databases
             Tags: data, sql

  csv        (alias for excel)

  project-db Project-specific database helpers
             Tags: data, postgresql
```

### No Results Found

```
You: /skill search blockchain

No skills found matching "blockchain".

Try:
  /skill list           - See all available skills
  /skill list --tag     - List by tag
```

---

## 5. Skill in Action

### PDF Skill Session

```
You: /skill pdf

Activated skill: pdf

You: Summarize the key points from report.pdf

[Skill: pdf active]

Reading report.pdf...

## Summary: Q4 Financial Report

### Key Points:

1. **Revenue Growth**: 15% increase YoY, reaching $45M
2. **Operating Costs**: Reduced by 8% through automation
3. **New Markets**: Expanded to 3 new regions
4. **Challenges**: Supply chain delays impacted Q4

### Financial Highlights:
- Gross Margin: 42% (up from 38%)
- Net Income: $8.2M
- Cash Position: $25M

### Outlook:
Management projects 20% growth for next fiscal year.

---
Source: report.pdf (32 pages analyzed)
```

### Excel Skill Session

```
You: /skill excel

Activated skill: excel

You: Analyze the sales data in sales_2024.xlsx

[Skill: excel active]

Reading sales_2024.xlsx...

## Sales Analysis: 2024

### Dataset Overview
- Rows: 1,247 transactions
- Columns: Date, Product, Region, Amount, Quantity
- Date Range: Jan 1, 2024 - Dec 31, 2024

### Key Statistics

| Metric          | Value      |
|-----------------|------------|
| Total Revenue   | $2,345,678 |
| Average Order   | $1,881     |
| Total Units     | 15,892     |
| Unique Products | 45         |

### Top Products by Revenue
1. Enterprise License - $456,789 (19.5%)
2. Professional Plan - $345,678 (14.7%)
3. Basic Subscription - $234,567 (10.0%)

### Regional Performance
- North America: 45% of revenue
- Europe: 30% of revenue
- Asia Pacific: 25% of revenue

### Trends
- Q4 showed 25% increase over Q3
- December was highest revenue month
```

### Database Skill Session

```
You: /skill database

Activated skill: database

You: Analyze the schema and suggest optimizations

[Skill: database active]

Analyzing database schema...

## Schema Analysis

### Tables Found (12)
- users (45,230 rows)
- orders (128,456 rows)
- products (1,234 rows)
- order_items (456,789 rows)
- categories (45 rows)
- ...

### Optimization Recommendations

#### 1. Missing Indexes (High Impact)
```sql
-- orders table: frequently queried by user_id
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- order_items: join optimization
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
```

#### 2. Query Patterns Detected
- Heavy joins between orders and order_items
- Frequent date range queries on orders.created_at

#### 3. Suggested Improvements
- Add composite index on (user_id, created_at) for orders
- Consider partitioning orders table by date
- Review N+1 query patterns in application code

Would you like me to generate the migration scripts?
```

---

## 6. Custom Skill Creation

### User Skill File Example

```yaml
# ~/.src/forge/skills/react-expert.yaml
name: react-expert
description: Expert React and TypeScript development assistance
author: Your Name
version: 1.0.0
tags:
  - react
  - typescript
  - frontend
aliases:
  - react
  - tsx

tools:
  - read
  - write
  - edit
  - glob
  - grep
  - bash

config:
  typescript:
    type: bool
    default: true
    description: Use TypeScript by default

  styling:
    type: choice
    choices:
      - css-modules
      - tailwind
      - styled-components
    default: tailwind
    description: Preferred styling approach

prompt: |
  You are an expert React developer specializing in modern React patterns
  and TypeScript.

  When writing React code:
  1. Use functional components with hooks
  2. Prefer TypeScript for type safety
  3. Follow React best practices
  4. Use {{ styling }} for styling
  5. Write accessible components (ARIA)

  When reviewing React code:
  1. Check for common anti-patterns
  2. Verify proper hook usage
  3. Look for performance issues
  4. Ensure proper error boundaries

  Always explain your reasoning and suggest improvements.
```

### Project Skill File Example

```markdown
---
name: project-api
description: Project-specific API development helpers
author: Team
version: 1.0.0
tags:
  - api
  - backend
tools:
  - read
  - write
  - bash
  - grep
---

# Project API Skill

You are assisting with the MyProject API development.

## Project Context

- Framework: FastAPI
- Database: PostgreSQL with SQLAlchemy
- Auth: JWT tokens
- API Style: RESTful with OpenAPI docs

## Conventions

When creating new endpoints:

1. Place route handlers in `src/routes/`
2. Use Pydantic models from `src/models/`
3. Follow naming convention: `{resource}_{action}`
4. Always include proper error handling
5. Add OpenAPI documentation strings

## Example Endpoint

```python
@router.post("/items", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ItemResponse:
    """Create a new item."""
    return await item_service.create(db, item, current_user)
```
```

---

## 7. Skill Status Display

### Show Active Skill

```
You: /skill

Active Skill: pdf
Description: Analyze and extract information from PDF documents

Tools enabled: read, bash

To deactivate: /skill off
To switch: /skill <name>
```

### No Active Skill

```
You: /skill

No skill currently active.

Use /skill <name> to activate a skill.
Use /skill list to see available skills.

Popular skills:
  pdf       - PDF document analysis
  excel     - Spreadsheet data analysis
  database  - Database queries and optimization
```

---

## 8. Skill Error Handling

### Unknown Skill

```
You: /skill unknown

Error: Skill "unknown" not found.

Did you mean one of these?
  - unix (user skill)

Use /skill list to see all available skills.
```

### Skill Load Error

```
Startup: Loading skills...

Warning: Failed to load skill from ~/.src/forge/skills/broken.yaml
  Error: Invalid YAML syntax at line 15
  Skipping this skill.

Loaded 7 skills successfully.
```

### Missing Tool Warning

```
You: /skill custom-skill

Warning: Skill "custom-skill" requires tool "special_tool" which is not available.
Some functionality may be limited.

Activated skill: custom-skill
```

---

## 9. REPL Integration

### Skill Indicator in Prompt

```
forge> /skill pdf
Activated skill: pdf

forge [pdf]> Analyze the document structure

[Reading document...]

The document has the following structure:
...

forge [pdf]> /skill off
Deactivated skill: pdf

forge>
```

### Skill Context in Messages

```
forge [excel]> What formulas would help analyze this data?

[Context: Excel skill active - specialized spreadsheet assistance]

For your sales data analysis, I recommend these formulas:

1. **SUMIFS** - Conditional sum by criteria
   =SUMIFS(Amount, Region, "North", Year, 2024)

2. **AVERAGEIF** - Average with condition
   =AVERAGEIF(Category, "Electronics", Revenue)

3. **VLOOKUP/XLOOKUP** - Cross-reference data
   =XLOOKUP(ProductID, Products[ID], Products[Name])

Would you like me to help implement any of these?
```

---

## 10. Skill Reload

### Hot Reload Skills

```
You: /skill reload

Reloading skills...

Reloaded:
  ✓ pdf (built-in)
  ✓ excel (built-in)
  ✓ database (built-in)
  ✓ api (built-in)
  ✓ testing (built-in)
  ✓ react-expert (user)
  ✓ project-api (project)

7 skills loaded successfully.
```

### Reload with Errors

```
You: /skill reload

Reloading skills...

  ✓ pdf (built-in)
  ✓ excel (built-in)
  ✗ my-broken-skill (user)
    Error: Missing required field 'prompt'
  ✓ project-api (project)

6 of 7 skills loaded.
1 skill failed to load - check the file for errors.
```

---

## 11. Skill Help

### General Skill Help

```
You: /help skill

Skill System Commands:

  /skill              Show active skill or list available
  /skill <name>       Activate a skill
  /skill off          Deactivate current skill
  /skill list         List all available skills
  /skill list --tag   List skills by tag
  /skill info <name>  Show skill details
  /skill search       Search for skills
  /skill reload       Reload all skills

Creating Custom Skills:

  User skills:    ~/.src/forge/skills/*.yaml or *.md
  Project skills: .src/forge/skills/*.yaml or *.md

  See documentation for skill file format.
```

---

## 12. Automatic Skill Suggestion

### Context-Based Suggestion

```
You: Can you help me analyze this Excel file: sales.xlsx

I notice you're working with an Excel file. Would you like to
activate the Excel skill for specialized spreadsheet assistance?

  [Yes, activate Excel skill]  [No, continue without skill]
```

### File Extension Detection

```
You: Read and summarize report.pdf

I see you're working with a PDF file. The PDF skill provides
specialized capabilities for document analysis.

Activating PDF skill...

[Skill: pdf active]

Reading report.pdf...
```

---

## Notes

- Skills provide specialized context and capabilities
- Only one skill can be active at a time
- Skills modify system prompts transparently
- Tool filtering happens automatically
- Custom skills support YAML and Markdown formats
- Skills persist across session saves
- Hot reload allows development iteration
