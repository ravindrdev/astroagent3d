"""Core agent loop using Claude's tool-use API."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import anthropic

from astroagent.agent.prompts import SYSTEM_PROMPT
from astroagent.tools.anomaly_detector import DetectAnomalies
from astroagent.tools.base import ToolRegistry
from astroagent.tools.exoplanet_archive import QueryExoplanetArchive
from astroagent.tools.galaxy_map import QueryGalaxyMap
from astroagent.tools.habitable_zone import CalculateHabitableZone
from astroagent.tools.light_curves import FetchLightCurve
from astroagent.tools.sdss_query import SearchSDSS
from astroagent.viz.galaxy_renderer import GalaxyMapRenderer
from astroagent.viz.jupyter_widget import display_light_curve, display_orbit_viewer


@dataclass
class AgentStep:
    """A single step in the agent's reasoning process."""

    type: str
    content: str
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_result: dict[str, Any] | None = None


@dataclass
class AgentResponse:
    """Complete response from the agent including reasoning steps and final answer."""

    text: str
    steps: list[AgentStep] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    visualizations: list[dict[str, Any]] = field(default_factory=list)


class AstroAgent:
    """AI-powered astronomical research agent.

    Uses Claude's tool-calling to autonomously query NASA databases,
    analyze data, and generate interactive 3D visualizations of
    planetary systems.

    Usage:
        agent = AstroAgent()
        result = agent.ask("Show me the TRAPPIST-1 system")
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        api_key: str | None = None,
        max_iterations: int = 10,
        verbose: bool = True,
    ) -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_iterations = max_iterations
        self._verbose = verbose
        self._conversation: list[dict[str, Any]] = []
        self._registry = ToolRegistry()
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        self._registry.register(QueryExoplanetArchive())
        self._registry.register(FetchLightCurve())
        self._registry.register(CalculateHabitableZone())
        self._registry.register(DetectAnomalies())
        self._registry.register(SearchSDSS())
        self._registry.register(QueryGalaxyMap())

    def ask(self, query: str) -> AgentResponse:
        """Send a natural language query to the agent and get a response.

        The agent will autonomously decide which tools to call,
        retrieve real data from NASA APIs, and generate visualizations
        when appropriate.
        """
        self._conversation.append({"role": "user", "content": query})
        steps: list[AgentStep] = []
        collected_data: dict[str, Any] = {}
        visualizations: list[dict[str, Any]] = []

        for iteration in range(self._max_iterations):
            response = self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=self._registry.get_claude_tools(),
                messages=self._conversation,
            )

            if response.stop_reason == "end_turn":
                text = self._extract_text(response)
                self._conversation.append({"role": "assistant", "content": response.content})
                steps.append(AgentStep(type="response", content=text))
                if self._verbose:
                    self._print_step("done", f"Completed in {iteration + 1} iteration(s)")
                return AgentResponse(text=text, steps=steps, data=collected_data, visualizations=visualizations)

            if response.stop_reason == "tool_use":
                self._conversation.append({"role": "assistant", "content": response.content})
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input

                        if self._verbose:
                            self._print_step(
                                "tool",
                                f"Calling: {tool_name}({json.dumps(tool_input, default=str)[:80]})",
                            )

                        steps.append(
                            AgentStep(
                                type="tool_call",
                                content=f"Calling {tool_name}",
                                tool_name=tool_name,
                                tool_input=tool_input,
                            )
                        )

                        try:
                            result = self._registry.execute(tool_name, tool_input)
                        except Exception as e:
                            result = {"error": str(e)}

                        collected_data[tool_name] = result
                        steps.append(
                            AgentStep(
                                type="tool_result",
                                content=self._summarize_result(result),
                                tool_name=tool_name,
                                tool_result=result,
                            )
                        )

                        if self._verbose:
                            self._print_step("data", self._summarize_result(result))

                        viz = self._check_for_visualization(tool_name, result)
                        if viz:
                            visualizations.append(viz)

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result, default=str),
                            }
                        )

                self._conversation.append({"role": "user", "content": tool_results})

        final_text = "Reached maximum iterations. Here is what I found so far."
        return AgentResponse(text=final_text, steps=steps, data=collected_data, visualizations=visualizations)

    def _check_for_visualization(self, tool_name: str, result: dict[str, Any]) -> dict[str, Any] | None:
        """Auto-detect when a visualization should be rendered."""
        if tool_name == "query_exoplanet_archive" and result.get("count", 0) > 0:
            planets = result.get("planets", [])
            if planets and planets[0].get("semi_major_axis_au") is not None:
                try:
                    display_orbit_viewer(planets)
                except Exception:
                    pass
                return {"type": "orbit_3d", "data": planets}

        if tool_name == "fetch_light_curve" and result.get("data_points"):
            try:
                display_light_curve(
                    result["data_points"],
                    title=(f"{result.get('target', 'Unknown')} - {result.get('mission', '')} Light Curve"),
                )
            except Exception:
                pass
            return {"type": "light_curve", "data": result["data_points"]}

        if tool_name == "query_galaxy_map" and result.get("count", 0) > 0:
            planets = result.get("planets", [])
            try:
                galaxy_renderer = GalaxyMapRenderer()
                galaxy_renderer.render_to_file(
                    planets,
                    "galaxy_map.html",
                    stats=result.get("stats"),
                )
                if self._verbose:
                    self._print_step(
                        "viz",
                        f"Galaxy map saved: galaxy_map.html ({len(planets)} planets)",
                    )
            except Exception:
                pass
            return {"type": "galaxy_map", "count": len(planets)}

        return None

    def _extract_text(self, response: anthropic.types.Message) -> str:
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts)

    def _summarize_result(self, result: dict[str, Any]) -> str:
        if "error" in result:
            return f"Error: {result['error']}"
        if "count" in result:
            return f"Received: {result['count']} results"
        if "data_points_returned" in result:
            return f"Received: {result['data_points_returned']} data points"
        if "habitable_zone" in result:
            hz = result["habitable_zone"]["conservative"]
            return f"Received: HZ inner={hz['inner_au']} AU, outer={hz['outer_au']} AU"
        if "total_anomalies" in result:
            return f"Received: {result['total_anomalies']} anomalies detected"
        return f"Received: {len(json.dumps(result, default=str))} bytes"

    def _print_step(self, step_type: str, message: str) -> None:
        icons = {
            "think": "✨",
            "tool": "⚒️",
            "data": "📡",
            "viz": "🌌",
            "done": "✅",
        }
        icon = icons.get(step_type, "▶")
        print(f"  {icon} {message}")

    def reset(self) -> None:
        """Clear the conversation history to start fresh."""
        self._conversation.clear()

    @property
    def tools(self) -> list[str]:
        """List available tool names."""
        return self._registry.tool_names

    @property
    def conversation_length(self) -> int:
        return len(self._conversation)
