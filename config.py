"""
Centralized configuration for the concepts_builder application.
Uses pydantic-settings for environment variable management and validation.
"""

import logging
from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_key: str = Field(default="", alias="SUPABASE_SERVICE_KEY")
    
    # Model Configuration
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    
    # Processing Configuration
    max_concurrent_uploads: int = Field(default=1, alias="MAX_CONCURRENT_UPLOADS")
    max_concurrent_generations: int = Field(default=3, alias="MAX_CONCURRENT_GENERATIONS")
    
    # Paths - Base directories
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience access
settings = get_settings()


def setup_logging(
    level: int = logging.INFO,
    log_file: str = "app.log",
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> None:
    """
    Configure application-wide logging with file and console handlers.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Path to the log file
        format_string: Format string for log messages
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Avoid adding duplicate handlers
    if root_logger.handlers:
        return
    
    formatter = logging.Formatter(format_string)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler with colors
    class ColoredFormatter(logging.Formatter):
        """Formatter that adds colors to log levels."""
        COLORS = {
            logging.DEBUG: "\033[36m",     # Cyan
            logging.INFO: "\033[32m",      # Green
            logging.WARNING: "\033[33m",   # Yellow
            logging.ERROR: "\033[31m",     # Red
            logging.CRITICAL: "\033[1;31m", # Bold Red
        }
        RESET = "\033[0m"
        
        def format(self, record):
            color = self.COLORS.get(record.levelno, self.RESET)
            message = super().format(record)
            return f"{color}{message}{self.RESET}"
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter(format_string))
    root_logger.addHandler(console_handler)
    
    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.WARNING)