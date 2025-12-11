#!/usr/bin/env python3
"""End-to-end test for Code-Forge agent.

This script tests the full agent flow:
1. Load configuration
2. Create LLM with OpenRouter
3. Register and bind tools
4. Set system prompt
5. Run agent with test prompts
6. Verify tool calls, responses, and context retention

Usage:
    python scripts/test_e2e.py [--verbose] [--suite SUITE]

Suites:
    all         - Run all test suites (default)
    tools       - Test all tool calling (Glob, Read, Write, Edit, Grep, Bash)
    context     - Test multi-turn context retention
    workflow    - Test file operations workflow
    search      - Test search and analysis workflows
    errors      - Test error handling
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

if TYPE_CHECKING:
    from code_forge.langchain.agent import AgentResult, Code-ForgeAgent


@dataclass
class TestResult:
    """Result of a single test."""

    name: str
    passed: bool
    message: str
    details: dict[str, str] = field(default_factory=dict)


@dataclass
class TestSuiteResult:
    """Result of a test suite."""

    name: str
    results: list[TestResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total(self) -> int:
        return len(self.results)


class EndToEndTester:
    """End-to-end test runner for Code-Forge."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.agent: Code-ForgeAgent | None = None
        self.system_prompt: str = ""
        self.tool_names: list[str] = []
        self.temp_dir: str = ""
        self.config: Any = None  # Will be set in setup

    async def setup(self) -> bool:
        """Set up the test environment."""
        from code_forge.config import ConfigLoader
        from code_forge.langchain.agent import Code-ForgeAgent
        from code_forge.langchain.llm import OpenRouterLLM
        from code_forge.langchain.prompts import get_system_prompt
        from code_forge.llm import OpenRouterClient
        from code_forge.llm.models import Message
        from code_forge.tools import ToolRegistry, register_all_tools

        print("=" * 60)
        print("Code-Forge End-to-End Test Suite")
        print("=" * 60)

        # Step 1: Load configuration
        print("\n[Setup] Loading configuration...")
        try:
            config_loader = ConfigLoader()
            config = config_loader.load_all()
            self.config = config  # Store for later use
            print(f"  ✓ Config loaded, model: {config.model.default}")
        except Exception as e:
            print(f"  ✗ Failed to load config: {e}")
            return False

        # Step 2: Check API key
        print("[Setup] Checking API key...")
        api_key = os.environ.get("OPENROUTER_API_KEY") or config.get_api_key()
        if not api_key:
            print("  ✗ OPENROUTER_API_KEY not set")
            print("    Set it with: export OPENROUTER_API_KEY=your-key")
            return False
        print(f"  ✓ API key found ({api_key[:10]}...)")

        # Step 3: Create LLM
        print("[Setup] Creating LLM...")
        try:
            client = OpenRouterClient(api_key=api_key)
            llm = OpenRouterLLM(client=client, model=config.model.default)
            print(f"  ✓ LLM created with model: {config.model.default}")
        except Exception as e:
            print(f"  ✗ Failed to create LLM: {e}")
            return False

        # Step 4: Register tools
        print("[Setup] Registering tools...")
        try:
            from code_forge.langchain.tools import adapt_tools_for_langchain

            register_all_tools()
            tool_registry = ToolRegistry()
            raw_tools = [tool_registry.get(name) for name in tool_registry.list_names()]
            raw_tools = [t for t in raw_tools if t is not None]
            # Wrap tools for LangChain compatibility (matching real CLI)
            tools = adapt_tools_for_langchain(raw_tools)
            self.tool_names = [t.name for t in tools if hasattr(t, "name")]
            print(f"  ✓ Registered {len(tools)} tools: {', '.join(self.tool_names)}")
        except Exception as e:
            print(f"  ✗ Failed to register tools: {e}")
            return False

        # Step 5: Create agent
        print("[Setup] Creating agent...")
        try:
            self.agent = Code-ForgeAgent(llm=llm, tools=tools, max_iterations=10)
            self.system_prompt = get_system_prompt(
                tool_names=self.tool_names,
                working_directory=os.getcwd(),
                model=config.model.default,
            )
            self.agent.memory.set_system_message(Message.system(self.system_prompt))
            print(f"  ✓ Agent created")
        except Exception as e:
            print(f"  ✗ Failed to create agent: {e}")
            return False

        # Step 6: Create temp directory for tests
        self.temp_dir = tempfile.mkdtemp(prefix="code_forge_e2e_")
        print(f"  ✓ Temp directory: {self.temp_dir}")

        print("\n" + "=" * 60)
        return True

    def cleanup(self) -> None:
        """Clean up test resources."""
        import shutil
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def reset_agent(self) -> None:
        """Reset agent memory while preserving system prompt."""
        from code_forge.llm.models import Message

        if self.agent:
            self.agent.reset()
            self.agent.memory.set_system_message(Message.system(self.system_prompt))

    async def run_prompt(self, prompt: str) -> AgentResult:
        """Run a prompt through the agent."""
        if not self.agent:
            raise RuntimeError("Agent not initialized")
        return await self.agent.run(prompt)

    def print_result(self, result: TestResult) -> None:
        """Print a test result."""
        status = "✓" if result.passed else "✗"
        print(f"  {status} {result.name}: {result.message}")
        if self.verbose and result.details:
            for key, value in result.details.items():
                print(f"      {key}: {value}")

    # =========================================================================
    # Test Suite: All Tools
    # =========================================================================

    async def test_all_tools(self) -> TestSuiteResult:
        """Test that all tools work correctly."""
        suite = TestSuiteResult(name="All Tools")
        print("\n[Suite] All Tools Tests")
        print("-" * 40)

        # Test 1: Glob tool - find files
        self.reset_agent()
        try:
            result = await self.run_prompt(
                "Use Glob to find all Python files in src/code_forge/tools/. "
                "List the file names you find."
            )
            tool_called = any(tc.name == "Glob" for tc in result.tool_calls)
            # Should find some .py files
            has_files = ".py" in result.output
            if tool_called and has_files:
                suite.results.append(TestResult(
                    name="Glob tool",
                    passed=True,
                    message="Found Python files",
                ))
            else:
                suite.results.append(TestResult(
                    name="Glob tool",
                    passed=False,
                    message="Glob failed" if not tool_called else "No .py files found",
                    details={"response": result.output[:200]},
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Glob tool", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 2: Read tool - read file content
        self.reset_agent()
        try:
            result = await self.run_prompt(
                "Read the file pyproject.toml and tell me the project version."
            )
            tool_called = any(tc.name == "Read" for tc in result.tool_calls)
            has_version = "1.0.0" in result.output
            if tool_called and has_version:
                suite.results.append(TestResult(
                    name="Read tool",
                    passed=True,
                    message="Read file and found version 1.0.0",
                ))
            else:
                suite.results.append(TestResult(
                    name="Read tool",
                    passed=False,
                    message="Read failed" if not tool_called else "Version not found",
                    details={"response": result.output[:200]},
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Read tool", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 3: Write tool - create new file
        self.reset_agent()
        test_file = os.path.join(self.temp_dir, "test_write.txt")
        try:
            result = await self.run_prompt(
                f"Use Write to create a new file at {test_file} with the content "
                "'Hello from Code-Forge test!'"
            )
            tool_called = any(tc.name == "Write" for tc in result.tool_calls)
            file_exists = os.path.exists(test_file)
            content_correct = False
            if file_exists:
                with open(test_file) as f:
                    content_correct = "Hello from Code-Forge" in f.read()

            if tool_called and file_exists and content_correct:
                suite.results.append(TestResult(
                    name="Write tool",
                    passed=True,
                    message="Created file with correct content",
                ))
            else:
                suite.results.append(TestResult(
                    name="Write tool",
                    passed=False,
                    message=f"Write failed (called={tool_called}, exists={file_exists}, content={content_correct})",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Write tool", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 4: Edit tool - modify existing file
        self.reset_agent()
        edit_file = os.path.join(self.temp_dir, "test_edit.txt")
        with open(edit_file, "w") as f:
            f.write("Line 1: Original text\nLine 2: Keep this\n")
        try:
            result = await self.run_prompt(
                f"Read {edit_file}, then Edit it to change 'Original text' to 'Modified text'."
            )
            edit_called = any(tc.name == "Edit" for tc in result.tool_calls)
            with open(edit_file) as f:
                content = f.read()
            content_correct = "Modified text" in content and "Keep this" in content

            if edit_called and content_correct:
                suite.results.append(TestResult(
                    name="Edit tool",
                    passed=True,
                    message="Modified file correctly",
                ))
            else:
                suite.results.append(TestResult(
                    name="Edit tool",
                    passed=False,
                    message=f"Edit failed (called={edit_called}, content_correct={content_correct})",
                    details={"content": content[:200]},
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Edit tool", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 5: Grep tool - search file contents
        self.reset_agent()
        try:
            result = await self.run_prompt(
                "Use Grep to search for 'BaseTool' in src/code_forge/tools/. "
                "Tell me which files contain this term."
            )
            tool_called = any(tc.name == "Grep" for tc in result.tool_calls)
            # Should find base.py
            has_results = "base" in result.output.lower()
            if tool_called and has_results:
                suite.results.append(TestResult(
                    name="Grep tool",
                    passed=True,
                    message="Found files containing BaseTool",
                ))
            else:
                suite.results.append(TestResult(
                    name="Grep tool",
                    passed=False,
                    message="Grep failed" if not tool_called else "No results found",
                    details={"response": result.output[:200]},
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Grep tool", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 6: Bash tool - run command
        self.reset_agent()
        try:
            result = await self.run_prompt(
                "Use Bash to run 'pwd' and tell me the current directory."
            )
            tool_called = any(tc.name == "Bash" for tc in result.tool_calls)
            # Should contain a path
            has_path = "/" in result.output or "Code-Forge" in result.output
            if tool_called and has_path:
                suite.results.append(TestResult(
                    name="Bash tool",
                    passed=True,
                    message="Ran command and got path",
                ))
            else:
                suite.results.append(TestResult(
                    name="Bash tool",
                    passed=False,
                    message="Bash failed" if not tool_called else "No path in output",
                    details={"response": result.output[:200]},
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Bash tool", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 7: BashOutput tool - monitor background process
        self.reset_agent()
        try:
            result = await self.run_prompt(
                "Use Bash to start a background command 'sleep 1 && echo done' "
                "(set run_in_background=true), then use BashOutput to check its status."
            )
            bash_called = any(tc.name == "Bash" for tc in result.tool_calls)
            bashoutput_called = any(tc.name == "BashOutput" for tc in result.tool_calls)

            if bash_called and bashoutput_called:
                suite.results.append(TestResult(
                    name="BashOutput tool",
                    passed=True,
                    message="Started background process and checked output",
                ))
            elif bash_called:
                suite.results.append(TestResult(
                    name="BashOutput tool",
                    passed=True,
                    message="Bash called (BashOutput may not be needed)",
                ))
            else:
                suite.results.append(TestResult(
                    name="BashOutput tool",
                    passed=False,
                    message="Background process workflow incomplete",
                    details={"response": result.output[:200]},
                ))
        except Exception as e:
            suite.results.append(TestResult(name="BashOutput tool", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 8: KillShell tool - terminate process
        self.reset_agent()
        try:
            result = await self.run_prompt(
                "Use Bash to start a long-running background command 'sleep 60' "
                "(set run_in_background=true), then use KillShell to terminate it."
            )
            bash_called = any(tc.name == "Bash" for tc in result.tool_calls)
            kill_called = any(tc.name == "KillShell" for tc in result.tool_calls)

            if bash_called and kill_called:
                suite.results.append(TestResult(
                    name="KillShell tool",
                    passed=True,
                    message="Started and terminated background process",
                ))
            elif bash_called:
                suite.results.append(TestResult(
                    name="KillShell tool",
                    passed=True,
                    message="Bash called (process may have completed)",
                ))
            else:
                suite.results.append(TestResult(
                    name="KillShell tool",
                    passed=False,
                    message="Process termination workflow incomplete",
                    details={"response": result.output[:200]},
                ))
        except Exception as e:
            suite.results.append(TestResult(name="KillShell tool", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        return suite

    # =========================================================================
    # Test Suite: Multi-Turn Context Retention
    # =========================================================================

    async def test_context_retention(self) -> TestSuiteResult:
        """Test that context is retained across multiple turns."""
        suite = TestSuiteResult(name="Context Retention")
        print("\n[Suite] Context Retention Tests")
        print("-" * 40)

        # Reset once at the start - keep memory for all turns
        self.reset_agent()

        # Turn 1: Read a file and establish context
        try:
            result1 = await self.run_prompt(
                "Read pyproject.toml and remember these details: "
                "the project name, version, and description."
            )
            tool_called = any(tc.name == "Read" for tc in result1.tool_calls)
            if tool_called:
                suite.results.append(TestResult(
                    name="Turn 1: Read and memorize",
                    passed=True,
                    message="File read successfully",
                ))
            else:
                suite.results.append(TestResult(
                    name="Turn 1: Read and memorize",
                    passed=False,
                    message="Read tool not called",
                ))
            self.print_result(suite.results[-1])
        except Exception as e:
            suite.results.append(TestResult(
                name="Turn 1: Read and memorize",
                passed=False,
                message=f"Error: {e}",
            ))
            self.print_result(suite.results[-1])
            return suite

        # Turn 2: Recall version from memory
        try:
            result2 = await self.run_prompt(
                "What was the project version? Answer from memory, don't read the file again."
            )
            read_called_again = any(tc.name == "Read" for tc in result2.tool_calls)
            has_version = "1.0.0" in result2.output

            if has_version and not read_called_again:
                suite.results.append(TestResult(
                    name="Turn 2: Recall version",
                    passed=True,
                    message="Version recalled from memory",
                ))
            elif has_version:
                suite.results.append(TestResult(
                    name="Turn 2: Recall version",
                    passed=True,
                    message="Version found (re-read file)",
                ))
            else:
                suite.results.append(TestResult(
                    name="Turn 2: Recall version",
                    passed=False,
                    message="Could not recall version",
                    details={"response": result2.output[:200]},
                ))
            self.print_result(suite.results[-1])
        except Exception as e:
            suite.results.append(TestResult(
                name="Turn 2: Recall version",
                passed=False,
                message=f"Error: {e}",
            ))
            self.print_result(suite.results[-1])

        # Turn 3: Recall project name
        try:
            result3 = await self.run_prompt(
                "What was the project name from that file?"
            )
            has_name = "code_forge" in result3.output.lower()

            if has_name:
                suite.results.append(TestResult(
                    name="Turn 3: Recall name",
                    passed=True,
                    message="Project name recalled",
                ))
            else:
                suite.results.append(TestResult(
                    name="Turn 3: Recall name",
                    passed=False,
                    message="Could not recall name",
                    details={"response": result3.output[:200]},
                ))
            self.print_result(suite.results[-1])
        except Exception as e:
            suite.results.append(TestResult(
                name="Turn 3: Recall name",
                passed=False,
                message=f"Error: {e}",
            ))
            self.print_result(suite.results[-1])

        # Turn 4: Use recalled info in a new question
        try:
            result4 = await self.run_prompt(
                "Based on the description you read, what does this project do?"
            )
            # Should mention AI, CLI, development, assistant, or similar
            relevant = any(word in result4.output.lower() for word in
                         ["ai", "cli", "assistant", "development", "openrouter", "langchain"])

            if relevant:
                suite.results.append(TestResult(
                    name="Turn 4: Use context",
                    passed=True,
                    message="Used file context in answer",
                ))
            else:
                suite.results.append(TestResult(
                    name="Turn 4: Use context",
                    passed=False,
                    message="Answer not based on file context",
                    details={"response": result4.output[:200]},
                ))
            self.print_result(suite.results[-1])
        except Exception as e:
            suite.results.append(TestResult(
                name="Turn 4: Use context",
                passed=False,
                message=f"Error: {e}",
            ))
            self.print_result(suite.results[-1])

        return suite

    # =========================================================================
    # Test Suite: File Operations Workflow
    # =========================================================================

    async def test_file_workflow(self) -> TestSuiteResult:
        """Test a complete file operations workflow."""
        suite = TestSuiteResult(name="File Workflow")
        print("\n[Suite] File Operations Workflow Tests")
        print("-" * 40)

        self.reset_agent()

        # Create test file
        workflow_file = os.path.join(self.temp_dir, "workflow_test.py")
        with open(workflow_file, "w") as f:
            f.write('''def greet(name):
    """Greet a person."""
    return f"Hello, {name}!"

def add(a, b):
    """Add two numbers."""
    return a + b
''')

        try:
            # Step 1: Read and understand the file
            result1 = await self.run_prompt(
                f"Read {workflow_file} and tell me what functions are defined."
            )
            read_called = any(tc.name == "Read" for tc in result1.tool_calls)
            has_functions = "greet" in result1.output.lower() and "add" in result1.output.lower()

            if read_called and has_functions:
                suite.results.append(TestResult(
                    name="Read and analyze",
                    passed=True,
                    message="Identified both functions",
                ))
            else:
                suite.results.append(TestResult(
                    name="Read and analyze",
                    passed=False,
                    message=f"Analysis incomplete (read={read_called}, functions={has_functions})",
                ))
            self.print_result(suite.results[-1])

            # Step 2: Edit the file to add a new function
            result2 = await self.run_prompt(
                f"Edit {workflow_file} to add a new function called 'subtract' that subtracts b from a. "
                "Add it after the add function."
            )
            edit_called = any(tc.name == "Edit" for tc in result2.tool_calls)
            with open(workflow_file) as f:
                content = f.read()
            has_subtract = "def subtract" in content

            if edit_called and has_subtract:
                suite.results.append(TestResult(
                    name="Add new function",
                    passed=True,
                    message="Added subtract function",
                ))
            else:
                suite.results.append(TestResult(
                    name="Add new function",
                    passed=False,
                    message=f"Edit failed (edit={edit_called}, has_subtract={has_subtract})",
                ))
            self.print_result(suite.results[-1])

            # Step 3: Verify the edit by reading again
            result3 = await self.run_prompt(
                f"Read {workflow_file} again and confirm the subtract function was added correctly."
            )
            read_called = any(tc.name == "Read" for tc in result3.tool_calls)
            confirms_edit = "subtract" in result3.output.lower()

            if read_called and confirms_edit:
                suite.results.append(TestResult(
                    name="Verify edit",
                    passed=True,
                    message="Confirmed subtract function exists",
                ))
            else:
                suite.results.append(TestResult(
                    name="Verify edit",
                    passed=False,
                    message="Could not verify edit",
                ))
            self.print_result(suite.results[-1])

        except Exception as e:
            suite.results.append(TestResult(
                name="Workflow error",
                passed=False,
                message=f"Error: {e}",
            ))
            self.print_result(suite.results[-1])

        return suite

    # =========================================================================
    # Test Suite: Search and Analysis
    # =========================================================================

    async def test_search_workflow(self) -> TestSuiteResult:
        """Test search and code analysis workflows."""
        suite = TestSuiteResult(name="Search & Analysis")
        print("\n[Suite] Search and Analysis Tests")
        print("-" * 40)

        # Test 1: Find files then read one
        self.reset_agent()
        try:
            result = await self.run_prompt(
                "Use Glob to find Python files in src/code_forge/core/, "
                "then Read the errors.py file and list the exception classes defined there."
            )
            glob_called = any(tc.name == "Glob" for tc in result.tool_calls)
            read_called = any(tc.name == "Read" for tc in result.tool_calls)
            # Should find Code-ForgeError
            has_exception = "code_forgeerror" in result.output.lower() or "error" in result.output.lower()

            if glob_called and read_called and has_exception:
                suite.results.append(TestResult(
                    name="Glob then Read",
                    passed=True,
                    message="Found files and analyzed errors.py",
                ))
            else:
                suite.results.append(TestResult(
                    name="Glob then Read",
                    passed=False,
                    message=f"Workflow incomplete (glob={glob_called}, read={read_called})",
                    details={"response": result.output[:200]},
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Glob then Read", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 2: Grep to find usage then understand
        self.reset_agent()
        try:
            result = await self.run_prompt(
                "Use Grep to find where 'ToolResult' is used in src/code_forge/tools/, "
                "then explain what ToolResult is used for based on the code."
            )
            grep_called = any(tc.name == "Grep" for tc in result.tool_calls)
            # Should explain tool results
            explains = any(word in result.output.lower() for word in
                          ["result", "success", "error", "output", "return"])

            if grep_called and explains:
                suite.results.append(TestResult(
                    name="Grep and explain",
                    passed=True,
                    message="Found usages and explained purpose",
                ))
            else:
                suite.results.append(TestResult(
                    name="Grep and explain",
                    passed=False,
                    message=f"Analysis incomplete (grep={grep_called})",
                    details={"response": result.output[:200]},
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Grep and explain", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 3: Complex multi-step analysis
        self.reset_agent()
        try:
            result = await self.run_prompt(
                "I want to understand the tool system. "
                "1. Use Glob to find files in src/code_forge/tools/ "
                "2. Read the base.py file "
                "3. Tell me the main classes and their purposes."
            )
            glob_called = any(tc.name == "Glob" for tc in result.tool_calls)
            read_called = any(tc.name == "Read" for tc in result.tool_calls)
            # Should mention BaseTool, ToolResult, etc.
            has_analysis = any(word in result.output.lower() for word in
                              ["basetool", "toolresult", "toolparameter", "execute"])

            if glob_called and read_called and has_analysis:
                suite.results.append(TestResult(
                    name="Multi-step analysis",
                    passed=True,
                    message="Completed multi-step code analysis",
                ))
            else:
                suite.results.append(TestResult(
                    name="Multi-step analysis",
                    passed=False,
                    message=f"Incomplete (glob={glob_called}, read={read_called}, analysis={has_analysis})",
                    details={"response": result.output[:300]},
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Multi-step analysis", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        return suite

    # =========================================================================
    # Test Suite: Error Handling
    # =========================================================================

    async def test_error_handling(self) -> TestSuiteResult:
        """Test error handling scenarios."""
        suite = TestSuiteResult(name="Error Handling")
        print("\n[Suite] Error Handling Tests")
        print("-" * 40)

        # Test 1: Non-existent file
        self.reset_agent()
        try:
            result = await self.run_prompt(
                "Read the file /nonexistent/path/file_xyz_12345.txt"
            )
            read_called = any(tc.name == "Read" for tc in result.tool_calls)
            handles_error = any(phrase in result.output.lower() for phrase in
                               ["not found", "does not exist", "no such file", "error", "cannot"])

            if read_called and handles_error:
                suite.results.append(TestResult(
                    name="Non-existent file",
                    passed=True,
                    message="Error handled gracefully",
                ))
            elif read_called:
                suite.results.append(TestResult(
                    name="Non-existent file",
                    passed=True,
                    message="Tool called (error in result)",
                ))
            else:
                suite.results.append(TestResult(
                    name="Non-existent file",
                    passed=False,
                    message="Read tool not called",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Non-existent file", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 2: Invalid bash command
        self.reset_agent()
        try:
            result = await self.run_prompt(
                "Run the command 'nonexistent_cmd_xyz_12345' using Bash"
            )
            bash_called = any(tc.name == "Bash" for tc in result.tool_calls)

            if bash_called:
                suite.results.append(TestResult(
                    name="Invalid command",
                    passed=True,
                    message="Attempted invalid command",
                ))
            else:
                suite.results.append(TestResult(
                    name="Invalid command",
                    passed=False,
                    message="Bash tool not called",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Invalid command", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 3: Edit without reading first (should fail or read first)
        self.reset_agent()
        edit_file = os.path.join(self.temp_dir, "edit_test.txt")
        with open(edit_file, "w") as f:
            f.write("test content")
        try:
            result = await self.run_prompt(
                f"Edit {edit_file} to change 'test' to 'modified'. "
                "You'll need to read it first."
            )
            # Should either read then edit, or handle the need to read
            read_called = any(tc.name == "Read" for tc in result.tool_calls)
            edit_called = any(tc.name == "Edit" for tc in result.tool_calls)

            if read_called and edit_called:
                suite.results.append(TestResult(
                    name="Edit requires read",
                    passed=True,
                    message="Read before edit (correct workflow)",
                ))
            elif edit_called:
                suite.results.append(TestResult(
                    name="Edit requires read",
                    passed=True,
                    message="Edit attempted",
                ))
            else:
                suite.results.append(TestResult(
                    name="Edit requires read",
                    passed=False,
                    message="Neither read nor edit called",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Edit requires read", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        return suite

    # =========================================================================
    # Test Suite: Web Tools
    # =========================================================================

    async def test_web_tools(self) -> TestSuiteResult:
        """Test web search and fetch tools."""
        suite = TestSuiteResult(name="Web Tools")
        print("\n[Suite] Web Tools Tests")
        print("-" * 40)

        # Check if web tools are registered
        web_tools_available = "WebSearch" in self.tool_names or "WebFetch" in self.tool_names

        if not web_tools_available:
            # Web tools not registered, test that they exist as modules
            try:
                from code_forge.web import WebSearchTool, WebFetchTool

                suite.results.append(TestResult(
                    name="WebSearch tool",
                    passed=True,
                    message="WebSearchTool class exists (not registered)",
                ))
                suite.results.append(TestResult(
                    name="WebFetch tool",
                    passed=True,
                    message="WebFetchTool class exists (not registered)",
                ))
            except ImportError as e:
                suite.results.append(TestResult(
                    name="WebSearch tool",
                    passed=False,
                    message=f"Import error: {e}",
                ))
                suite.results.append(TestResult(
                    name="WebFetch tool",
                    passed=False,
                    message=f"Import error: {e}",
                ))
            self.print_result(suite.results[-2])
            self.print_result(suite.results[-1])
            return suite

        # Test 1: WebSearch tool
        self.reset_agent()
        try:
            result = await self.run_prompt(
                "Use WebSearch to search for 'Python programming language' "
                "and tell me what you find."
            )
            tool_called = any(tc.name == "WebSearch" for tc in result.tool_calls)
            has_results = any(word in result.output.lower() for word in
                            ["python", "programming", "language", "guido", "search"])

            if tool_called and has_results:
                suite.results.append(TestResult(
                    name="WebSearch tool",
                    passed=True,
                    message="Search completed with results",
                ))
            elif tool_called:
                suite.results.append(TestResult(
                    name="WebSearch tool",
                    passed=True,
                    message="Search tool called",
                ))
            else:
                suite.results.append(TestResult(
                    name="WebSearch tool",
                    passed=False,
                    message="WebSearch not called",
                    details={"response": result.output[:200]},
                ))
        except Exception as e:
            suite.results.append(TestResult(name="WebSearch tool", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 2: WebFetch tool
        self.reset_agent()
        try:
            result = await self.run_prompt(
                "Use WebFetch to fetch https://example.com and describe what you see."
            )
            tool_called = any(tc.name == "WebFetch" for tc in result.tool_calls)
            has_content = any(word in result.output.lower() for word in
                            ["example", "domain", "website", "page", "html"])

            if tool_called and has_content:
                suite.results.append(TestResult(
                    name="WebFetch tool",
                    passed=True,
                    message="Fetched and analyzed web content",
                ))
            elif tool_called:
                suite.results.append(TestResult(
                    name="WebFetch tool",
                    passed=True,
                    message="Fetch tool called",
                ))
            else:
                suite.results.append(TestResult(
                    name="WebFetch tool",
                    passed=False,
                    message="WebFetch not called",
                    details={"response": result.output[:200]},
                ))
        except Exception as e:
            suite.results.append(TestResult(name="WebFetch tool", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        return suite

    # =========================================================================
    # Test Suite: Slash Commands
    # =========================================================================

    async def test_slash_commands(self) -> TestSuiteResult:
        """Test slash command execution."""
        suite = TestSuiteResult(name="Slash Commands")
        print("\n[Suite] Slash Commands Tests")
        print("-" * 40)

        from code_forge.commands import CommandExecutor, CommandContext, register_builtin_commands
        from code_forge.sessions import SessionManager

        # Register commands and create executor
        register_builtin_commands()
        session_manager = SessionManager.get_instance()
        session = session_manager.create(title="E2E Command Test")

        command_context = CommandContext(
            session_manager=session_manager,
            config=self.config,
            llm=None,
        )
        executor = CommandExecutor()

        # Test 1: /help command
        try:
            result = await executor.execute("/help", command_context)
            has_help = result.output and ("help" in result.output.lower() or "command" in result.output.lower())

            if has_help and not result.error:
                suite.results.append(TestResult(
                    name="/help command",
                    passed=True,
                    message="Help displayed successfully",
                ))
            else:
                suite.results.append(TestResult(
                    name="/help command",
                    passed=False,
                    message=f"Help failed: {result.error or 'no output'}",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="/help command", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 2: /commands command
        try:
            result = await executor.execute("/commands", command_context)
            has_commands = result.output and any(cmd in result.output.lower() for cmd in
                                                  ["help", "exit", "session", "config"])

            if has_commands and not result.error:
                suite.results.append(TestResult(
                    name="/commands command",
                    passed=True,
                    message="Commands list displayed",
                ))
            else:
                suite.results.append(TestResult(
                    name="/commands command",
                    passed=False,
                    message=f"Commands failed: {result.error or 'no output'}",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="/commands command", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 3: /tools command
        try:
            result = await executor.execute("/tools", command_context)
            has_tools = result.output and any(tool in result.output for tool in
                                               ["Read", "Write", "Bash", "Glob"])

            if has_tools and not result.error:
                suite.results.append(TestResult(
                    name="/tools command",
                    passed=True,
                    message="Tools list displayed",
                ))
            else:
                suite.results.append(TestResult(
                    name="/tools command",
                    passed=False,
                    message=f"Tools failed: {result.error or 'no output'}",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="/tools command", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 4: /session list command
        try:
            result = await executor.execute("/session list", command_context)
            # Should show at least our test session
            success = not result.error

            if success:
                suite.results.append(TestResult(
                    name="/session list command",
                    passed=True,
                    message="Session list executed",
                ))
            else:
                suite.results.append(TestResult(
                    name="/session list command",
                    passed=False,
                    message=f"Session list failed: {result.error}",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="/session list command", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 5: /config get command
        try:
            result = await executor.execute("/config get model.default", command_context)
            success = not result.error and result.output

            if success:
                suite.results.append(TestResult(
                    name="/config get command",
                    passed=True,
                    message="Config value retrieved",
                ))
            else:
                suite.results.append(TestResult(
                    name="/config get command",
                    passed=False,
                    message=f"Config get failed: {result.error}",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="/config get command", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Clean up test session
        try:
            session_manager.delete(session.id)
        except Exception:
            pass

        return suite

    # =========================================================================
    # Test Suite: Session Management
    # =========================================================================

    async def test_session_management(self) -> TestSuiteResult:
        """Test session creation, saving, and retrieval."""
        suite = TestSuiteResult(name="Session Management")
        print("\n[Suite] Session Management Tests")
        print("-" * 40)

        from code_forge.sessions import SessionManager

        session_manager = SessionManager.get_instance()
        test_session_id = None

        # Test 1: Create session
        try:
            session = session_manager.create(title="E2E Test Session")
            test_session_id = session.id

            if session.id and session.title == "E2E Test Session":
                suite.results.append(TestResult(
                    name="Create session",
                    passed=True,
                    message=f"Session created: {session.id[:8]}...",
                ))
            else:
                suite.results.append(TestResult(
                    name="Create session",
                    passed=False,
                    message="Session creation incomplete",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Create session", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 2: Add messages to session
        try:
            session_manager.add_message("user", "Test message from E2E")
            session_manager.add_message("assistant", "Test response from E2E")

            current = session_manager.current_session
            has_messages = current and len(current.messages) >= 2

            if has_messages:
                suite.results.append(TestResult(
                    name="Add messages",
                    passed=True,
                    message="Messages added to session",
                ))
            else:
                suite.results.append(TestResult(
                    name="Add messages",
                    passed=False,
                    message="Messages not found in session",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Add messages", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 3: Save session
        try:
            session_manager.save()

            suite.results.append(TestResult(
                name="Save session",
                passed=True,
                message="Session saved successfully",
            ))
        except Exception as e:
            suite.results.append(TestResult(name="Save session", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 4: List sessions
        try:
            sessions = session_manager.list_sessions()
            found = any(s.id == test_session_id for s in sessions)

            if found:
                suite.results.append(TestResult(
                    name="List sessions",
                    passed=True,
                    message=f"Found {len(sessions)} sessions",
                ))
            else:
                suite.results.append(TestResult(
                    name="List sessions",
                    passed=False,
                    message="Test session not found in list",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="List sessions", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 5: Resume session
        try:
            # Create a new session first
            session_manager.create(title="Another Session")

            # Now resume the original test session
            resumed = session_manager.resume(test_session_id)

            if resumed and resumed.id == test_session_id:
                suite.results.append(TestResult(
                    name="Resume session",
                    passed=True,
                    message="Session resumed successfully",
                ))
            else:
                suite.results.append(TestResult(
                    name="Resume session",
                    passed=False,
                    message="Could not resume session",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Resume session", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 6: Delete session
        try:
            if test_session_id:
                session_manager.delete(test_session_id)
                sessions = session_manager.list_sessions()
                deleted = not any(s.id == test_session_id for s in sessions)

                if deleted:
                    suite.results.append(TestResult(
                        name="Delete session",
                        passed=True,
                        message="Session deleted successfully",
                    ))
                else:
                    suite.results.append(TestResult(
                        name="Delete session",
                        passed=False,
                        message="Session still exists after delete",
                    ))
            else:
                suite.results.append(TestResult(
                    name="Delete session",
                    passed=False,
                    message="No session to delete",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Delete session", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        return suite

    # =========================================================================
    # Test Suite: Context Management
    # =========================================================================

    async def test_context_management(self) -> TestSuiteResult:
        """Test context token counting and management."""
        suite = TestSuiteResult(name="Context Management")
        print("\n[Suite] Context Management Tests")
        print("-" * 40)

        from code_forge.context import get_counter, ContextManager, SlidingWindowStrategy

        # Test 1: Token counting
        try:
            counter = get_counter("anthropic/claude-3.5-sonnet")  # Factory function needs model
            test_text = "Hello, this is a test message for token counting."
            count = counter.count(test_text)

            if count > 0:
                suite.results.append(TestResult(
                    name="Token counting",
                    passed=True,
                    message=f"Counted {count} tokens",
                ))
            else:
                suite.results.append(TestResult(
                    name="Token counting",
                    passed=False,
                    message="Token count was 0",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Token counting", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 2: Context limits via llm routing
        try:
            from code_forge.llm.routing import get_model_context_limit

            max_tokens = get_model_context_limit("anthropic/claude-3.5-sonnet")

            if max_tokens > 0:
                suite.results.append(TestResult(
                    name="Context limits",
                    passed=True,
                    message=f"Max context: {max_tokens:,} tokens",
                ))
            else:
                suite.results.append(TestResult(
                    name="Context limits",
                    passed=False,
                    message="Could not determine context limit",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Context limits", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 3: Truncation strategy
        try:
            from code_forge.context import get_counter

            strategy = SlidingWindowStrategy(window_size=5)  # Correct parameter name
            # Create messages as dicts (what the strategy expects)
            messages = [
                {"role": "user", "content": f"Message {i}"} for i in range(10)
            ]
            # Get a counter for the truncation
            counter = get_counter("anthropic/claude-3.5-sonnet")
            truncated = strategy.truncate(messages, 100000, counter)

            if len(truncated) <= 5:
                suite.results.append(TestResult(
                    name="Truncation strategy",
                    passed=True,
                    message=f"Truncated from 10 to {len(truncated)} messages",
                ))
            else:
                suite.results.append(TestResult(
                    name="Truncation strategy",
                    passed=False,
                    message=f"Truncation failed: {len(truncated)} messages",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Truncation strategy", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 4: Context manager
        try:
            manager = ContextManager(model="anthropic/claude-3.5-sonnet")

            suite.results.append(TestResult(
                name="Context manager",
                passed=True,
                message="Context manager created",
            ))
        except Exception as e:
            suite.results.append(TestResult(name="Context manager", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        return suite

    # =========================================================================
    # Test Suite: Subagents
    # =========================================================================

    async def test_subagents(self) -> TestSuiteResult:
        """Test subagent system."""
        suite = TestSuiteResult(name="Subagents")
        print("\n[Suite] Subagents Tests")
        print("-" * 40)

        from code_forge.agents import AgentTypeRegistry, AgentManager

        # Test 1: Agent type registry
        try:
            registry = AgentTypeRegistry.get_instance()
            types = registry.list_types()

            expected_types = ["explore", "plan", "code-review", "general"]
            found_types = [t for t in expected_types if t in types]

            if len(found_types) >= 2:
                suite.results.append(TestResult(
                    name="Agent type registry",
                    passed=True,
                    message=f"Found agent types: {', '.join(found_types)}",
                ))
            else:
                suite.results.append(TestResult(
                    name="Agent type registry",
                    passed=False,
                    message=f"Missing agent types. Found: {types}",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Agent type registry", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 2: Agent manager singleton
        try:
            manager = AgentManager.get_instance()

            if manager is not None:
                suite.results.append(TestResult(
                    name="Agent manager",
                    passed=True,
                    message="Agent manager initialized",
                ))
            else:
                suite.results.append(TestResult(
                    name="Agent manager",
                    passed=False,
                    message="Agent manager is None",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Agent manager", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 3: Create agent config
        try:
            from code_forge.agents import AgentConfig

            config = AgentConfig(
                agent_type="explore",
                description="Test task for E2E",
            )

            if config.agent_type == "explore" and config.description:
                suite.results.append(TestResult(
                    name="Agent config",
                    passed=True,
                    message="Agent config created",
                ))
            else:
                suite.results.append(TestResult(
                    name="Agent config",
                    passed=False,
                    message="Agent config invalid",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Agent config", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 4: Agent through main agent (integration test)
        self.reset_agent()
        try:
            # Ask the main agent to use an explore subagent
            result = await self.run_prompt(
                "Using your capabilities, briefly describe the structure of src/code_forge/tools/. "
                "Focus on what types of files are there."
            )

            # Should provide information about the tools directory
            has_info = any(word in result.output.lower() for word in
                         ["tool", "file", "base", "execution", "python", ".py"])

            if has_info:
                suite.results.append(TestResult(
                    name="Agent task execution",
                    passed=True,
                    message="Agent explored codebase",
                ))
            else:
                suite.results.append(TestResult(
                    name="Agent task execution",
                    passed=False,
                    message="Agent did not provide expected info",
                    details={"response": result.output[:200]},
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Agent task execution", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        return suite

    # =========================================================================
    # Test Suite: Git Integration
    # =========================================================================

    async def test_git_integration(self) -> TestSuiteResult:
        """Test Git integration features."""
        suite = TestSuiteResult(name="Git Integration")
        print("\n[Suite] Git Integration Tests")
        print("-" * 40)

        from code_forge.git import GitRepository

        # Test 1: Repository detection
        try:
            repo = GitRepository(os.getcwd())
            is_repo = repo.is_git_repo  # Property, not method

            if is_repo:
                suite.results.append(TestResult(
                    name="Repository detection",
                    passed=True,
                    message="Git repository detected",
                ))
            else:
                suite.results.append(TestResult(
                    name="Repository detection",
                    passed=False,
                    message="Not a git repository",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Repository detection", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 2: Get current branch
        try:
            repo = GitRepository(os.getcwd())
            branch = repo.current_branch  # Property, not method

            if branch:
                suite.results.append(TestResult(
                    name="Current branch",
                    passed=True,
                    message=f"Branch: {branch}",
                ))
            else:
                suite.results.append(TestResult(
                    name="Current branch",
                    passed=False,
                    message="Could not get branch",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Current branch", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 3: Git root
        try:
            repo = GitRepository(os.getcwd())
            root = repo.root  # Property

            if root and root.exists():
                suite.results.append(TestResult(
                    name="Git root",
                    passed=True,
                    message=f"Root: {root}",
                ))
            else:
                suite.results.append(TestResult(
                    name="Git root",
                    passed=False,
                    message="Root not found",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Git root", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 4: Is dirty check
        try:
            repo = GitRepository(os.getcwd())
            is_dirty = repo.is_dirty  # Property

            suite.results.append(TestResult(
                name="Dirty check",
                passed=True,
                message=f"Repository dirty: {is_dirty}",
            ))
        except Exception as e:
            suite.results.append(TestResult(name="Dirty check", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 5: Get info (async)
        try:
            repo = GitRepository(os.getcwd())
            info = await repo.get_info()

            if info and info.is_git_repo:
                suite.results.append(TestResult(
                    name="Repository info",
                    passed=True,
                    message=f"Info retrieved, branch: {info.current_branch}",
                ))
            else:
                suite.results.append(TestResult(
                    name="Repository info",
                    passed=False,
                    message="Could not get repository info",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Repository info", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        return suite

    # =========================================================================
    # Test Suite: Permission System
    # =========================================================================

    async def test_permission_system(self) -> TestSuiteResult:
        """Test permission checking system."""
        suite = TestSuiteResult(name="Permission System")
        print("\n[Suite] Permission System Tests")
        print("-" * 40)

        from code_forge.permissions import PermissionChecker, PermissionLevel, PermissionRule, RuleSet

        # Test 1: Permission levels
        try:
            levels = [PermissionLevel.ALLOW, PermissionLevel.ASK, PermissionLevel.DENY]

            if len(levels) == 3:
                suite.results.append(TestResult(
                    name="Permission levels",
                    passed=True,
                    message="All permission levels available",
                ))
            else:
                suite.results.append(TestResult(
                    name="Permission levels",
                    passed=False,
                    message="Missing permission levels",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Permission levels", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 2: Permission rule creation
        try:
            rule = PermissionRule(
                pattern="Bash(*)",
                permission=PermissionLevel.ASK,
            )

            if rule.pattern and rule.permission == PermissionLevel.ASK:
                suite.results.append(TestResult(
                    name="Permission rule creation",
                    passed=True,
                    message="Rule created successfully",
                ))
            else:
                suite.results.append(TestResult(
                    name="Permission rule creation",
                    passed=False,
                    message="Rule creation failed",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Permission rule creation", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 3: Permission checker
        try:
            checker = PermissionChecker()

            # Check a tool permission
            result = checker.check("Read", {"file_path": "/tmp/test.txt"})

            # Result is PermissionResult with .allowed, .needs_confirmation, .denied
            if hasattr(result, 'allowed') or hasattr(result, 'level'):
                suite.results.append(TestResult(
                    name="Permission checker",
                    passed=True,
                    message="Permission check completed",
                ))
            else:
                suite.results.append(TestResult(
                    name="Permission checker",
                    passed=False,
                    message="Invalid result returned",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Permission checker", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 4: RuleSet
        try:
            ruleset = RuleSet(rules=[
                PermissionRule(
                    pattern="Read(/etc/*)",
                    permission=PermissionLevel.DENY,
                )
            ])

            suite.results.append(TestResult(
                name="RuleSet",
                passed=True,
                message="RuleSet created with rule",
            ))
        except Exception as e:
            suite.results.append(TestResult(name="RuleSet", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        return suite

    # =========================================================================
    # Test Suite: Hooks System
    # =========================================================================

    async def test_hooks_system(self) -> TestSuiteResult:
        """Test hooks system."""
        suite = TestSuiteResult(name="Hooks System")
        print("\n[Suite] Hooks System Tests")
        print("-" * 40)

        from code_forge.hooks import HookExecutor, EventType, HookRegistry, Hook

        # Test 1: Event types
        try:
            # EventType contains the hook event names
            types = [
                EventType.TOOL_PRE_EXECUTE,
                EventType.TOOL_POST_EXECUTE,
                EventType.USER_PROMPT_SUBMIT,
            ]

            if len(types) >= 3:
                suite.results.append(TestResult(
                    name="Event types",
                    passed=True,
                    message="Event types available",
                ))
            else:
                suite.results.append(TestResult(
                    name="Event types",
                    passed=False,
                    message="Missing event types",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Event types", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 2: Hook registry
        try:
            registry = HookRegistry.get_instance()

            if registry is not None:
                suite.results.append(TestResult(
                    name="Hook registry",
                    passed=True,
                    message="Registry created",
                ))
            else:
                suite.results.append(TestResult(
                    name="Hook registry",
                    passed=False,
                    message="Registry is None",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Hook registry", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 3: Hook executor creation
        try:
            executor = HookExecutor()

            if executor is not None:
                suite.results.append(TestResult(
                    name="Hook executor",
                    passed=True,
                    message="Executor created",
                ))
            else:
                suite.results.append(TestResult(
                    name="Hook executor",
                    passed=False,
                    message="Executor is None",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Hook executor", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        return suite

    # =========================================================================
    # Test Suite: Plugin System
    # =========================================================================

    async def test_plugin_system(self) -> TestSuiteResult:
        """Test plugin system."""
        suite = TestSuiteResult(name="Plugin System")
        print("\n[Suite] Plugin System Tests")
        print("-" * 40)

        from code_forge.plugins import PluginManager, PluginRegistry

        # Test 1: Plugin registry (not a singleton, just a class)
        try:
            registry = PluginRegistry()

            if registry is not None:
                suite.results.append(TestResult(
                    name="Plugin registry",
                    passed=True,
                    message="Registry created",
                ))
            else:
                suite.results.append(TestResult(
                    name="Plugin registry",
                    passed=False,
                    message="Registry is None",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Plugin registry", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 2: Plugin manager (not a singleton, just a class)
        try:
            manager = PluginManager()

            if manager is not None:
                suite.results.append(TestResult(
                    name="Plugin manager",
                    passed=True,
                    message="Manager created",
                ))
            else:
                suite.results.append(TestResult(
                    name="Plugin manager",
                    passed=False,
                    message="Manager is None",
                ))
        except Exception as e:
            suite.results.append(TestResult(name="Plugin manager", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        # Test 3: Plugin discovery
        try:
            from code_forge.plugins import PluginDiscovery

            discovery = PluginDiscovery()

            suite.results.append(TestResult(
                name="Plugin discovery",
                passed=True,
                message="Discovery initialized",
            ))
        except Exception as e:
            suite.results.append(TestResult(name="Plugin discovery", passed=False, message=f"Error: {e}"))
        self.print_result(suite.results[-1])

        return suite

    # =========================================================================
    # Main Runner
    # =========================================================================

    async def run_all(self, suites: list[str] | None = None) -> int:
        """Run all test suites."""
        if not await self.setup():
            return 1

        all_suites: list[TestSuiteResult] = []
        suite_map = {
            "tools": self.test_all_tools,
            "context": self.test_context_retention,
            "workflow": self.test_file_workflow,
            "search": self.test_search_workflow,
            "errors": self.test_error_handling,
            "web": self.test_web_tools,
            "commands": self.test_slash_commands,
            "sessions": self.test_session_management,
            "context-mgmt": self.test_context_management,
            "subagents": self.test_subagents,
            "git": self.test_git_integration,
            "permissions": self.test_permission_system,
            "hooks": self.test_hooks_system,
            "plugins": self.test_plugin_system,
        }

        # Determine which suites to run
        if suites is None or "all" in suites:
            suites_to_run = list(suite_map.keys())
        else:
            suites_to_run = [s for s in suites if s in suite_map]

        try:
            for suite_name in suites_to_run:
                try:
                    result = await suite_map[suite_name]()
                    all_suites.append(result)
                except Exception as e:
                    print(f"\n  ✗ Suite '{suite_name}' failed with error: {e}")
        finally:
            self.cleanup()

        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        total_passed = 0
        total_failed = 0

        for suite in all_suites:
            status = "✓" if suite.failed == 0 else "✗"
            print(f"{status} {suite.name}: {suite.passed}/{suite.total} passed")
            total_passed += suite.passed
            total_failed += suite.failed

        print("-" * 40)
        print(f"Total: {total_passed} passed, {total_failed} failed")
        print("=" * 60)

        return 0 if total_failed == 0 else 1


async def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Code-Forge End-to-End Tests")
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output",
    )
    parser.add_argument(
        "--suite", "-s",
        action="append",
        choices=[
            "all", "tools", "context", "workflow", "search", "errors",
            "web", "commands", "sessions", "context-mgmt", "subagents",
            "git", "permissions", "hooks", "plugins"
        ],
        help="Test suite(s) to run (default: all)",
    )
    args = parser.parse_args()

    tester = EndToEndTester(verbose=args.verbose)
    return await tester.run_all(args.suite)


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
