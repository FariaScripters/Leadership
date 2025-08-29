from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List

class Settings(BaseSettings):
    # Database settings
    mongodb_database: str = "leadership_db"
    mongodb_url: str = "mongodb://localhost:27017"
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    
    # Gemini settings
    gemini_api_key: str = "AIzaSyDJsHS0Viv9IUEW5vOO2bvgpe6AZCblXHQ"
    
    # OpenRouter settings
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_default_model: str = "google/gemini-flash-1.5-8b"
    openrouter_fallback_models: List[str] = [
        "google/gemini-flash-1.5-8b",
        "meta-llama/llama-3.1-8b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "microsoft/phi-3-medium-128k-instruct:free"
    ]
    
    # Browser CDP settings
    chrome_remote_debugging_port: int = 9222
    chrome_ws_endpoint: str = "ws://localhost:9222"
    
    # MCP server settings
    mcp_servers: Dict[str, Dict[str, Any]] = {
        "sequentialthinking": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "mcp/sequentialthinking"
            ]
        },
        "memory": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "-v",
                "/local-directory:/local-directory",
                "mcp/memory"
            ]
        },
        "playwright-mcp": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "-v",
                "/local-directory:/local-directory",
                "mcp/mcp-playwright"
            ]
        },
        "task-orchestrator": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "-v",
                "/local-directory:/local-directory",
                "ghcr.io/jpicklyk/task-orchestrator"
            ]
        },
        "puppeteer": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "-e",
                "DOCKER_CONTAINER",
                "mcp/puppeteer"
            ],
            "env": {
                "DOCKER_CONTAINER": "true"
            }
        },
        "playwright": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "mcp/playwright"
            ]
        }
    }
    
    class Config:
        env_prefix = ""
        case_sensitive = False

_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
