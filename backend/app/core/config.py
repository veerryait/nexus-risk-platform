"""
Application Configuration
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "change_this_to_a_secure_random_string"
    
    # Database
    DATABASE_URL: str = ""
    DB_HOST: str = ""
    DB_PORT: int = 6543
    DB_NAME: str = "postgres"
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # External APIs
    MARINE_TRAFFIC_API_KEY: str = ""
    OPENWEATHER_API_KEY: str = ""
    NEWS_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
