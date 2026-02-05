"""
Extract exercise questions from a chapter PDF and save to JSON + PDF.

Assumes concepts CSV already exists for the chapter.

Usage:
    uv run python extract_exercise.py
"""

import asyncio
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from config import setup_logging
from pipelines import process_chapter_for_exercise_questions, generate_exercise_questions_pdf
from prompts.rbse import MATHS_6_CORODOVA_EXERCISE_PROMPT

setup_logging()


async def extract_and_save(pdf_path: str | Path):
    """Extract exercise questions from PDF and save to JSON + PDF."""
    pdf_path = Path(pdf_path)
    
    print(f"📖 Processing: {pdf_path.name}")
    
    # Step 1: Extract exercise questions → JSON
    print("  ⏳ Extracting exercise questions...")
    exercise_bank = await process_chapter_for_exercise_questions(
        chapter_pdf_path=pdf_path,
        prompt=MATHS_6_CORODOVA_EXERCISE_PROMPT,
    )
    print(f"  ✅ Extracted {len(exercise_bank.exercise_questions)} questions → JSON saved")
    
    # Step 2: Generate PDF from JSON
    print("  ⏳ Generating PDF...")
    pdf_output = await generate_exercise_questions_pdf(chapter_pdf_path=pdf_path)
    print(f"  ✅ PDF saved: {pdf_output}")
    
    return exercise_bank


async def main():
    # === CONFIGURE YOUR PDF PATH HERE ===
    pdf_path = Path("data/rbse/maths_6_corodova/13_perimeter_and_area.pdf")
    
    # Or process multiple chapters:
    # pdf_paths = [
    #     Path("data/rbse/maths_6_corodova/05_fractions.pdf"),
    #     Path("data/rbse/maths_6_corodova/06_decimals.pdf"),
    # ]
    # for pdf_path in pdf_paths:
    #     await extract_and_save(pdf_path)
    
    await extract_and_save(pdf_path)


if __name__ == "__main__":
    asyncio.run(main())
