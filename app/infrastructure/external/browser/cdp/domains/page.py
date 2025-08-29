from typing import Dict, Any, Optional, List
from .base import CDPDomain

class PageDomain(CDPDomain):
    """CDP Page domain implementation"""
    
    async def enable(self):
        """Enable page domain events"""
        await self.execute_command("Page.enable")
        
    async def navigate(self, url: str, referrer: str = None) -> Dict[str, Any]:
        """Navigate to URL
        
        Args:
            url: URL to navigate to
            referrer: Referrer URL
            
        Returns:
            Navigation result with loaderId and frameId
        """
        params = {"url": url}
        if referrer:
            params["referrer"] = referrer
        return await self.execute_command("Page.navigate", params)
        
    async def reload(self, ignore_cache: bool = False):
        """Reload page
        
        Args:
            ignore_cache: If true, browser cache is ignored
        """
        await self.execute_command("Page.reload", {"ignoreCache": ignore_cache})
        
    async def capture_screenshot(self, format: str = "png", quality: Optional[int] = None,
                               clip: Optional[Dict[str, Any]] = None, full_page: bool = False) -> str:
        """Take page screenshot
        
        Args:
            format: Image format (png/jpeg)
            quality: Compression quality (jpeg only)
            clip: Capture clip rectangle
            full_page: Capture full page
            
        Returns:
            Base64-encoded screenshot data
        """
        params = {"format": format}
        if quality is not None and format == "jpeg":
            params["quality"] = quality
        if clip:
            params["clip"] = clip
        if full_page:
            # Get full page dimensions
            metrics = await self.execute_command("Page.getLayoutMetrics")
            viewport = metrics["contentSize"]
            params["clip"] = {
                "x": 0,
                "y": 0,
                "width": viewport["width"],
                "height": viewport["height"],
                "scale": 1
            }
        
        result = await self.execute_command("Page.captureScreenshot", params)
        return result.get("data", "")
