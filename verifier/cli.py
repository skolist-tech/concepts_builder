#!/usr/bin/env python
"""
CLI entry point for the verifier package.

Provides command-line interface for running verification checks on
concept CSVs and question JSON files.

Usage:
    python -m verifier --input_dir <directory_path> --check-chapters
    python -m verifier --input_dir <directory_path> --check-concepts
    python -m verifier --input_dir <directory_path> --check-concepts --suggest
    python -m verifier --input_dir <directory_path> --check-conventions
    python -m verifier --input_dir <directory_path> --check-chapters --check-concepts --check-conventions
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
from verifier.checkers import (
    check_chapter_consistency,
    check_concept_consistency,
    check_conventions,
)
from verifier.loaders import get_file_groups

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed argument namespace with input_dir and check flags.
    """
    parser = argparse.ArgumentParser(
        description="Verify consistency between concept CSVs and question JSONs"
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Directory containing concept CSVs and question JSONs"
    )
    parser.add_argument(
        "--check-chapters",
        action="store_true",
        help="Check chapter_name and chapter_id consistency"
    )
    parser.add_argument(
        "--check-concepts",
        action="store_true",
        help="Check that concepts in questions exist in CSVs"
    )
    parser.add_argument(
        "--suggest",
        action="store_true",
        help="Use Gemini AI to suggest correct concept mappings for missing concepts (requires --check-concepts)"
    )
    parser.add_argument(
        "--apply-gemini-suggestion",
        action="store_true",
        help="Validate and apply Gemini suggestions to JSON files (requires --suggest)"
    )
    parser.add_argument(
        "--check-conventions",
        action="store_true",
        help="Check file naming conventions and position consistency"
    )
    
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> bool:
    """
    Validate command line arguments.
    
    Args:
        args: Parsed argument namespace.
        
    Returns:
        True if arguments are valid, False otherwise.
    """
    # Require at least one check
    if not args.check_chapters and not args.check_concepts and not args.check_conventions:
        logger.error("Please specify at least one check: --check-chapters, --check-concepts, or --check-conventions")
        return False
    
    # --suggest requires --check-concepts
    if args.suggest and not args.check_concepts:
        logger.error("--suggest requires --check-concepts to be enabled")
        return False
    
    # --apply-gemini-suggestion requires --suggest
    if args.apply_gemini_suggestion and not args.suggest:
        logger.error("--apply-gemini-suggestion requires --suggest to be enabled")
        return False
    
    return True


def main() -> None:
    """
    Main entry point for the verifier CLI.
    
    Parses arguments, validates them, loads file groups, and runs the
    requested verification checks. Exits with code 1 if any checks fail.
    """
    args = parse_args()
    
    if not validate_args(args):
        sys.exit(1)
    
    input_dir = Path(args.input_dir)
    
    logger.info(f"Input directory: {input_dir}")
    logger.info("")
    
    try:
        groups = get_file_groups(input_dir)
        logger.info(f"Found {len(groups)} chapter file groups")
        logger.info("")
        
        total_failed = 0
        
        if args.check_chapters:
            _, ch_failed, _ = check_chapter_consistency(groups)
            total_failed += ch_failed
            logger.info("")
        
        if args.check_concepts:
            _, co_failed, _ = asyncio.run(check_concept_consistency(
                groups, 
                suggest=args.suggest,
                apply_suggestions=args.apply_gemini_suggestion,
            ))
            total_failed += co_failed
            logger.info("")
        
        if args.check_conventions:
            _, conv_failed, _ = check_conventions(input_dir)
            total_failed += conv_failed
        
        if total_failed > 0:
            sys.exit(1)
        
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
