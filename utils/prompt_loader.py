"""
Prompt loading utility for CLI tools.

Handles loading prompts from text files.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_prompt(file_path: str) -> str:
    """
    Load a prompt from a text file.
    
    Args:
        file_path: Path to the prompt file.
    
    Returns:
        The prompt text content.
    
    Raises:
        FileNotFoundError: If the prompt file doesn't exist.
        ValueError: If the file is empty.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    
    content = path.read_text(encoding="utf-8").strip()
    
    if not content:
        raise ValueError(f"Empty prompt file: {file_path}")
    
    logger.info(f"Loaded prompt from {file_path} ({len(content)} chars)")
    return content
