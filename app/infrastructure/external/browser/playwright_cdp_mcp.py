from typing import Dict, Any, List, Optional
from app.infrastructure.external.browser.puppeteer_mcp import BrowserMCP
import logging

logger = logging.getLogger(__name__)

class PlaywrightCDPMCP(BrowserMCP):
    """Playwright MCP implementation with CDP support"""
    
    def __init__(self):
        super().__init__("playwright")
        
    async def goto(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
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
        
        if wait_until == "networkidle":
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
        
    async def click(self, selector: str, options: Optional[Dict[str, Any]] = None) -> None:
        """Click element
        
        Args:
            selector: Element selector
            options: Click options
        """
        click_options = options or {}
        position = click_options.get("position", {})
        
        js = f"""
            (selector => {{
                const element = document.querySelector(selector);
                if (!element) throw new Error('Element not found');
                const rect = element.getBoundingClientRect();
                return {{
                    x: rect.left + {position.get("x", 0)},
                    y: rect.top + {position.get("y", 0)}
                }};
            }})("{selector}")
        """
        
        # Get element position
        pos = await self._evaluate(js)
        
        # Perform click
        await self.cdp.send_command(
            "Input.dispatchMouseEvent",
            {
                "type": "mousePressed",
                "x": pos["x"],
                "y": pos["y"],
                "button": "left",
                "clickCount": 1
            }
        )
        
        await self.cdp.send_command(
            "Input.dispatchMouseEvent",
            {
                "type": "mouseReleased",
                "x": pos["x"],
                "y": pos["y"],
                "button": "left",
                "clickCount": 1
            }
        )
        
    async def fill(self, selector: str, value: str) -> None:
        """Fill input element
        
        Args:
            selector: Element selector
            value: Value to fill
        """
        await self._evaluate(f"""
            (selector => {{
                const element = document.querySelector(selector);
                if (!element) throw new Error('Element not found');
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype,
                    "value"
                ).set;
                nativeInputValueSetter.call(element, "{value}");
                element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                element.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }})("{selector}")
        """)
        
    async def screenshot(self, options: Optional[Dict[str, Any]] = None) -> str:
        """Take screenshot
        
        Args:
            options: Screenshot options
            
        Returns:
            Base64 encoded screenshot
        """
        screenshot_options = options or {}
        
        if screenshot_options.get("fullPage"):
            # Get full page dimensions
            metrics = await self.cdp.send_command("Page.getLayoutMetrics")
            viewport = metrics["contentSize"]
            
            # Set viewport to full page size
            await self.cdp.send_command(
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": viewport["width"],
                    "height": viewport["height"],
                    "deviceScaleFactor": 1,
                    "mobile": False
                }
            )
            
        result = await self.cdp.send_command(
            "Page.captureScreenshot",
            {"format": "png"}
        )
        
        if screenshot_options.get("fullPage"):
            # Reset viewport
            await self.cdp.send_command("Emulation.clearDeviceMetricsOverride")
            
        return result.get("data", "")
