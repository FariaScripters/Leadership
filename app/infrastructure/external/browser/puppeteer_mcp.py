from typing import Dict, Any, List, Optional
from app.infrastructure.external.mcp.sequential_thinking import MCPServer
from app.infrastructure.external.browser.cdp_connection import CDPConnectionManager
import logging
import json
import base64

logger = logging.getLogger(__name__)

class BrowserMCP(MCPServer):
    """Base Browser MCP implementation with CDP support"""
    
    def __init__(self, server_name: str):
        super().__init__(server_name)
        self.cdp = CDPConnectionManager()
        
    async def initialize(self):
        """Initialize browser connection"""
        await super().initialize()
        await self.cdp.connect()
        
    async def cleanup(self):
        """Clean up browser connection"""
        await self.cdp.disconnect()
        await super().cleanup()
        
    async def _evaluate(self, expression: str) -> Any:
        """Evaluate JavaScript expression
        
        Args:
            expression: JavaScript expression to evaluate
            
        Returns:
            Evaluation result
        """
        result = await self.cdp.send_command(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True
            }
        )
        return result.get("result", {}).get("value")

class PuppeteerMCP(BrowserMCP):
    """Puppeteer MCP implementation"""
    
    def __init__(self):
        super().__init__("puppeteer")
        
    async def navigate(self, url: str, wait_until: str = "networkidle0") -> Dict[str, Any]:
        """Navigate to URL
        
        Args:
            url: URL to navigate to
            wait_until: Navigation wait condition
            
        Returns:
            Navigation result
        """
        result = await self.cdp.send_command(
            "Page.navigate",
            {"url": url}
        )
        
        if wait_until == "networkidle0":
            # Wait for network to be idle
            await self.cdp.send_command(
                "Runtime.evaluate",
                {
                    "expression": """
                    new Promise(resolve => {
                        if (document.readyState === 'complete') {
                            resolve();
                        } else {
                            window.addEventListener('load', resolve);
                        }
                    })
                    """
                }
            )
            
        return result
        
    async def click(self, selector: str) -> None:
        """Click element
        
        Args:
            selector: Element selector
        """
        await self._evaluate(f"""
            document.querySelector("{selector}").click()
        """)
        
    async def type(self, selector: str, text: str) -> None:
        """Type text into element
        
        Args:
            selector: Element selector
            text: Text to type
        """
        await self._evaluate(f"""
            const el = document.querySelector("{selector}");
            el.value = "{text}";
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
        """)
        
    async def screenshot(self, clip: Optional[Dict[str, int]] = None) -> str:
        """Take screenshot
        
        Args:
            clip: Optional viewport clip rectangle
            
        Returns:
            Base64 encoded screenshot
        """
        options = {"format": "png"}
        if clip:
            options["clip"] = clip
            
        result = await self.cdp.send_command("Page.captureScreenshot", options)
        return result.get("data", "")
