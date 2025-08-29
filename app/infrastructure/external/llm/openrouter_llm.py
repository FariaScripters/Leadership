import aiohttp
import json
import logging
from typing import List, Dict, Any, Optional
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class OpenRouterLLM:
    """OpenRouter implementation of the LLM interface with free model support"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.openrouter_base_url
        self.api_key = self.settings.openrouter_api_key
        self.default_model = self.settings.openrouter_default_model
        self.fallback_models = self.settings.openrouter_fallback_models
        
    async def ask(self, messages: List[Dict[str, str]], temperature: Optional[float] = 0.7) -> Dict[str, Any]:
        """Send a message to OpenRouter and get a response with fallback support
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Optional temperature parameter for response generation
            
        Returns:
            Dictionary containing the response
        """
        # Try models in order: default, then fallbacks
        models_to_try = [self.default_model] + self.fallback_models
        
        for model in models_to_try:
            try:
                response = await self._try_model(model, messages, temperature)
                if response and "content" in response and response["content"]:
                    logger.info(f"Successfully used model: {model}")
                    return response
            except Exception as e:
                logger.warning(f"Model {model} failed: {str(e)}")
                continue
        
        # All models failed
        error_msg = "All OpenRouter models failed. Please check your API key and internet connection."
        logger.error(error_msg)
        return {
            "content": f"Error: {error_msg}",
            "role": "assistant"
        }
    
    async def _try_model(self, model: str, messages: List[Dict[str, str]], temperature: float) -> Dict[str, Any]:
        """Try to get a response from a specific model
        
        Args:
            model: The model name to use
            messages: List of message dictionaries
            temperature: Temperature parameter
            
        Returns:
            Dictionary containing the response
        """
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo/leadership-assistant",
            "X-Title": "Leadership Assistant"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    return {
                        "content": content,
                        "role": "assistant",
                        "model_used": model
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from OpenRouter
        
        Returns:
            List of model information dictionaries
        """
        if not self.api_key:
            return []
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
                    else:
                        logger.warning(f"Failed to fetch models: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching models: {str(e)}")
            return []
    
    def get_free_models(self) -> List[str]:
        """Get list of known free models
        
        Returns:
            List of free model identifiers
        """
        return [
            "google/gemini-flash-1.5-8b",
            "meta-llama/llama-3.1-8b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
            "microsoft/phi-3-medium-128k-instruct:free",
            "qwen/qwen-2-7b-instruct:free",
            "nousresearch/hermes-3-llama-3.1-8b:free"
        ]
