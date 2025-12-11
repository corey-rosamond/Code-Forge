"""Logging infrastructure for Code-Forge."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from rich.logging import RichHandler

if TYPE_CHECKING:
    from pathlib import Path


def setup_logging(
    level: int = logging.INFO,
    log_file: Path | None = None,
    rich_console: bool = True,
) -> None:
    """Configure logging for Code-Forge.

    Args:
        level: Logging level (default: INFO).
        log_file: Optional file path for log output.
        rich_console: Use Rich for console formatting (default: True).
    """
    handlers: list[logging.Handler] = []

    if rich_console:
        handlers.append(
            RichHandler(
                rich_tracebacks=True,
                show_time=True,
                show_path=False,
            )
        )
    else:
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        handlers.append(stream_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        handlers.append(file_handler)

    # Configure root logger for Code-Forge
    root_logger = logging.getLogger("Code-Forge")
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    for handler in handlers:
        root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: The name for the logger (will be prefixed with 'Code-Forge.').

    Returns:
        A configured Logger instance.
    """
    return logging.getLogger(f"Code-Forge.{name}")
