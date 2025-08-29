from typing import Dict, Any, Optional, List
import json
import logging
from .session import CDPSession, TargetInfo
from .connection import CDPConnection

logger = logging.getLogger(__name__)

class Page:
    """Represents a page target with CDP functionality"""
    
    def __init__(self, session: CDPSession):
        self.session = session
        self._enabled_domains: List[str] = []
        
    @property
    def target_id(self) -> str:
        return self.session.target_info.target_id
        
    @property
    def url(self) -> str:
        return self.session.target_info.url
        
    async def enable_domain(self, domain: str):
        """Enable a CDP domain for this page"""
        if domain not in self._enabled_domains:
            await self.session.enable_domain(domain)
            self._enabled_domains.append(domain)
            
    async def navigate(self, url: str, timeout: float = 30) -> Dict[str, Any]:
        """Navigate to URL and wait for load event
        
        Args:
            url: URL to navigate to
            timeout: Navigation timeout in seconds
            
        Returns:
            Navigation response from CDP
        """
        # Enable required domains
        await self.enable_domain("Page")
        
        # Navigate
        return await self.session.send(
            "Page.navigate",
            {"url": url},
            timeout=timeout
        )
        
    async def get_frame_tree(self) -> Dict[str, Any]:
        """Get frame tree for page"""
        await self.enable_domain("Page")
        return await self.session.send("Page.getFrameTree")
        
    async def enable_runtime(self):
        """Enable runtime domain for JavaScript execution"""
        await self.enable_domain("Runtime")
        
    async def evaluate(self, expression: str) -> Any:
        """Evaluate JavaScript expression
        
        Args:
            expression: JavaScript expression to evaluate
            
        Returns:
            Evaluation result
        """
        await self.enable_runtime()
        
        response = await self.session.send(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True
            }
        )
        
        result = response.get("result", {})
        if "value" in result:
            return result["value"]
        elif "description" in result:
            return result["description"]
        return None
        
    async def set_viewport(self, width: int, height: int):
        """Set viewport size
        
        Args:
            width: Viewport width
            height: Viewport height
        """
        await self.enable_domain("Emulation")
        await self.session.send(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": width,
                "height": height,
                "deviceScaleFactor": 1,
                "mobile": False
            }
        )
        
    async def screenshot(self, format: str = "png") -> bytes:
        """Take screenshot of page
        
        Args:
            format: Image format ("png" or "jpeg")
            
        Returns:
            Screenshot as bytes
        """
        await self.enable_domain("Page")
        
        response = await self.session.send(
            "Page.captureScreenshot",
            {"format": format}
        )
        
        import base64
        return base64.b64decode(response["data"])
        
    async def set_animation_speed(self, speed: float = 1.0):
        """Set animation playback speed
        
        Args:
            speed: Animation speed multiplier
        """
        await self.enable_domain("Animation")
        await self.session.send(
            "Animation.setPlaybackRate",
            {"playbackRate": speed}
        )
        
    async def close(self):
        """Close the page"""
        try:
            await self.session.send(
                "Page.close"
            )
        except Exception as e:
            logger.error(f"Error closing page: {str(e)}")
        finally:
            await self.session.detach()
