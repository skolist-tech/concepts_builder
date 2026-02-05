"""
PDF generation pipeline.

Handles the workflow for converting question banks to PDF format.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, List

from schemas import (
    load_solved_bank_json, 
    load_exercise_bank_json,
    save_solved_bank_pdf,
    save_exercise_bank_pdf,
)
from utils.paths import (
    get_chapter_paths,
    get_chapter_name,
    get_solved_examples_json_path,
    get_solved_examples_pdf_path,
    get_exercise_questions_json_path,
    get_exercise_questions_pdf_path,
)

logger = logging.getLogger(__name__)


async def generate_solved_examples_pdf(
    chapter_pdf_path: Path,
    json_path: Optional[Path] = None,
    output_pdf_path: Optional[Path] = None
) -> Optional[Path]:
    """
    Generate a PDF from solved examples JSON file.
    
    Args:
        chapter_pdf_path: Path to the original chapter PDF (used for naming).
        json_path: Path to the solved examples JSON. Auto-generated if not provided.
        output_pdf_path: Path for the output PDF. Auto-generated if not provided.
    
    Returns:
        Path to the generated PDF, or None if JSON doesn't exist.
    """
    chapter_pdf_path = Path(chapter_pdf_path)
    chapter_name = get_chapter_name(chapter_pdf_path)
    
    if json_path is None:
        json_path = get_solved_examples_json_path(chapter_pdf_path)
    
    if output_pdf_path is None:
        output_pdf_path = get_solved_examples_pdf_path(chapter_pdf_path)
    
    json_path = Path(json_path)
    
    if not json_path.exists():
        logger.warning(f"JSON not found for {chapter_name}: {json_path}")
        return None
    
    try:
        logger.info(f"Generating solved examples PDF for {chapter_name}...")
        
        # Load the bank from JSON
        bank = await asyncio.to_thread(load_solved_bank_json, str(json_path))
        
        # Generate PDF
        await save_solved_bank_pdf(bank, str(output_pdf_path))
        
        logger.info(f"Successfully generated PDF: {output_pdf_path}")
        return output_pdf_path
        
    except Exception as e:
        logger.error(f"Failed to generate PDF for {chapter_name}: {e}")
        return None


async def generate_exercise_questions_pdf(
    chapter_pdf_path: Path,
    json_path: Optional[Path] = None,
    output_pdf_path: Optional[Path] = None
) -> Optional[Path]:
    """
    Generate a PDF from exercise questions JSON file.
    
    Args:
        chapter_pdf_path: Path to the original chapter PDF (used for naming).
        json_path: Path to the exercise questions JSON. Auto-generated if not provided.
        output_pdf_path: Path for the output PDF. Auto-generated if not provided.
    
    Returns:
        Path to the generated PDF, or None if JSON doesn't exist.
    """
    chapter_pdf_path = Path(chapter_pdf_path)
    chapter_name = get_chapter_name(chapter_pdf_path)
    
    if json_path is None:
        json_path = get_exercise_questions_json_path(chapter_pdf_path)
    
    if output_pdf_path is None:
        output_pdf_path = get_exercise_questions_pdf_path(chapter_pdf_path)
    
    json_path = Path(json_path)
    
    if not json_path.exists():
        logger.warning(f"JSON not found for {chapter_name}: {json_path}")
        return None
    
    try:
        logger.info(f"Generating exercise questions PDF for {chapter_name}...")
        
        # Load the bank from JSON
        bank = await asyncio.to_thread(load_exercise_bank_json, str(json_path))
        
        # Generate PDF
        await save_exercise_bank_pdf(bank, str(output_pdf_path))
        
        logger.info(f"Successfully generated PDF: {output_pdf_path}")
        return output_pdf_path
        
    except Exception as e:
        logger.error(f"Failed to generate PDF for {chapter_name}: {e}")
        return None


async def generate_all_pdfs(
    chapter_paths: Optional[List[Path]] = None,
    question_type: str = "both"
) -> dict:
    """
    Generate PDFs for all chapters.
    
    Args:
        chapter_paths: List of chapter PDF paths. Uses default if not provided.
        question_type: "solved", "exercise", or "both".
    
    Returns:
        Dictionary with generation results.
    """
    if chapter_paths is None:
        chapter_paths = get_chapter_paths()
    
    results = {
        "solved_examples": {"success": 0, "failed": 0},
        "exercise_questions": {"success": 0, "failed": 0},
    }
    
    tasks = []
    
    for chapter_path in chapter_paths:
        if question_type in ("solved", "both"):
            tasks.append(("solved", generate_solved_examples_pdf(chapter_path)))
        if question_type in ("exercise", "both"):
            tasks.append(("exercise", generate_exercise_questions_pdf(chapter_path)))
    
    # Run all tasks concurrently
    task_results = await asyncio.gather(
        *[task[1] for task in tasks],
        return_exceptions=True
    )
    
    for (q_type, _), result in zip(tasks, task_results):
        key = "solved_examples" if q_type == "solved" else "exercise_questions"
        if isinstance(result, Exception):
            results[key]["failed"] += 1
            logger.error(f"PDF generation failed: {result}")
        elif result is not None:
            results[key]["success"] += 1
        else:
            results[key]["failed"] += 1
    
    logger.info(f"PDF generation complete: {results}")
    return results
