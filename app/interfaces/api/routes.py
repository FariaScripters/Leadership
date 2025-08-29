from fastapi import APIRouter, HTTPException
from app.infrastructure.external.llm.gemini_llm import GeminiLLM
from typing import Dict, List

router = APIRouter()
llm = GeminiLLM()

@router.post("/chat")
async def chat(messages: List[Dict[str, str]]):
    """
    Chat endpoint that uses Gemini for responses
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
    """
    try:
        response = await llm.ask(messages)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
