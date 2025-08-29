from typing import Protocol, Dict, Any, Optional, List, AsyncIterator
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime

@dataclass
class BrowserCapabilities:
    """Browser provider capabilities"""
    name: str
    version: str
    supports_cdp: bool
    supports_mcp: bool
    private_deployment: bool
    features: List[str]

@dataclass
class BrowserConfig:
    """Browser configuration"""
    headless: bool = True
    private_deployment: bool = True
    user_data_dir: Optional[str] = None
    extra_args: List[str] = None
    mcp_endpoint: Optional[str] = None
    proxy_config: Optional[Dict[str, Any]] = None

class BrowserProtocol(Protocol):
    """Base protocol for browser providers"""
    
    @abstractmethod
    async def get_capabilities(self) -> BrowserCapabilities:
        """Get browser capabilities"""
        pass
        
    @abstractmethod
    async def launch(self, config: BrowserConfig):
        """Launch browser instance"""
        pass
        
    @abstractmethod
    async def new_page(self) -> 'PageProtocol':
        """Create new page"""
        pass
        
    @abstractmethod
    async def close(self):
        """Close browser instance"""
        pass
        
    @abstractmethod
    async def connect_to_mcp(self, endpoint: str):
        """Connect to MCP server"""
        pass

class PageProtocol(Protocol):
    """Base protocol for page interactions"""
    
    @abstractmethod
    async def goto(self, url: str):
        """Navigate to URL"""
        pass
        
    @abstractmethod
    async def evaluate(self, script: str) -> Any:
        """Evaluate JavaScript"""
        pass
        
    @abstractmethod
    async def get_content(self) -> str:
        """Get page content"""
        pass
        
    @abstractmethod
    async def close(self):
        """Close page"""
        pass
        
    @abstractmethod
    async def screenshot(self) -> bytes:
        """Take screenshot"""
        pass
        
    @abstractmethod
    async def wait_for_selector(self, selector: str):
        """Wait for element"""
        pass

class MCPBrowserProvider:
    """MCP-based browser provider"""
    
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        
    async def create_browser(self, config: BrowserConfig) -> BrowserProtocol:
        """Create browser through MCP"""
        # Connect to MCP server
        if config.mcp_endpoint:
            await self.mcp_client.connect(config.mcp_endpoint)
            
        # Request browser instance
        browser_id = await self.mcp_client.send_command(
            "browser.create",
            {
                "headless": config.headless,
                "privateDeployment": config.private_deployment
            }
        )
        
        return MCPBrowser(self.mcp_client, browser_id)

class MCPBrowser:
    """MCP browser implementation"""
    
    def __init__(self, mcp_client, browser_id: str):
        self.mcp_client = mcp_client
        self.browser_id = browser_id
        self._pages: Dict[str, 'MCPPage'] = {}
        
    async def get_capabilities(self) -> BrowserCapabilities:
        result = await self.mcp_client.send_command(
            "browser.getCapabilities",
            {"browserId": self.browser_id}
        )
        return BrowserCapabilities(**result)
        
    async def new_page(self) -> 'MCPPage':
        page_id = await self.mcp_client.send_command(
            "browser.newPage",
            {"browserId": self.browser_id}
        )
        page = MCPPage(self.mcp_client, page_id)
        self._pages[page_id] = page
        return page
        
    async def close(self):
        for page in list(self._pages.values()):
            await page.close()
        await self.mcp_client.send_command(
            "browser.close",
            {"browserId": self.browser_id}
        )
        
    async def connect_to_mcp(self, endpoint: str):
        await self.mcp_client.connect(endpoint)

class MCPPage:
    """MCP page implementation"""
    
    def __init__(self, mcp_client, page_id: str):
        self.mcp_client = mcp_client
        self.page_id = page_id
        
    async def goto(self, url: str):
        await self.mcp_client.send_command(
            "page.goto",
            {
                "pageId": self.page_id,
                "url": url
            }
        )
        
    async def evaluate(self, script: str) -> Any:
        result = await self.mcp_client.send_command(
            "page.evaluate",
            {
                "pageId": self.page_id,
                "script": script
            }
        )
        return result.get("value")
        
    async def get_content(self) -> str:
        result = await self.mcp_client.send_command(
            "page.content",
            {"pageId": self.page_id}
        )
        return result["content"]
        
    async def close(self):
        await self.mcp_client.send_command(
            "page.close",
            {"pageId": self.page_id}
        )
        
    async def screenshot(self) -> bytes:
        result = await self.mcp_client.send_command(
            "page.screenshot",
            {"pageId": self.page_id}
        )
        return result["data"]
        
    async def wait_for_selector(self, selector: str):
        await self.mcp_client.send_command(
            "page.waitForSelector",
            {
                "pageId": self.page_id,
                "selector": selector
            }
        )
