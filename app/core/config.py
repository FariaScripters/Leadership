from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database settings
    mongodb_database: str = "leadership_db"
    mongodb_url: str = "mongodb://localhost:27017"
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    
    # Gemini settings
    gemini_api_key: str = "AIzaSyDJsHS0Viv9IUEW5vOO2bvgpe6AZCblXHQ"
    
    class Config:
        env_prefix = ""
        case_sensitive = False

_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
