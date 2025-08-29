from typing import Dict, Any, Optional
import logging
from app.core.agent import Tool, ToolCapability, ToolContext, ToolType
from app.infrastructure.external.browser.factory import browser_factory
from app.infrastructure.external.browser.protocol import BrowserProtocol, BrowserConfig

logger = logging.getLogger(__name__)

class BrowserTool(Tool):
    """Browser automation tool with takeover support"""
    
    def __init__(self):
        self.context: Optional[ToolContext] = None
        self.browser: Optional[BrowserProtocol] = None
        self.current_page_id: Optional[str] = None
        
    def get_capabilities(self) -> ToolCapability:
        return ToolCapability(
            name="browser",
            type=ToolType.BROWSER,
            description="Browser automation with takeover support",
            private=True,
            requires_auth=True,
            sandbox=True
        )
        
    async def initialize(self, context: ToolContext):
        """Initialize browser in sandbox"""
        self.context = context
        
        # Check if we should connect to existing browser
        takeover_url = context.params.get("takeover_url")
        if takeover_url:
            # Connect to existing browser via MCP
            self.browser = await browser_factory.create_browser(
                provider="mcp",
                config=BrowserConfig(
                    mcp_endpoint=takeover_url,
                    private_deployment=False
                )
            )
        else:
            # Launch new browser
            self.browser = await browser_factory.create_browser(
                provider="cdp",
                config=BrowserConfig(
                    headless=True,
                    private_deployment=True,
                    user_data_dir=f"{context.workspace}/browser_data"
                )
            )
            
    async def execute(self, command: str, params: Dict[str, Any]) -> Any:
        """Execute browser command"""
        if not self.browser:
            raise RuntimeError("Browser not initialized")
            
        if command == "new_page":
            page = await self.browser.new_page()
            return {"success": True}
            
        elif command == "goto":
            page = await self.browser.new_page()
            await page.goto(params["url"])
            return {"success": True}
            
        elif command == "evaluate":
            page = await self.browser.new_page()
            result = await page.evaluate(params["script"])
            return {"result": result}
            
        elif command == "screenshot":
            page = await self.browser.new_page()
            screenshot = await page.screenshot()
            # Save screenshot in workspace
            screenshot_path = f"{self.context.workspace}/screenshot.png"
            with open(screenshot_path, "wb") as f:
                f.write(screenshot)
            return {"path": screenshot_path}
            
        elif command == "expose_cdp":
            # Get CDP endpoint for takeover
            if hasattr(self.browser, "connection"):
                return {
                    "wsEndpoint": self.browser.connection.ws_url
                }
            return {"error": "Browser does not support CDP exposure"}
            
        else:
            raise ValueError(f"Unknown command: {command}")
            
    async def cleanup(self):
        """Cleanup browser"""
        if self.browser:
            await self.browser.close()
            self.browser = None
