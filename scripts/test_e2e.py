#!/usr/bin/env python3
"""End-to-end test for OpenCode agent.

This script tests the full agent flow:
1. Load configuration
2. Create LLM with OpenRouter
3. Register and bind tools
4. Set system prompt
5. Run agent with test prompts
6. Verify tool calls and responses

Usage:
    python scripts/test_e2e.py
"""

from __future__ import annotations

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


async def main() -> int:
    """Run end-to-end tests."""
    from opencode.config import ConfigLoader
    from opencode.langchain.agent import OpenCodeAgent
    from opencode.langchain.llm import OpenRouterLLM
    from opencode.langchain.prompts import get_system_prompt
    from opencode.llm import OpenRouterClient
    from opencode.llm.models import Message
    from opencode.tools import ToolRegistry, register_all_tools

    print("=" * 60)
    print("OpenCode End-to-End Test")
    print("=" * 60)

    # Step 1: Load configuration
    print("\n[1/6] Loading configuration...")
    try:
        config_loader = ConfigLoader()
        config = config_loader.load_all()
        print(f"  ✓ Config loaded, default model: {config.model.default}")
    except Exception as e:
        print(f"  ✗ Failed to load config: {e}")
        return 1

    # Step 2: Check API key
    print("\n[2/6] Checking API key...")
    api_key = os.environ.get("OPENROUTER_API_KEY") or config.get_api_key()
    if not api_key:
        print("  ✗ OPENROUTER_API_KEY not set")
        print("    Set it with: export OPENROUTER_API_KEY=your-key")
        return 1
    print(f"  ✓ API key found ({api_key[:10]}...)")

    # Step 3: Create LLM
    print("\n[3/6] Creating LLM...")
    try:
        client = OpenRouterClient(api_key=api_key)
        llm = OpenRouterLLM(client=client, model=config.model.default)
        print(f"  ✓ LLM created with model: {config.model.default}")
    except Exception as e:
        print(f"  ✗ Failed to create LLM: {e}")
        return 1

    # Step 4: Register tools
    print("\n[4/6] Registering tools...")
    try:
        register_all_tools()
        tool_registry = ToolRegistry()
        tools = [tool_registry.get(name) for name in tool_registry.list_names()]
        tools = [t for t in tools if t is not None]
        tool_names = [t.name for t in tools if hasattr(t, "name")]
        print(f"  ✓ Registered {len(tools)} tools: {', '.join(tool_names[:5])}...")
    except Exception as e:
        print(f"  ✗ Failed to register tools: {e}")
        return 1

    # Step 5: Create agent with system prompt
    print("\n[5/6] Creating agent...")
    try:
        agent = OpenCodeAgent(llm=llm, tools=tools, max_iterations=5)
        system_prompt = get_system_prompt(
            tool_names=tool_names,
            working_directory=os.getcwd(),
            model=config.model.default,
        )
        agent.memory.set_system_message(Message.system(system_prompt))
        print(f"  ✓ Agent created with {len(system_prompt)} char system prompt")
    except Exception as e:
        print(f"  ✗ Failed to create agent: {e}")
        return 1

    # Step 6: Run test prompts
    print("\n[6/6] Running test prompts...")

    test_cases = [
        {
            "name": "List files",
            "prompt": "Use the Glob tool to list Python files in the src/opencode directory. Just list the first 5 files you find.",
            "expect_tool": "Glob",
        },
        {
            "name": "Read file",
            "prompt": "Use the Read tool to read the first 20 lines of pyproject.toml and tell me the project name.",
            "expect_tool": "Read",
        },
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\n  Test {i}: {test['name']}")
        print(f"  Prompt: {test['prompt'][:60]}...")

        try:
            # Reset agent memory for each test
            agent.reset()
            agent.memory.set_system_message(Message.system(system_prompt))

            # Run agent
            result = await agent.run(test["prompt"])

            # Check if expected tool was called
            tool_called = any(tc.name == test["expect_tool"] for tc in result.tool_calls)

            if tool_called:
                print(f"  ✓ Tool '{test['expect_tool']}' was called")
                print(f"  ✓ Got response ({len(result.output)} chars)")
                print(f"    Iterations: {result.iterations}, Tools called: {len(result.tool_calls)}")
                if result.usage:
                    print(f"    Tokens: {result.usage.total_tokens}")
                passed += 1
            else:
                print(f"  ✗ Expected tool '{test['expect_tool']}' was NOT called")
                print(f"    Tools called: {[tc.name for tc in result.tool_calls]}")
                print(f"    Response: {result.output[:200]}...")
                failed += 1

        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
