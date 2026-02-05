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
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent / "data")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    @property
    def rbse_data_dir(self) -> Path:
        """RBSE input data directory."""
        return self.data_dir / "rbse"
    
    @property
    def rbse_output_dir(self) -> Path:
        """RBSE output directory."""
        return self.data_dir / "rbse_output"
    
    @property
    def ncert_data_dir(self) -> Path:
        """NCERT input data directory."""
        return self.data_dir / "ncert"
    
    def get_subject_input_dir(self, subject: str) -> Path:
        """Get input directory for a specific subject."""
        return self.rbse_data_dir / subject
    
    def get_subject_output_dir(self, subject: str) -> Path:
        """Get output directory for a specific subject."""
        return self.rbse_output_dir / subject


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
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


# Subject IDs mapping (can be extended or moved to database)
SUBJECT_IDS = {
    "maths_6_corodova": "11ea3956-d46e-4476-bb2c-a50afa027f5c", # stage-db
    # 'maths_6_corodova': "cc20f630-f811-49a2-ba21-632562b16ad0", 
}


def get_subject_id(subject_name: str) -> str:
    """Get the UUID for a subject by name."""
    if subject_name not in SUBJECT_IDS:
        raise ValueError(f"Unknown subject: {subject_name}. Available: {list(SUBJECT_IDS.keys())}")
    return SUBJECT_IDS[subject_name]