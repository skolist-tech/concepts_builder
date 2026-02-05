"""
Concepts Builder - Main Entry Point

A tool for extracting structured educational content from textbook PDFs using AI.
Generates concepts, solved examples, and exercise questions, then uploads to Supabase.

Usage:
    # Run with default settings (uploads exercise questions to Supabase)
    uv run python main.py
    
    # Or import and use specific pipelines
    from pipelines import (
        process_chapter_for_concepts,
        process_chapter_for_solved_examples,
        upload_all_chapters,
    )
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from config import setup_logging, settings
from utils.paths import get_chapter_paths
from pipelines import (
    process_chapter_for_concepts,
    process_chapter_for_solved_examples,
    process_chapter_for_exercise_questions,
    generate_all_pdfs,
    upload_all_chapters,
)
from prompts.rbse import (
    MATHS_6_CORODOVA_PROMPT,
    MATHS_6_CORODOVA_SOLVED_EG_PROMPT,
    MATHS_6_CORODOVA_EXERCISE_PROMPT,
)

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)


# Configuration for processing
SUBJECT_NAME = "maths_6_corodova"
CHAPTERS_TO_PROCESS: List[str] = [
    # Add specific chapter filenames to process only those, or leave empty for all
    # Example: "05_fractions.pdf", "13_perimeter_and_area.pdf"
]


def get_chapters_to_process() -> List[Path]:
    """Get list of chapter paths to process based on configuration."""
    all_chapters = get_chapter_paths(
        input_dir=settings.get_subject_input_dir(SUBJECT_NAME)
    )
    
    if CHAPTERS_TO_PROCESS:
        return [p for p in all_chapters if p.name in CHAPTERS_TO_PROCESS]
    
    return all_chapters


async def generate_concepts_for_all_chapters():
    """Generate concepts for all chapters and save to CSV."""
    chapters = get_chapters_to_process()
    logger.info(f"Processing {len(chapters)} chapters for concepts")
    
    tasks = []
    for i, chapter_path in enumerate(chapters, 1):
        tasks.append(
            process_chapter_for_concepts(
                chapter_pdf_path=chapter_path,
                prompt=MATHS_6_CORODOVA_PROMPT,
                chapter_position=i,
            )
        )
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = sum(1 for r in results if not isinstance(r, Exception))
    logger.info(f"Concepts generated for {successful}/{len(chapters)} chapters")


async def generate_solved_examples_for_all_chapters():
    """Generate solved examples for all chapters and save to JSON."""
    chapters = get_chapters_to_process()
    logger.info(f"Processing {len(chapters)} chapters for solved examples")
    
    tasks = []
    for chapter_path in chapters:
        tasks.append(
            process_chapter_for_solved_examples(
                chapter_pdf_path=chapter_path,
                prompt=MATHS_6_CORODOVA_SOLVED_EG_PROMPT,
            )
        )
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Failed: {result}")
    
    successful = sum(1 for r in results if not isinstance(r, Exception))
    logger.info(f"Solved examples generated for {successful}/{len(chapters)} chapters")


async def generate_exercise_questions_for_all_chapters():
    """Generate exercise questions for all chapters and save to JSON."""
    chapters = get_chapters_to_process()
    logger.info(f"Processing {len(chapters)} chapters for exercise questions")
    
    tasks = []
    for chapter_path in chapters:
        tasks.append(
            process_chapter_for_exercise_questions(
                chapter_pdf_path=chapter_path,
                prompt=MATHS_6_CORODOVA_EXERCISE_PROMPT,
            )
        )
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Failed: {result}")
    
    successful = sum(1 for r in results if not isinstance(r, Exception))
    logger.info(f"Exercise questions generated for {successful}/{len(chapters)} chapters")


async def generate_pdfs_for_all_chapters():
    """Generate PDFs from JSON files for all chapters."""
    chapters = get_chapters_to_process()
    await generate_all_pdfs(chapter_paths=chapters, question_type="both")


async def upload_to_supabase(question_type: str = "both"):
    """Upload questions to Supabase."""
    chapters = get_chapters_to_process()
    await upload_all_chapters(
        subject_name=SUBJECT_NAME,
        chapter_paths=chapters,
        question_type=question_type,
        max_concurrent=settings.max_concurrent_uploads,
    )


async def main():
    """
    Main entry point.
    
    Uncomment the desired pipeline to run:
    """
    # Step 1: Generate concepts from PDFs
    # await generate_concepts_for_all_chapters()
    
    # Step 2: Generate solved examples (requires concepts CSV)
    # await generate_solved_examples_for_all_chapters()
    
    # Step 3: Generate exercise questions (requires concepts CSV)
    # await generate_exercise_questions_for_all_chapters()
    
    # Step 4: Generate PDFs from JSON files
    # await generate_pdfs_for_all_chapters()
    
    # Step 5: Upload to Supabase
    await upload_to_supabase(question_type="exercise")


if __name__ == "__main__":
    asyncio.run(main())
