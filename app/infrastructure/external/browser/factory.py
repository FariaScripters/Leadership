from typing import Dict, Type, Optional
from .protocol import BrowserProtocol, BrowserConfig
from .built_in import CDPBrowserProvider

class BrowserFactory:
    """Factory for creating browser instances"""
    
    def __init__(self):
        self._providers: Dict[str, Type] = {
            "cdp": CDPBrowserProvider
        }
        
    def register_provider(self, name: str, provider_class: Type):
        """Register new browser provider"""
        self._providers[name] = provider_class
        
    async def create_browser(
        self,
        provider: str = "cdp",
        config: Optional[BrowserConfig] = None
    ) -> BrowserProtocol:
        """Create browser instance
        
        Args:
            provider: Provider name ("cdp" or "mcp")
            config: Browser configuration
            
        Returns:
            Browser instance
            
        Raises:
            ValueError: If provider not found
        """
        if provider not in self._providers:
            raise ValueError(f"Provider {provider} not found")
            
        if config is None:
            config = BrowserConfig()
            
        provider_class = self._providers[provider]
        provider_instance = provider_class()
        return await provider_instance.create_browser(config)

# Global factory instance
browser_factory = BrowserFactory()
