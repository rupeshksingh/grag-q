from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    # Database Settings
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    
    # API Keys
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str
    
    # Pipeline Settings
    DEFAULT_SEARCH_SCOPE: List[str] = ["Technical", "Requirements"]
    DEFAULT_RELEVANCE_THRESHOLD: float = 0.7
    DEFAULT_MAX_RESULTS: int = 100
    DEFAULT_INCLUDE_METADATA: bool = True
    
    # Retry Settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = "tender_pipeline.log"
    
    # Performance Monitoring
    ENABLE_PERFORMANCE_MONITORING: bool = True
    PERFORMANCE_LOG_INTERVAL: int = 100
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings():
    return Settings()