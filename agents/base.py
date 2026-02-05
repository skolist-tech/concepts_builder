"""
Base generator module providing shared Gemini client and utilities for all agents.
"""

import os
import logging
from typing import Optional

from google import genai
from google.genai import types

from config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Singleton-style Gemini client manager.
    Ensures only one client instance is created and reused across agents.
    """
    
    _instance: Optional[genai.Client] = None
    
    @classmethod
    def get_client(cls) -> genai.Client:
        """
        Get or create the Gemini client instance.
        
        Returns:
            The Gemini client instance.
        
        Raises:
            ValueError: If GEMINI_API_KEY is not set.
        """
        if cls._instance is None:
            api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY not set. Please set it in your .env file or environment."
                )
            cls._instance = genai.Client(api_key=api_key)
            logger.info("Gemini client initialized")
        return cls._instance
    
    @classmethod
    def reset_client(cls) -> None:
        """Reset the client instance (useful for testing)."""
        cls._instance = None


def read_pdf_as_part(pdf_path: str) -> types.Part:
    """
    Read a PDF file and return it as a Gemini Part object.
    
    Args:
        pdf_path: Path to the PDF file.
    
    Returns:
        A Gemini Part object containing the PDF data.
    
    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    with open(pdf_path, "rb") as f:
        part = types.Part.from_bytes(data=f.read(), mime_type="application/pdf")
    
    logger.info(f"PDF read successfully: {pdf_path}")
    return part


def format_concepts_list(concepts: list[str]) -> str:
    """
    Format a list of concepts for inclusion in a prompt.
    
    Args:
        concepts: List of concept names.
    
    Returns:
        Formatted string with concepts list.
    """
    if not concepts:
        return ""
    
    concepts_text = "\n\nCONCEPTS LIST:\n"
    concepts_text += "\n".join(f"- {concept}" for concept in concepts)
    return concepts_text


# Convenience function to get client
def get_gemini_client() -> genai.Client:
    """Convenience function to get the Gemini client."""
    return GeminiClient.get_client()
