import google.generativeai as genai
from typing import List, Dict, Any, Optional
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class GeminiLLM:
    """Gemini implementation of the LLM interface"""
    
    def __init__(self):
        self.settings = get_settings()
        # Configure the Gemini API
        genai.configure(api_key=self.settings.gemini_api_key)
        # For text-only input, use the gemini-pro model
        self.model = genai.GenerativeModel('gemini-pro')
        
    async def ask(self, messages: List[Dict[str, str]], temperature: Optional[float] = 0.7) -> Dict[str, Any]:
        """Send a message to Gemini and get a response
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Optional temperature parameter for response generation
            
        Returns:
            Dictionary containing the response
        """
        try:
            # Convert chat format to Gemini format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature
                )
            )
            
            return {
                "content": response.text,
                "role": "assistant"
            }
            
        except Exception as e:
            logger.error(f"Error in Gemini LLM: {str(e)}")
            return {
                "content": f"Error: {str(e)}",
                "role": "assistant"
            }
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to a single prompt string
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Combined prompt string
        """
        prompt = ""
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            
            if role == 'system':
                prompt += f"System: {content}\n\n"
            elif role == 'user':
                prompt += f"Human: {content}\n\n"
            elif role == 'assistant':
                prompt += f"Assistant: {content}\n\n"
                
        return prompt.strip()
