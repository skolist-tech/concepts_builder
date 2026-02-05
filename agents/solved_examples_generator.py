"""
Solved Examples Generator Agent.

Takes a prompt, PDF path, and concepts list as input, uses Gemini to 
generate solved examples mapped to concepts, returns a SolvedExamplesBank object.
"""

import os
import logging

from google.genai import types

from config import settings
from agents.base import get_gemini_client, read_pdf_as_part, format_concepts_list
from schemas import SolvedExamplesBank

logger = logging.getLogger(__name__)


async def generate_solved_examples(
    prompt: str, 
    pdf_path: str, 
    concepts_list: list[str]
) -> SolvedExamplesBank:
    """
    Generate solved examples from a chapter PDF using Gemini.
    
    Args:
        prompt: The prompt instructing how to extract solved examples.
        pdf_path: Path to the chapter PDF file.
        concepts_list: List of concept names to map questions to.
    
    Returns:
        A SolvedExamplesBank object containing solved examples.
    
    Raises:
        ValueError: If inputs are invalid or response cannot be parsed.
        FileNotFoundError: If the PDF file doesn't exist.
    """
    if not concepts_list:
        raise ValueError("concepts_list cannot be empty.")
    if not prompt:
        raise ValueError("prompt cannot be empty.")
    if not pdf_path:
        raise ValueError("pdf_path cannot be empty.")
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")
    
    client = get_gemini_client()
    part = read_pdf_as_part(pdf_path)
    
    # Format concepts list and append to prompt
    full_prompt = prompt + format_concepts_list(concepts_list)
    
    response = await client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=[full_prompt, part],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SolvedExamplesBank,
        ),
    )
    
    logger.info("Response generated successfully")
    solved_examples_bank: SolvedExamplesBank = response.parsed
    
    if solved_examples_bank is None:
        logger.error(f"Failed to parse response for {pdf_path}. Raw response text: {response.text}")
        raise ValueError(
            f"Failed to parse response from Gemini for {pdf_path}. "
            "The model might have been blocked or returned invalid JSON."
        )

    logger.info("SolvedExamplesBank parsed successfully")
    logger.info(
        f"Generated SolvedExamplesBank with {len(solved_examples_bank.solved_examples_questions)} "
        f"solved examples for chapter: {solved_examples_bank.chapter_name}."
    )
    return solved_examples_bank