"""
Concept generation pipeline.

Handles the workflow for generating concepts from chapter PDFs.
"""

import logging
from pathlib import Path
from typing import Optional

from agents import generate_concepts
from schemas import Chapter, save_csv
from utils.paths import get_concepts_csv_path

logger = logging.getLogger(__name__)


async def process_chapter_for_concepts(
    chapter_pdf_path: Path,
    prompt: str,
    output_csv_path: Optional[Path] = None,
    chapter_position: int = 1
) -> Chapter:
    """
    Process a chapter PDF to extract concepts and save to CSV.
    
    Args:
        chapter_pdf_path: Path to the chapter PDF file.
        prompt: The prompt for concept extraction.
        output_csv_path: Path for the output CSV. Auto-generated if not provided.
        chapter_position: Position of the chapter (used in CSV).
    
    Returns:
        The generated Chapter object.
    
    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
        ValueError: If concept generation fails.
    """
    chapter_pdf_path = Path(chapter_pdf_path)
    
    if not chapter_pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {chapter_pdf_path}")
    
    if output_csv_path is None:
        output_csv_path = get_concepts_csv_path(chapter_pdf_path)
    
    logger.info(f"Processing chapter for concepts: {chapter_pdf_path}")
    
    # Generate concepts using the agent
    chapter: Chapter = await generate_concepts(
        prompt=prompt,
        pdf_path=str(chapter_pdf_path)
    )
    
    # Save to CSV
    save_csv(chapter, str(output_csv_path), chapter_position)
    logger.info(f"Concepts saved to CSV: {output_csv_path}")
    
    return chapter
