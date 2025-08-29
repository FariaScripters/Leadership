from typing import Dict, Any, List
import json
import asyncio
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class MCPServer:
    """Model Context Protocol Server interface"""
    
    def __init__(self, server_name: str):
        self.settings = get_settings()
        self.server_name = server_name
        self.process = None
        
    async def start(self):
        """Start the MCP server process"""
        if self.process:
            return
            
        try:
            # Get server config
            config = self.settings.mcp_servers.get(self.server_name)
            if not config:
                raise ValueError(f"No configuration found for MCP server: {self.server_name}")
                
            # Create process
            self.process = await asyncio.create_subprocess_exec(
                config["command"],
                *config["args"],
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            logger.info(f"Started MCP server: {self.server_name}")
            
        except Exception as e:
            logger.error(f"Failed to start MCP server {self.server_name}: {str(e)}")
            raise
            
    async def stop(self):
        """Stop the MCP server process"""
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
                self.process = None
                logger.info(f"Stopped MCP server: {self.server_name}")
            except Exception as e:
                logger.error(f"Error stopping MCP server {self.server_name}: {str(e)}")
                
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to MCP server
        
        Args:
            request: Request dictionary to send
            
        Returns:
            Response from server
        """
        if not self.process:
            await self.start()
            
        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()
            
            # Get response
            response_line = await self.process.stdout.readline()
            if not response_line:
                raise Exception("No response from server")
                
            # Parse response
            response = json.loads(response_line)
            return response
            
        except Exception as e:
            logger.error(f"Error in MCP server {self.server_name}: {str(e)}")
            # Try to restart server
            await self.stop()
            await self.start()
            raise

class SequentialThinkingMCP(MCPServer):
    """Sequential Thinking MCP implementation"""
    
    def __init__(self):
        super().__init__("sequentialthinking")
        
    async def process_thought(self, context: str, query: str) -> List[str]:
        """Process a thought sequence
        
        Args:
            context: Context for the thought process
            query: Query to process
            
        Returns:
            List of thought steps
        """
        request = {
            "context": context,
            "query": query,
            "type": "thought_sequence"
        }
        
        response = await self.send_request(request)
        return response.get("thoughts", [])
