#!/usr/bin/env python
"""
Sync Chapter Info Script

Reads chapter_name and chapter_id from concept CSV files and applies them
to the corresponding exercise_questions.json and solved_examples.json files.

Usage:
    python sync_chapter_info.py --input_dir <directory_path>
    python sync_chapter_info.py --input_dir <directory_path> --dry-run
"""

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_csv_chapter_info(csv_path: Path) -> Optional[Dict[str, str]]:
    """Load chapter_name and chapter_id from a concepts CSV."""
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            logger.warning(f"Empty CSV: {csv_path}")
            return None
        
        first_row = rows[0]
        return {
            "chapter_name": first_row.get("chapter_name", "").strip(),
            "chapter_id": first_row.get("chapter_id", "").strip(),
        }
    except Exception as e:
        logger.error(f"Failed to read CSV {csv_path}: {e}")
        return None


def update_json_chapter_info(
    json_path: Path, 
    chapter_name: str, 
    chapter_id: str,
    dry_run: bool = False
) -> bool:
    """
    Update chapter_name and chapter_id in a JSON file.
    
    Returns True if changes were made (or would be made in dry-run), False otherwise.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        current_name = data.get("chapter_name", "")
        current_id = data.get("chapter_id", "")
        
        changes_needed = False
        
        if current_name != chapter_name:
            logger.info(f"  chapter_name: '{current_name}' -> '{chapter_name}'")
            changes_needed = True
        
        if current_id != chapter_id:
            logger.info(f"  chapter_id: '{current_id}' -> '{chapter_id}'")
            changes_needed = True
        
        if not changes_needed:
            return False
        
        if dry_run:
            logger.info(f"  [DRY-RUN] Would update {json_path.name}")
            return True
        
        # Apply changes
        data["chapter_name"] = chapter_name
        data["chapter_id"] = chapter_id
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"  Updated {json_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update {json_path}: {e}")
        return False


def process_directory(input_dir: Path, dry_run: bool = False) -> Dict[str, int]:
    """
    Process all CSV files in a directory and sync chapter info to JSONs.
    
    Returns stats dict with counts.
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Directory not found: {input_dir}")
    
    csv_files = sorted(input_dir.glob("*_concepts.csv"))
    if not csv_files:
        raise ValueError(f"No concept CSV files found in: {input_dir}")
    
    stats = {
        "total_chapters": 0,
        "chapters_updated": 0,
        "files_updated": 0,
        "files_skipped": 0,
        "errors": 0,
    }
    
    logger.info(f"Found {len(csv_files)} concept CSV files")
    logger.info("=" * 70)
    
    for csv_path in csv_files:
        stats["total_chapters"] += 1
        prefix = csv_path.stem.replace("_concepts", "")
        
        # Load chapter info from CSV
        chapter_info = load_csv_chapter_info(csv_path)
        if not chapter_info:
            stats["errors"] += 1
            continue
        
        chapter_name = chapter_info["chapter_name"]
        chapter_id = chapter_info["chapter_id"]
        
        if not chapter_name:
            logger.warning(f"Skipping {prefix}: No chapter_name in CSV")
            stats["errors"] += 1
            continue
        
        logger.info(f"Processing: {prefix}")
        logger.info(f"  CSV chapter_name: '{chapter_name}'")
        logger.info(f"  CSV chapter_id: '{chapter_id}'")
        
        chapter_updated = False
        
        # Update exercise JSON
        exercise_json = input_dir / f"{prefix}_exercise_questions.json"
        if exercise_json.exists():
            if update_json_chapter_info(exercise_json, chapter_name, chapter_id, dry_run):
                stats["files_updated"] += 1
                chapter_updated = True
            else:
                stats["files_skipped"] += 1
        
        # Update solved examples JSON
        solved_json = input_dir / f"{prefix}_solved_examples.json"
        if solved_json.exists():
            if update_json_chapter_info(solved_json, chapter_name, chapter_id, dry_run):
                stats["files_updated"] += 1
                chapter_updated = True
            else:
                stats["files_skipped"] += 1
        
        if chapter_updated:
            stats["chapters_updated"] += 1
        
        logger.info("")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Sync chapter_name and chapter_id from CSVs to JSON files"
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Directory containing concept CSVs and question JSONs"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without actually modifying files"
    )
    
    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    
    if args.dry_run:
        logger.info("DRY-RUN MODE: No files will be modified")
        logger.info("")
    
    try:
        stats = process_directory(input_dir, dry_run=args.dry_run)
        
        logger.info("=" * 70)
        logger.info("SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total chapters processed: {stats['total_chapters']}")
        logger.info(f"Chapters with updates:    {stats['chapters_updated']}")
        logger.info(f"JSON files updated:       {stats['files_updated']}")
        logger.info(f"JSON files unchanged:     {stats['files_skipped']}")
        if stats['errors'] > 0:
            logger.error(f"Errors:                   {stats['errors']}")
        
        if args.dry_run and stats['files_updated'] > 0:
            logger.info("")
            logger.info("Run without --dry-run to apply these changes.")
        
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
