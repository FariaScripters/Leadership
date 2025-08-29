"""
Main FastAPI application for Leadership Assistant with OpenRouter integration.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import OpenRouter LLM
from app.infrastructure.external.llm.llm_factory import LLMFactory

# Create FastAPI app
app = FastAPI(
    title="Leadership Assistant API",
    description="AI-powered leadership coaching with OpenRouter integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM factory
llm_factory = LLMFactory()

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Leadership Assistant API",
        "version": "1.0.0",
        "llm_provider": "OpenRouter",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway monitoring."""
    try:
        # Test OpenRouter connection
        llm = llm_factory.create_llm()
        return {
            "status": "healthy",
            "llm_provider": "OpenRouter",
            "default_model": os.getenv("OPENROUTER_DEFAULT_MODEL", "google/gemini-flash-1.5-8b")
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )

@app.post("/api/chat")
async def chat_endpoint(message: dict):
    """Basic chat endpoint for testing."""
    try:
        llm = llm_factory.create_llm()
        response = await llm.generate_async(
            prompt=message.get("message", "Hello"),
            system_prompt="You are a helpful leadership coach."
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
