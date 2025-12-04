"""CLI entry point for OpenCode."""

from __future__ import annotations

import asyncio
import sys

from opencode import __version__
from opencode.cli.repl import OpenCodeREPL
from opencode.config import ConfigLoader
from opencode.core import get_logger

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

    # Start REPL
    try:
        repl = OpenCodeREPL(config)
        return asyncio.run(repl.run())
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.exception("REPL error")
        print(f"Error: {e}", file=sys.stderr)
        return 1


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
