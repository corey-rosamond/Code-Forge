"""CLI entry point for OpenCode."""

from __future__ import annotations

import asyncio
import os
import sys
from typing import TYPE_CHECKING

from opencode import __version__
from opencode.cli.repl import OpenCodeREPL
from opencode.config import ConfigLoader
from opencode.core import get_logger

if TYPE_CHECKING:
    from opencode.config import OpenCodeConfig

logger = get_logger("cli")


def main() -> int:
    """Main entry point for OpenCode CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    args = sys.argv[1:]

    if "--version" in args or "-v" in args:
        print(f"opencode {__version__}")
        return 0

    if "--help" in args or "-h" in args:
        print_help()
        return 0

    # Check for unknown flags
    for arg in args:
        if arg.startswith("-") and arg not in (
            "-v",
            "--version",
            "-h",
            "--help",
            "-p",
            "--print",
            "--continue",
            "--resume",
        ):
            print(f"Error: Unknown option '{arg}'", file=sys.stderr)
            print("Run 'opencode --help' for usage information", file=sys.stderr)
            return 1

    # Load configuration
    try:
        config_loader = ConfigLoader()
        config = config_loader.load_all()
    except Exception as e:
        logger.exception("Failed to load configuration")
        print(f"Error: Failed to load configuration: {e}", file=sys.stderr)
        return 1

    # Check for API key
    api_key = os.environ.get("OPENROUTER_API_KEY") or config.get_api_key()
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set", file=sys.stderr)
        print("Get an API key at https://openrouter.ai/keys", file=sys.stderr)
        return 1

    # Start REPL
    try:
        repl = OpenCodeREPL(config)
        return asyncio.run(run_with_agent(repl, config, api_key))
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.exception("REPL error")
        print(f"Error: {e}", file=sys.stderr)
        return 1


async def run_with_agent(repl: OpenCodeREPL, config: OpenCodeConfig, api_key: str) -> int:
    """Run REPL with agent and command handling.

    Args:
        repl: The REPL instance.
        config: Application configuration.
        api_key: OpenRouter API key.

    Returns:
        Exit code.
    """
    from opencode.commands import CommandExecutor, CommandContext, register_builtin_commands
    from opencode.langchain.llm import OpenRouterLLM
    from opencode.langchain.agent import OpenCodeAgent
    from opencode.langchain.tools import adapt_tools_for_langchain
    from opencode.llm import OpenRouterClient
    from opencode.tools import ToolRegistry, register_all_tools
    from opencode.sessions import SessionManager

    # Register tools
    register_all_tools()
    tool_registry = ToolRegistry()

    # Create OpenRouter client and LLM
    from opencode.llm.routing import get_model_context_limit

    client = OpenRouterClient(api_key=api_key)
    llm = OpenRouterLLM(
        client=client,
        model=config.model.default,
    )

    # Update status bar with model info
    model_context = get_model_context_limit(config.model.default)
    repl._status.set_model(config.model.default)
    repl._status.set_tokens(0, model_context)

    # Create agent with tools (wrapped for LangChain compatibility)
    raw_tools = [tool_registry.get(name) for name in tool_registry.list_names()]
    raw_tools = [t for t in raw_tools if t is not None]
    tools = adapt_tools_for_langchain(raw_tools)
    agent = OpenCodeAgent(
        llm=llm,
        tools=tools,
    )

    # Set system prompt to instruct the LLM to use tools
    from opencode.llm.models import Message
    from opencode.langchain.prompts import get_system_prompt

    tool_names = [t.name for t in tools if t is not None and hasattr(t, "name")]
    system_prompt = get_system_prompt(
        tool_names=tool_names,
        working_directory=os.getcwd(),
        model=config.model.default,
    )

    agent.memory.set_system_message(Message.system(system_prompt))

    # Create session manager
    session_manager = SessionManager.get_instance()
    session = session_manager.create(title="CLI Session")

    # Register commands
    register_builtin_commands()

    # Create command context
    command_context = CommandContext(
        session_manager=session_manager,
        config=config,
        llm=llm,
    )

    # Create command executor (uses default registry and parser)
    command_executor = CommandExecutor()

    # Track cumulative token usage (use list for mutable closure)
    total_tokens = [0]

    # Register input handler
    async def handle_input(text: str) -> None:
        """Handle user input - route to commands or agent."""
        if text.startswith("/"):
            # Execute command
            cmd_result = await command_executor.execute(text, command_context)
            if cmd_result.output:
                repl.output.print(cmd_result.output)
            if cmd_result.error:
                repl.output.print_error(cmd_result.error)

            # Check for exit command
            if text.strip() in ("/exit", "/quit", "/q"):
                repl.stop()
        else:
            # Send to agent
            repl._status.set_status("Thinking...")
            try:
                # Add user message to session
                session_manager.add_message("user", text)

                # Run agent
                agent_result = await agent.run(text)

                # Display response
                repl.output.print(f"\n{agent_result.output}\n")

                # Add assistant message to session
                session_manager.add_message("assistant", agent_result.output)

                # Update token count (cumulative)
                if agent_result.usage:
                    total_tokens[0] += agent_result.usage.total_tokens
                    repl._status.set_tokens(total_tokens[0])

            except Exception as e:
                logger.exception("Agent error")
                repl.output.print_error(f"Error: {e}")
            finally:
                repl._status.set_status("Ready")

    repl.on_input(handle_input)

    # Run REPL
    return await repl.run()


def print_help() -> None:
    """Print help message."""
    help_text = """
OpenCode - AI-powered CLI Development Assistant

Usage: opencode [OPTIONS] [PROMPT]

Options:
  -v, --version     Show version and exit
  -h, --help        Show this help message
  --continue        Resume most recent session
  --resume          Select session to resume
  -p, --print       Run in headless mode with prompt

For more information, visit: https://github.com/opencode
"""
    print(help_text.strip())


if __name__ == "__main__":
    sys.exit(main())
