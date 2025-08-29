from typing import Dict, Any, Optional, List
import asyncio
import logging
from .protocol import BrowserProtocol, PageProtocol, BrowserConfig, BrowserCapabilities
from .cdp.connection import CDPConnection
from .cdp.session import CDPSession, TargetInfo
from .cdp.page import Page
from .cdp.launcher import ChromeLauncher

logger = logging.getLogger(__name__)

class CDPBrowserProvider:
    """Built-in CDP-based browser provider"""
    
    async def create_browser(self, config: BrowserConfig) -> BrowserProtocol:
        """Create CDP browser instance"""
        launcher = ChromeLauncher()
        connection = await launcher.launch(
            headless=config.headless,
            user_data_dir=config.user_data_dir,
            extra_args=config.extra_args
        )
        return CDPBrowser(connection)

class CDPBrowser(BrowserProtocol):
    """CDP browser implementation"""
    
    def __init__(self, connection: CDPConnection):
        self.connection = connection
        self._targets: Dict[str, TargetInfo] = {}
        self._sessions: Dict[str, CDPSession] = {}
        self._pages: Dict[str, CDPPage] = {}
        
    async def get_capabilities(self) -> BrowserCapabilities:
        return BrowserCapabilities(
            name="Chrome",
            version=await self._get_version(),
            supports_cdp=True,
            supports_mcp=False,
            private_deployment=True,
            features=["cdp", "screenshots", "js_evaluation"]
        )
        
    async def _get_version(self) -> str:
        result = await self.connection.send_command("Browser.getVersion")
        return result.get("product", "Chrome")
        
    async def launch(self, config: BrowserConfig):
        await self._setup_target_discovery()
        
    async def _setup_target_discovery(self):
        async def on_target_created(params: Dict[str, Any]):
            target_info = params["targetInfo"]
            target = TargetInfo(
                target_id=target_info["targetId"],
                type=target_info["type"],
                title=target_info["title"],
                url=target_info["url"],
                attached=target_info["attached"],
                browser_context_id=target_info.get("browserContextId")
            )
            self._targets[target.target_id] = target
            if target.type == "page" and not target.attached:
                await self._attach_to_target(target.target_id)
                
        self.connection.on("Target.targetCreated", on_target_created)
        await self.connection.send_command(
            "Target.setDiscoverTargets",
            {"discover": True}
        )
        
    async def _attach_to_target(self, target_id: str) -> Optional[CDPSession]:
        target = self._targets.get(target_id)
        if not target:
            return None
            
        response = await self.connection.send_command(
            "Target.attachToTarget",
            {
                "targetId": target_id,
                "flatten": True
            }
        )
        session_id = response["sessionId"]
        
        session = CDPSession(self.connection, target, session_id)
        self._sessions[target_id] = session
        
        if target.type == "page":
            page = CDPPage(session)
            self._pages[target_id] = page
            
        return session
        
    async def new_page(self) -> 'CDPPage':
        response = await self.connection.send_command(
            "Target.createTarget",
            {"url": "about:blank"}
        )
        target_id = response["targetId"]
        
        while target_id not in self._pages:
            await asyncio.sleep(0.1)
            
        return self._pages[target_id]
        
    async def close(self):
        for page in list(self._pages.values()):
            await page.close()
        for session in list(self._sessions.values()):
            await session.detach()
        await self.connection.disconnect()
        
    async def connect_to_mcp(self, endpoint: str):
        raise NotImplementedError("CDP browser does not support MCP")

class CDPPage(PageProtocol):
    """CDP page implementation"""
    
    def __init__(self, session: CDPSession):
        self.session = session
        self._enabled_domains: List[str] = []
        
    async def _enable_domain(self, domain: str):
        if domain not in self._enabled_domains:
            await self.session.enable_domain(domain)
            self._enabled_domains.append(domain)
            
    async def goto(self, url: str):
        await self._enable_domain("Page")
        await self.session.send(
            "Page.navigate",
            {"url": url}
        )
        
    async def evaluate(self, script: str) -> Any:
        await self._enable_domain("Runtime")
        response = await self.session.send(
            "Runtime.evaluate",
            {
                "expression": script,
                "returnByValue": True,
                "awaitPromise": True
            }
        )
        result = response.get("result", {})
        if "value" in result:
            return result["value"]
        return None
        
    async def get_content(self) -> str:
        await self._enable_domain("DOM")
        root = await self.session.send("DOM.getDocument")
        outer_html = await self.session.send(
            "DOM.getOuterHTML",
            {"nodeId": root["root"]["nodeId"]}
        )
        return outer_html["outerHTML"]
        
    async def close(self):
        try:
            await self.session.send("Page.close")
        finally:
            await self.session.detach()
            
    async def screenshot(self) -> bytes:
        await self._enable_domain("Page")
        response = await self.session.send("Page.captureScreenshot")
        import base64
        return base64.b64decode(response["data"])
        
    async def wait_for_selector(self, selector: str):
        await self._enable_domain("DOM")
        await self.session.send(
            "DOM.querySelector",
            {
                "nodeId": (await self.session.send("DOM.getDocument"))["root"]["nodeId"],
                "selector": selector
            }
        )
