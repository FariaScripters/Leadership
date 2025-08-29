import logging
from typing import Optional, Dict, Any
from app.core.config import get_settings
from app.infrastructure.external.llm.openrouter_llm import OpenRouterLLM

logger = logging.getLogger(__name__)

class LLMFactory:
    """Factory class to create appropriate LLM provider based on configuration"""
    
    @staticmethod
    def create_llm() -> OpenRouterLLM:
        """Create and return the appropriate LLM provider
        
        Returns:
            LLM provider instance
        """
        settings = get_settings()
        
        # For now, use OpenRouter as the primary provider
        # This can be extended to support multiple providers
        return OpenRouterLLM()
    
    @staticmethod
    def get_provider_info() -> Dict[str, Any]:
        """Get information about the current LLM provider
        
        Returns:
            Dictionary with provider information
        """
        settings = get_settings()
        
        return {
            "provider": "OpenRouter",
            "default_model": settings.openrouter_default_model,
            "fallback_models": settings.openrouter_fallback_models,
            "has_api_key": bool(settings.openrouter_api_key),
            "base_url": settings.openrouter_base_url
        }
    
    @staticmethod
    def get_free_models() -> list:
        """Get list of available free models
        
        Returns:
            List of free model identifiers
        """
        llm = LLMFactory.create_llm()
        return llm.get_free_models()
