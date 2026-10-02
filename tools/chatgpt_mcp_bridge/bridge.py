"""Multiplex the MCP servers in Homesteader's .mcp.json over one stdio server."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, ListToolsResult, PaginatedRequestParams, TextContent, Tool


LOGGER = logging.getLogger("homesteader-mcp-bridge")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / ".mcp.json"
ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")
MESHY_GENERATION_MARKERS = (
    "text_to_3d",
    "image_to_3d",
    "multi_image_to_3d",
    "text_to_image",
    "image_to_image",
    "retexture",
    "remesh",
    "refine",
    "animate",
    "creative_lab",
)


def expand_env(value: str) -> str:
    """Expand ${NAME} and ${NAME:-default} without logging the result."""

    def replace(match: re.Match[str]) -> str:
        name, default = match.groups()
        return os.environ.get(name, default or "")

    return ENV_PATTERN.sub(replace, value)


def tool_is_allowed(server_name: str, tool: Tool) -> bool:
    """Hide generic Meshy generation paths that bypass Homesteader's required pipeline."""
    if server_name.casefold() != "meshy":
        return True
    if any(marker in tool.name.casefold() for marker in MESHY_GENERATION_MARKERS):
        return False
    annotations = tool.annotations
    return tool.name.casefold() == "meshy_get_balance" or bool(
        annotations and annotations.readOnlyHint is True
    )


def tool_for_gateway(server_name: str, tool: Tool) -> Tool:
    data = tool.model_dump(by_alias=True, exclude_none=True)
    data["name"] = f"{server_name}__{tool.name}"
    prefix = f"From the {server_name} MCP server."
    data["description"] = f"{prefix} {tool.description or ''}".strip()
    return Tool(**data)


class Backend:
    def __init__(self, name: str, config: dict[str, Any], stack: AsyncExitStack):
        self.name = name
        self.config = config
        self.stack = stack
        self.session: ClientSession | None = None
        self.lock = asyncio.Lock()

    async def connect(self) -> ClientSession:
        async with self.lock:
            if self.session is not None:
                return self.session

            server_type = self.config.get("type", "stdio").casefold()
            if server_type in {"http", "streamable-http", "streamable_http"}:
                url = expand_env(str(self.config["url"]))
                transport = streamable_http_client(url, http_client=None)
                read_stream, write_stream, _ = await self.stack.enter_async_context(transport)
            elif server_type == "stdio":
                command = expand_env(str(self.config["command"]))
                args = [expand_env(str(value)) for value in self.config.get("args", [])]
                child_env = os.environ.copy()
                child_env.update(
                    {
                        str(key): expand_env(str(value))
                        for key, value in (self.config.get("env") or {}).items()
                    }
                )
                parameters = StdioServerParameters(
                    command=command,
                    args=args,
                    env=child_env,
                    cwd=self.config.get("cwd"),
                )
                read_stream, write_stream = await self.stack.enter_async_context(
                    stdio_client(parameters)
                )
            else:
                raise ValueError(f"Unsupported transport type: {server_type}")

            session = await self.stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()
            self.session = session
            LOGGER.info("Connected to MCP server '%s'", self.name)
            return session


class Bridge:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.stack = AsyncExitStack()
        self.backends: dict[str, Backend] = {}
        self.tool_routes: dict[str, tuple[str, str]] = {}
        self.refresh_lock = asyncio.Lock()

        raw = json.loads(config_path.read_text(encoding="utf-8-sig"))
        servers = raw.get("mcpServers")
        if not isinstance(servers, dict) or not servers:
            raise ValueError("The MCP config must contain a non-empty mcpServers object.")
        for name, config in servers.items():
            if isinstance(config, dict):
                self.backends[name] = Backend(name, config, self.stack)

        self.server = Server(
            name="homesteader-mcp-bridge",
            version="1.0.0",
            description="Proxy for the MCP servers configured by the Homesteader project.",
            on_list_tools=self.list_tools,
            on_call_tool=self.call_tool,
        )

    async def start(self) -> None:
        await self.stack.__aenter__()

    async def close(self) -> None:
        await self.stack.aclose()

    async def serve_stdio(self) -> None:
        await self.start()
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options(),
                )
        finally:
            await self.close()

    async def list_tools(self, _context: Any, _params: Any) -> ListToolsResult:
        async with self.refresh_lock:
            tools: list[Tool] = []
            routes: dict[str, tuple[str, str, bool]] = {}
            for server_name, backend in self.backends.items():
                try:
                    session = await backend.connect()
                    result = await session.list_tools()
                except Exception:  # A disconnected editor/backend should not hide other tools.
                    LOGGER.warning("Could not load tools from '%s' (%s)", server_name, type(exc).__name__)
                    continue

                while True:
                    for original_tool in result.tools:
                        if not tool_is_allowed(server_name, original_tool):
                            continue
                        exposed_tool = tool_for_gateway(server_name, original_tool)
                        if exposed_tool.name in routes:
                            LOGGER.warning("Skipping duplicate exposed tool name '%s'", exposed_tool.name)
                            continue
                        routes[exposed_tool.name] = (server_name, original_tool.name)
                        tools.append(exposed_tool)
                    if not result.next_cursor:
                        break
                    result = await session.list_tools(
                        params=PaginatedRequestParams(cursor=result.next_cursor)
                    )

            self.tool_routes = routes
            return ListToolsResult(tools=tools)

    async def call_tool(self, _context: Any, params: Any) -> CallToolResult:
        route = self.tool_routes.get(params.name)
        if route is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Unknown tool. Refresh the tool list and retry.")],
                isError=True,
            )

        server_name, original_name = route
        arguments = dict(params.arguments or {})
        try:
            session = await self.backends[server_name].connect()
            result = await session.call_tool(
                original_name,
                arguments,
                allow_input_required=True,
                allow_claimed=True,
            )
            if isinstance(result, CallToolResult):
                return result
            return CallToolResult(
                content=[TextContent(type="text", text=result.model_dump_json(by_alias=True))],
                isError=False,
            )
        except Exception as exc:
            LOGGER.warning("Tool call failed for '%s' (%s)", params.name, type(exc).__name__)
            return CallToolResult(
                content=[TextContent(type="text", text="Tool call failed. Check the local bridge log for details.")],
                isError=True,
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(os.environ.get("HOMESTEADER_MCP_CONFIG", DEFAULT_CONFIG)),
    )
    args = parser.parse_args()

    if not args.config.is_file():
        parser.error(f"MCP config not found: {args.config}")

    bridge = Bridge(args.config.resolve())
    logging.basicConfig(level=os.environ.get("HOMESTEADER_MCP_BRIDGE_LOG_LEVEL", "INFO"))
    try:
        asyncio.run(bridge.serve_stdio())
    except KeyboardInterrupt:
        LOGGER.info("Bridge stopped")


if __name__ == "__main__":
    main()
