#!/usr/bin/env python
"""
Exercise Questions Builder CLI

Extracts exercise questions from chapter PDFs and saves to JSON with UUIDs.

Usage:
    python exercise_questions_builder.py --input_dir <subject_directory_path> \
        --output_dir <exercise_question_json_output_directory_path> \
        --subject_id <subject_id_for_uuid_generation> \
        --prompt_file_path <path_to_prompt_file>
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from config import setup_logging
from pipelines.questions_pipeline import process_chapter_for_exercise_questions
from utils.prompt_loader import load_prompt
from utils.uuid_generator import validate_uuid

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)


def get_pdf_files(input_dir: Path) -> list[Path]:
    """Get all PDF files from the input directory."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        raise ValueError(f"No PDF files found in: {input_dir}")
    
    return pdf_files


def get_concepts_csv_path(pdf_path: Path, output_dir: Path) -> Path:
    """Get the concepts CSV path for a given PDF (expects it in output_dir)."""
    stem = pdf_path.stem
    return output_dir / f"{stem}_concepts.csv"


def get_output_json_path(pdf_path: Path, output_dir: Path) -> Path:
    """Generate the output JSON path for a given PDF."""
    stem = pdf_path.stem
    return output_dir / f"{stem}_exercise_questions.json"


async def process_all_chapters(
    input_dir: Path,
    output_dir: Path,
    subject_id: str,
    prompt: str
) -> None:
    """Process all chapter PDFs in the input directory."""
    pdf_files = get_pdf_files(input_dir)
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    successful = 0
    failed = 0
    
    for i, pdf_path in enumerate(pdf_files, 1):
        concepts_csv_path = get_concepts_csv_path(pdf_path, output_dir)
        output_json_path = get_output_json_path(pdf_path, output_dir)
        
        logger.info(f"[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")
        
        # Check if concepts CSV exists
        if not concepts_csv_path.exists():
            logger.error(f"[{i}/{len(pdf_files)}] Concepts CSV not found: {concepts_csv_path}")
            logger.error("Please run concepts_builder.py first to generate concept CSVs")
            failed += 1
            continue
        
        try:
            await process_chapter_for_exercise_questions(
                chapter_pdf_path=pdf_path,
                prompt=prompt,
                subject_id=subject_id,
                concepts_csv_path=concepts_csv_path,
                output_json_path=output_json_path
            )
            successful += 1
            logger.info(f"[{i}/{len(pdf_files)}] Saved: {output_json_path.name}")
        except Exception as e:
            failed += 1
            logger.error(f"[{i}/{len(pdf_files)}] Failed: {pdf_path.name} - {e}")
    
    logger.info(f"Completed: {successful} successful, {failed} failed out of {len(pdf_files)}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract exercise questions from chapter PDFs and save to JSON with UUIDs"
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Subject directory containing chapter PDFs"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Output directory for exercise question JSONs (should also contain concept CSVs)"
    )
    parser.add_argument(
        "--subject_id",
        type=str,
        required=True,
        help="Subject UUID for generating deterministic UUIDs"
    )
    parser.add_argument(
        "--prompt_file_path",
        type=str,
        required=True,
        help="Path to the prompt file for exercise question extraction"
    )
    
    args = parser.parse_args()
    
    # Validate subject_id
    if not validate_uuid(args.subject_id):
        logger.error(f"Invalid subject_id UUID: {args.subject_id}")
        sys.exit(1)
    
    # Load prompt
    try:
        prompt = load_prompt(args.prompt_file_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Subject ID: {args.subject_id}")
    
    try:
        asyncio.run(process_all_chapters(
            input_dir=input_dir,
            output_dir=output_dir,
            subject_id=args.subject_id,
            prompt=prompt
        ))
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
