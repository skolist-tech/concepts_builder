"""
Concept Generator Agent.

Takes a prompt and a PDF path as input, uses Gemini to generate 
structured concepts from the PDF, and returns a Chapter object.
"""

import logging

from google.genai import types

from config import settings
from agents.base import get_gemini_client, read_pdf_as_part
from schemas import Chapter

logger = logging.getLogger(__name__)


async def generate_concepts(prompt: str, pdf_path: str) -> Chapter:
    """
    Generate concepts from a chapter PDF using Gemini.
    
    Args:
        prompt: The prompt instructing how to extract concepts.
        pdf_path: Path to the chapter PDF file.
    
    Returns:
        A Chapter object containing topics and concepts.
    
    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
        ValueError: If the response cannot be parsed.
    """
    client = get_gemini_client()
    part = read_pdf_as_part(pdf_path)

    response = await client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=[prompt, part],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Chapter,
        ),
    )

    logger.info("Response generated successfully")

    chapter: Chapter = response.parsed
    
    if chapter is None:
        logger.error(f"Failed to parse response for {pdf_path}. Raw response: {response.text}")
        raise ValueError(f"Failed to parse response from Gemini for {pdf_path}")
    
    logger.info("Chapter parsed successfully")
    logger.info(
        f"Generated Chapter: {chapter.name} with {len(chapter.topics)} topics, "
        f"and {sum(len(topic.concepts) for topic in chapter.topics)} concepts."
    )
    return chapter
