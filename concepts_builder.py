#!/usr/bin/env python
"""
Concepts Builder CLI

Extracts concepts from chapter PDFs and saves to CSV with UUIDs.

Usage:
    python concepts_builder.py --input_dir <subject_directory_path> \
        --output_dir <concept_csv_output_directory_path> \
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

from config import setup_logging, settings
from pipelines.concept_pipeline import process_chapter_for_concepts
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


def get_output_csv_path(pdf_path: Path, output_dir: Path) -> Path:
    """Generate the output CSV path for a given PDF."""
    stem = pdf_path.stem
    return output_dir / f"{stem}_concepts.csv"


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

    max_concurrent = getattr(settings, "max_concurrent_generations", 3)
    logger.info(f"Using max_concurrent_generations={max_concurrent}")

    successful = 0
    failed = 0

    sem = asyncio.Semaphore(max_concurrent)
    results = []

    async def process_one(i, pdf_path):
        output_csv_path = get_output_csv_path(pdf_path, output_dir)
        logger.info(f"[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")
        async with sem:
            try:
                await process_chapter_for_concepts(
                    chapter_pdf_path=pdf_path,
                    prompt=prompt,
                    subject_id=subject_id,
                    output_csv_path=output_csv_path,
                    chapter_position=i
                )
                logger.info(f"[{i}/{len(pdf_files)}] Saved: {output_csv_path.name}")
                return True
            except Exception as e:
                logger.error(f"[{i}/{len(pdf_files)}] Failed: {pdf_path.name} - {e}")
                return False

    tasks = [process_one(i, pdf_path) for i, pdf_path in enumerate(pdf_files, 1)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    successful = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False or isinstance(r, Exception))
    logger.info(f"Completed: {successful} successful, {failed} failed out of {len(pdf_files)}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract concepts from chapter PDFs and save to CSV with UUIDs"
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
        help="Output directory for concept CSVs"
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
        help="Path to the prompt file for concept extraction"
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
