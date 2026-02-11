#!/usr/bin/env python
"""
UUID Migration CLI

Adds deterministic UUIDs to existing CSV and JSON files that don't have them.
Processes all matching files in a directory.

Usage:
    python migrate_add_uuids.py --input_dir ./data/rbse_output/maths_6 \
        --output_dir ./data/rbse_output_with_uuids/maths_6 \
        --subject_id <uuid>

Processes:
    - *_concepts.csv files
    - *_exercise_questions.json files
    - *_solved_examples.json files
"""

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from config import setup_logging
from utils.uuid_generator import validate_uuid
from utils.add_uuids_to_existing import add_uuids_to_directory

setup_logging()
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Add deterministic UUIDs to existing CSV and JSON files in a directory"
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Input directory containing CSV and JSON files without UUIDs"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Output directory for files with UUIDs added"
    )
    parser.add_argument(
        "--subject_id",
        type=str,
        required=True,
        help="Subject UUID for generating deterministic UUIDs"
    )
    
    args = parser.parse_args()
    
    # Validate subject_id
    if not validate_uuid(args.subject_id):
        logger.error(f"Invalid subject_id UUID: {args.subject_id}")
        sys.exit(1)
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        sys.exit(1)
    
    print(f"Input directory:  {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Subject ID:       {args.subject_id}")
    print()
    
    try:
        stats = add_uuids_to_directory(str(input_dir), str(output_dir), args.subject_id)
        
        print(f"✓ Migration complete:")
        print(f"  - {stats['concepts_csvs']} concept CSVs ({stats['total_concepts']} concepts)")
        print(f"  - {stats['exercise_jsons']} exercise question JSONs")
        print(f"  - {stats['solved_jsons']} solved example JSONs")
        print(f"  - {stats['total_questions']} total questions")
        
        if stats["errors"]:
            print(f"\n⚠ Errors ({len(stats['errors'])}):")
            for error in stats["errors"]:
                print(f"  - {error}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
