from typing import Dict, Any, List, Optional
from app.infrastructure.external.mcp.sequential_thinking import MCPServer
import logging

logger = logging.getLogger(__name__)

class PlaywrightMCP(MCPServer):
    """Playwright MCP implementation for browser automation"""
    
    def __init__(self):
        super().__init__("playwright-mcp")
        
    async def navigate(self, url: str, wait_for_load: bool = True) -> Dict[str, Any]:
        """Navigate to a URL
        
        Args:
            url: URL to navigate to
            wait_for_load: Whether to wait for page load
            
        Returns:
            Navigation result
        """
        request = {
            "type": "navigate",
            "url": url,
            "waitForLoad": wait_for_load
        }
        
        return await self.send_request(request)
        
    async def click(self, selector: str) -> Dict[str, Any]:
        """Click an element
        
        Args:
            selector: Element selector
            
        Returns:
            Click operation result
        """
        request = {
            "type": "click",
            "selector": selector
        }
        
        return await self.send_request(request)
        
    async def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        """Type text into an element
        
        Args:
            selector: Element selector
            text: Text to type
            
        Returns:
            Type operation result
        """
        request = {
            "type": "type",
            "selector": selector,
            "text": text
        }
        
        return await self.send_request(request)
        
    async def get_text(self, selector: str) -> Optional[str]:
        """Get text content of an element
        
        Args:
            selector: Element selector
            
        Returns:
            Element text content
        """
        request = {
            "type": "getText",
            "selector": selector
        }
        
        response = await self.send_request(request)
        return response.get("text")
        
    async def screenshot(self, selector: Optional[str] = None) -> Optional[str]:
        """Take a screenshot
        
        Args:
            selector: Optional element selector to screenshot
            
        Returns:
            Base64 encoded screenshot data
        """
        request = {
            "type": "screenshot",
            "selector": selector
        }
        
        response = await self.send_request(request)
        return response.get("data")
