"""Base class for all astronomy tools that the agent can invoke."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class AstroTool(ABC):
    """Base class for tools the AstroAgent can call via Claude's tool-use API."""

    name: str
    description: str
    input_schema: type[BaseModel]

    def to_claude_tool(self) -> dict[str, Any]:
        """Convert this tool to Claude's tool-use format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema.model_json_schema(),
        }

    @abstractmethod
    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool with the given parameters and return results."""

    def __repr__(self) -> str:
        return f"<AstroTool:{self.name}>"


class ToolRegistry:
    """Registry of available tools for the agent."""

    def __init__(self) -> None:
        self._tools: dict[str, AstroTool] = {}

    def register(self, tool: AstroTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> AstroTool:
        if name not in self._tools:
            available = ", ".join(self._tools.keys())
            raise KeyError(f"Unknown tool '{name}'. Available: {available}")
        return self._tools[name]

    def get_claude_tools(self) -> list[dict[str, Any]]:
        """Return all tools in Claude's expected format."""
        return [tool.to_claude_tool() for tool in self._tools.values()]

    def execute(self, name: str, arguments: str | dict[str, Any]) -> dict[str, Any]:
        """Look up a tool by name and execute it."""
        tool = self.get(name)
        if isinstance(arguments, str):
            arguments = json.loads(arguments)
        validated = tool.input_schema.model_validate(arguments)
        return tool.execute(**validated.model_dump())

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)
