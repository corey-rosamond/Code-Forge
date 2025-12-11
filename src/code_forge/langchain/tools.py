"""Tool adapters between LangChain and Code-Forge."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, ClassVar

from langchain_core.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel, Field, create_model


class LangChainToolAdapter(LangChainBaseTool):
    """
    Adapts an Code-Forge BaseTool to LangChain's tool interface.

    This allows Code-Forge tools to be used seamlessly with LangChain
    agents and chains.

    Example:
        ```python
        from code_forge.tools import ReadTool
        from code_forge.langchain.tools import LangChainToolAdapter

        read_tool = ReadTool()
        lc_tool = LangChainToolAdapter(forge_tool=read_tool)

        # Now usable with LangChain agents
        result = lc_tool.invoke({"file_path": "/path/to/file"})
        ```
    """

    forge_tool: Any  # Code-Forge BaseTool
    executor: Any = None  # Optional ToolExecutor
    context: Any = None  # Optional ExecutionContext

    # Required fields for LangChain BaseTool - we'll set dynamically
    name: str = ""
    description: str = ""

    # args_schema will be set dynamically in __init__
    args_schema: type[BaseModel] | None = None

    model_config: ClassVar[dict[str, Any]] = {"arbitrary_types_allowed": True}  # type: ignore[assignment]

    def __init__(self, **data: Any) -> None:
        """Initialize adapter with Code-Forge tool."""
        super().__init__(**data)
        # Set name and description from wrapped tool
        if self.forge_tool:
            object.__setattr__(self, "name", self.forge_tool.name)
            object.__setattr__(self, "description", self.forge_tool.description)
            # Generate args_schema from parameters
            object.__setattr__(self, "args_schema", self._generate_args_schema())

    def _generate_args_schema(self) -> type[BaseModel]:
        """
        Generate Pydantic model from Code-Forge tool parameters.

        Returns:
            Dynamically created Pydantic model for arguments
        """
        fields: dict[str, Any] = {}
        for param in self.forge_tool.parameters:
            # Map Code-Forge types to Python types
            type_map: dict[str, type] = {
                "string": str,
                "integer": int,
                "number": float,
                "boolean": bool,
                "array": list,
                "object": dict,
            }
            python_type = type_map.get(param.type, str)

            # Create field with or without default
            if param.required:
                fields[param.name] = (
                    python_type,
                    Field(description=param.description),
                )
            else:
                fields[param.name] = (
                    python_type | None,
                    Field(default=param.default, description=param.description),
                )

        # Create dynamic model
        model_name = f"{self.forge_tool.name.title().replace('_', '')}Args"
        return create_model(model_name, **fields)

    def _run(self, **kwargs: Any) -> str:
        """
        Execute tool synchronously.

        Args:
            **kwargs: Tool arguments

        Returns:
            Tool result as string
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None:
            # We're in an async context, create a new thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._arun(**kwargs))
                return future.result()
        else:
            return asyncio.run(self._arun(**kwargs))

    async def _arun(self, **kwargs: Any) -> str:
        """
        Execute tool asynchronously.

        Args:
            **kwargs: Tool arguments

        Returns:
            Tool result as string
        """
        from code_forge.tools.base import ExecutionContext

        # Get or create context
        context = self.context
        if context is None:
            context = ExecutionContext(working_dir=str(Path.cwd()))

        # Execute tool directly (not through executor to avoid naming issues)
        result = await self.forge_tool.execute(context, **kwargs)

        # Format result
        if result.success:
            if isinstance(result.output, str):
                return result.output
            return json.dumps(result.output, indent=2)
        else:
            return f"Error: {result.error}"


class CodeForgeToolAdapter:
    """
    Adapts a LangChain tool to Code-Forge's BaseTool interface.

    This allows existing LangChain tools to be used within Code-Forge's
    tool system.

    Example:
        ```python
        from langchain_community.tools import WikipediaQueryRun
        from code_forge.langchain.tools import CodeForgeToolAdapter

        wiki_tool = WikipediaQueryRun()
        forge_tool = CodeForgeToolAdapter(langchain_tool=wiki_tool)

        # Now usable with Code-Forge
        result = await tool_executor.execute(forge_tool, {"query": "Python"}, ctx)
        ```
    """

    def __init__(self, langchain_tool: LangChainBaseTool) -> None:
        """
        Initialize adapter.

        Args:
            langchain_tool: LangChain tool to wrap
        """
        self.langchain_tool = langchain_tool
        self._parameters = self._extract_parameters()

    @property
    def name(self) -> str:
        """Return tool name."""
        return self.langchain_tool.name

    @property
    def description(self) -> str:
        """Return tool description."""
        return self.langchain_tool.description

    @property
    def category(self) -> str:
        """Return tool category."""
        from code_forge.tools.base import ToolCategory

        return ToolCategory.OTHER

    @property
    def parameters(self) -> list[Any]:
        """Return tool parameters."""
        return self._parameters

    @property
    def requires_confirmation(self) -> bool:
        """Whether tool requires user confirmation."""
        return False

    def _extract_parameters(self) -> list[Any]:
        """Extract parameters from LangChain tool schema."""
        from code_forge.tools.base import ToolParameter

        params = []
        schema = getattr(self.langchain_tool, "args_schema", None)

        if schema:
            json_schema = schema.model_json_schema()
            properties = json_schema.get("properties", {})
            required = json_schema.get("required", [])

            for name, prop in properties.items():
                params.append(
                    ToolParameter(
                        name=name,
                        type=prop.get("type", "string"),
                        description=prop.get("description", ""),
                        required=name in required,
                        default=prop.get("default"),
                    )
                )

        return params

    async def execute(self, params: dict[str, Any], context: Any) -> Any:
        """
        Execute the LangChain tool.

        Args:
            params: Tool parameters
            context: Execution context

        Returns:
            ToolResult with execution output
        """
        from code_forge.tools.base import ToolResult

        try:
            # Try async first
            if hasattr(self.langchain_tool, "ainvoke"):
                output = await self.langchain_tool.ainvoke(params)
            else:
                # Fall back to sync
                output = self.langchain_tool.invoke(params)

            return ToolResult(
                success=True,
                output=output,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
            )

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function calling schema."""
        schema = getattr(self.langchain_tool, "args_schema", None)
        params: dict[str, Any] = {}
        if schema:
            params = schema.model_json_schema()

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": params,
            },
        }


def adapt_tools_for_langchain(
    tools: list[Any],
    executor: Any = None,
    context: Any = None,
) -> list[LangChainBaseTool]:
    """
    Convert a list of Code-Forge tools to LangChain tools.

    Args:
        tools: List of Code-Forge BaseTool instances
        executor: Optional ToolExecutor to use
        context: Optional ExecutionContext to use

    Returns:
        List of LangChain-compatible tools
    """
    return [
        LangChainToolAdapter(
            forge_tool=tool,
            executor=executor,
            context=context,
        )
        for tool in tools
    ]


def adapt_tools_for_forge(tools: list[LangChainBaseTool]) -> list[CodeForgeToolAdapter]:
    """
    Convert a list of LangChain tools to Code-Forge tools.

    Args:
        tools: List of LangChain tools

    Returns:
        List of Code-Forge-compatible tools
    """
    return [CodeForgeToolAdapter(langchain_tool=tool) for tool in tools]
