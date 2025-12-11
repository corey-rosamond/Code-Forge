"""
Built-in skills bundled with Code-Forge.
"""

from ..base import Skill, SkillConfig, SkillDefinition, SkillMetadata
from ..registry import SkillRegistry


def create_builtin_skill(
    name: str,
    description: str,
    prompt: str,
    tools: list[str] | None = None,
    tags: list[str] | None = None,
    aliases: list[str] | None = None,
    config: list[SkillConfig] | None = None,
    examples: list[str] | None = None,
) -> Skill:
    """Create a built-in skill.

    Args:
        name: Skill name
        description: Skill description
        prompt: System prompt addition
        tools: Required tools
        tags: Categorization tags
        aliases: Alternative names
        config: Configuration options
        examples: Usage examples

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
            aliases=aliases or [],
            examples=examples or [],
        ),
        prompt=prompt,
        tools=tools or [],
        config=config or [],
        is_builtin=True,
    )
    return Skill(definition)


# PDF Skill
PDF_SKILL = create_builtin_skill(
    name="pdf",
    description="Analyze and extract information from PDF documents",
    tags=["documents", "analysis"],
    tools=["read", "bash"],
    examples=[
        "Analyze this PDF and summarize key points",
        "Extract all tables from the document",
        "Find specific information in the PDF",
    ],
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
    aliases=["xlsx", "csv"],
    tools=["read", "write", "bash"],
    examples=[
        "Analyze this spreadsheet data",
        "Calculate statistics for the dataset",
        "Find trends in the data",
    ],
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
    aliases=["db"],
    tools=["read", "bash"],
    examples=[
        "Analyze the database schema",
        "Write a query to find specific data",
        "Optimize this SQL query",
    ],
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
    examples=[
        "Test this API endpoint",
        "Generate documentation for the API",
        "Debug this API request",
    ],
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
    aliases=["test"],
    tools=["read", "write", "bash", "glob", "grep"],
    examples=[
        "Write unit tests for this function",
        "Run the test suite",
        "Debug this failing test",
    ],
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


def get_builtin_skills() -> list[Skill]:
    """Get list of built-in skills.

    Returns:
        List of built-in Skill instances
    """
    return list(BUILTIN_SKILLS)


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
    "API_SKILL",
    "BUILTIN_SKILLS",
    "DATABASE_SKILL",
    "EXCEL_SKILL",
    "PDF_SKILL",
    "TESTING_SKILL",
    "create_builtin_skill",
    "get_builtin_skills",
    "register_builtin_skills",
]
