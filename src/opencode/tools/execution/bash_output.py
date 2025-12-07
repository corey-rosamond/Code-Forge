"""Tool for retrieving output from background shells."""

from __future__ import annotations

import re
from typing import Any

from opencode.tools.base import (
    BaseTool,
    ExecutionContext,
    ToolCategory,
    ToolParameter,
    ToolResult,
)
from opencode.tools.execution.shell_manager import ShellManager


class BashOutputTool(BaseTool):
    """Retrieve output from a running or completed background shell.

    Returns only new output since the last check.
    """

    @property
    def name(self) -> str:
        return "BashOutput"

    @property
    def description(self) -> str:
        return """Retrieves output from a running or completed background bash shell.

Usage:
- Takes a bash_id parameter identifying the shell
- Returns only new output since the last check
- Returns stdout and stderr output along with shell status
- Supports optional regex filtering to show only matching lines
- Shell IDs can be found from BashTool output or /tasks command"""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.EXECUTION

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="bash_id",
                type="string",
                description="The ID of the background shell to retrieve output from",
                required=True,
            ),
            ToolParameter(
                name="filter",
                type="string",
                description="Optional regex to filter output lines. "
                "Non-matching lines will be discarded.",
                required=False,
            ),
        ]

    async def _execute(
        self, context: ExecutionContext, **kwargs: Any  # noqa: ARG002
    ) -> ToolResult:
        bash_id = kwargs["bash_id"]
        filter_pattern = kwargs.get("filter")

        # Get shell
        shell = ShellManager.get_shell(bash_id)
        if shell is None:
            return ToolResult.fail(
                f"Shell not found: {bash_id}. "
                "The shell may have been cleaned up or the ID is incorrect."
            )

        # Read any pending output (always try, even if process completed)
        await shell.read_output()

        # Get new output
        output = shell.get_new_output()

        # Apply filter if provided
        if filter_pattern and output:
            try:
                regex = re.compile(filter_pattern)
                lines = output.splitlines()
                filtered_lines = [line for line in lines if regex.search(line)]
                output = "\n".join(filtered_lines)
            except re.error as e:
                return ToolResult.fail(f"Invalid filter regex: {e!s}")

        # Build status message
        status_msg = f"Status: {shell.status.value}"
        if shell.exit_code is not None:
            status_msg += f", Exit code: {shell.exit_code}"
        if shell.duration_ms:
            status_msg += f", Duration: {shell.duration_ms:.0f}ms"

        return ToolResult.ok(
            f"{status_msg}\n\n{output}" if output else status_msg,
            bash_id=bash_id,
            status=shell.status.value,
            exit_code=shell.exit_code,
            is_running=shell.is_running,
        )
