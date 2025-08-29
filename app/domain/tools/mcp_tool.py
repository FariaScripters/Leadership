from typing import Dict, Any, Optional, List
import logging
import asyncio
from app.core.agent import Tool, ToolCapability, ToolContext, ToolType
from app.infrastructure.external.mcp.client import MCPClient

logger = logging.getLogger(__name__)

class MCPTool(Tool):
    """MCP protocol tool integration"""
    
    def __init__(self):
        self.context: Optional[ToolContext] = None
        self.client: Optional[MCPClient] = None
        self.connected_tools: Dict[str, Dict[str, Any]] = {}
        
    def get_capabilities(self) -> ToolCapability:
        return ToolCapability(
            name="mcp",
            type=ToolType.MCP,
            description="MCP protocol integration for external tools",
            private=True,
            requires_auth=True,
            sandbox=True
        )
        
    async def initialize(self, context: ToolContext):
        """Initialize MCP client"""
        self.context = context
        self.client = MCPClient()
        
    async def execute(self, command: str, params: Dict[str, Any]) -> Any:
        """Execute MCP command"""
        if not self.client:
            raise RuntimeError("MCP client not initialized")
            
        if command == "connect":
            # Connect to MCP server
            await self.client.connect(params["endpoint"])
            return {"success": True}
            
        elif command == "discover_tools":
            # Discover available tools
            tools = await self.client.send_command("system.listTools")
            return {"tools": tools}
            
        elif command == "attach_tool":
            # Attach to external tool
            tool_id = params["tool_id"]
            response = await self.client.send_command(
                "tool.attach",
                {"toolId": tool_id}
            )
            self.connected_tools[tool_id] = response
            return response
            
        elif command == "execute_tool":
            # Execute command on attached tool
            tool_id = params["tool_id"]
            if tool_id not in self.connected_tools:
                raise ValueError(f"Tool {tool_id} not attached")
                
            return await self.client.send_command(
                "tool.execute",
                {
                    "toolId": tool_id,
                    "command": params["command"],
                    "params": params.get("params", {})
                }
            )
            
        elif command == "detach_tool":
            # Detach from tool
            tool_id = params["tool_id"]
            if tool_id in self.connected_tools:
                await self.client.send_command(
                    "tool.detach",
                    {"toolId": tool_id}
                )
                del self.connected_tools[tool_id]
            return {"success": True}
            
        else:
            raise ValueError(f"Unknown command: {command}")
            
    async def cleanup(self):
        """Cleanup MCP connection"""
        if self.client:
            # Detach from all tools
            for tool_id in list(self.connected_tools.keys()):
                try:
                    await self.client.send_command(
                        "tool.detach",
                        {"toolId": tool_id}
                    )
                except:
                    pass
            self.connected_tools.clear()
            
            # Disconnect client
            await self.client.disconnect()
            self.client = None
