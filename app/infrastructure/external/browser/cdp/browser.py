from typing import Dict, List, Optional, Any
import asyncio
import logging
from .connection import CDPConnection
from .session import CDPSession, TargetInfo
from .page import Page
from .launcher import ChromeLauncher

logger = logging.getLogger(__name__)

class Browser:
    """Browser instance with CDP support"""
    
    def __init__(self, connection: CDPConnection):
        self.connection = connection
        self._targets: Dict[str, TargetInfo] = {}
        self._sessions: Dict[str, CDPSession] = {}
        self._pages: Dict[str, Page] = {}
        
    @classmethod
    async def launch(cls, headless: bool = True) -> "Browser":
        """Launch new browser instance
        
        Args:
            headless: Whether to run in headless mode
            
        Returns:
            Browser instance
        """
        launcher = ChromeLauncher()
        connection = await launcher.launch(headless=headless)
        browser = cls(connection)
        
        # Setup target discovery
        await browser._setup_target_discovery()
        
        return browser
        
    async def _setup_target_discovery(self):
        """Setup target discovery and tracking"""
        
        # Handle target creation
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
            
            # Auto-attach to page targets
            if target.type == "page" and not target.attached:
                await self.attach_to_target(target.target_id)
                
        # Handle target destruction
        async def on_target_destroyed(params: Dict[str, Any]):
            target_id = params["targetId"]
            if target_id in self._targets:
                del self._targets[target_id]
            if target_id in self._sessions:
                await self._sessions[target_id].detach()
                del self._sessions[target_id]
            if target_id in self._pages:
                del self._pages[target_id]
                
        # Start discovering targets
        self.connection.on("Target.targetCreated", on_target_created)
        self.connection.on("Target.targetDestroyed", on_target_destroyed)
        
        await self.connection.send_command(
            "Target.setDiscoverTargets",
            {"discover": True}
        )
        
    async def attach_to_target(self, target_id: str) -> Optional[Page]:
        """Attach to target and create session
        
        Args:
            target_id: Target ID to attach to
            
        Returns:
            Page instance if target is a page, None otherwise
        """
        # Check if target exists
        target = self._targets.get(target_id)
        if not target:
            logger.error(f"Target {target_id} not found")
            return None
            
        # Attach to target
        response = await self.connection.send_command(
            "Target.attachToTarget",
            {
                "targetId": target_id,
                "flatten": True
            }
        )
        session_id = response["sessionId"]
        
        # Create session
        session = CDPSession(self.connection, target, session_id)
        self._sessions[target_id] = session
        
        # Create page if target is a page
        if target.type == "page":
            page = Page(session)
            self._pages[target_id] = page
            return page
            
        return None
        
    async def pages(self) -> List[Page]:
        """Get all pages
        
        Returns:
            List of page instances
        """
        return list(self._pages.values())
        
    async def new_page(self) -> Page:
        """Create new page
        
        Returns:
            Page instance
        """
        # Create new page target
        response = await self.connection.send_command(
            "Target.createTarget",
            {"url": "about:blank"}
        )
        target_id = response["targetId"]
        
        # Wait for target to be created and attached
        while target_id not in self._pages:
            await asyncio.sleep(0.1)
            
        return self._pages[target_id]
        
    async def close(self):
        """Close browser and cleanup"""
        # Close all pages
        for page in self._pages.values():
            await page.close()
            
        # Close all sessions
        for session in self._sessions.values():
            await session.detach()
            
        # Disconnect
        await self.connection.disconnect()
