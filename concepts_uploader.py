#!/usr/bin/env python
"""
Concepts Uploader CLI

Uploads concept CSVs (with UUIDs) to Supabase.

Usage:
    python concepts_uploader.py --input_dir <concept_csv_directory_path>
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

import supabase

from config import setup_logging, settings
from schemas.chapter_to_csv import load_csv_with_uuids

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)


def create_supabase_client() -> supabase.Client:
    """Create and return a Supabase client."""
    url = settings.supabase_url
    key = settings.supabase_service_key
    
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_SERVICE_KEY not set in environment")
    
    return supabase.Client(url, key)


def get_csv_files(input_dir: Path) -> List[Path]:
    """Get all concept CSV files from the input directory."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    csv_files = sorted(input_dir.glob("*_concepts.csv"))
    if not csv_files:
        raise ValueError(f"No concept CSV files found in: {input_dir}")
    
    return csv_files


async def upload_concepts_from_csv(
    client: supabase.Client,
    csv_path: Path
) -> Dict[str, int]:
    """
    Upload concepts from a CSV file to Supabase.
    
    Reads UUIDs from the CSV file (chapter_id, topic_id, concept_id).
    
    Args:
        client: Supabase client instance.
        csv_path: Path to the concepts CSV file.
    
    Returns:
        Statistics dictionary with upload results.
    """
    logger.info(f"Loading concepts from CSV: {csv_path}")
    
    # Load CSV with UUIDs
    data = load_csv_with_uuids(str(csv_path))
    
    subject_id = data["subject_id"]
    chapter_data = data["chapter"]
    topics_data = data["topics"]
    concepts_data = data["concepts"]
    
    logger.info(f"Found {len(concepts_data)} concepts in {len(topics_data)} topics")
    
    # Create chapter record
    chapter_record = {
        "id": chapter_data["id"],
        "name": chapter_data["name"],
        "description": chapter_data["description"] or "",
        "subject_id": subject_id,
        "position": chapter_data["position"],
    }
    
    # Create topic records
    topic_records = [
        {
            "id": topic["id"],
            "name": topic["name"],
            "description": topic["description"] or "",
            "chapter_id": topic["chapter_id"],
            "position": topic["position"],
        }
        for topic in topics_data.values()
    ]
    
    # Create concept records
    concept_records = [
        {
            "id": concept["id"],
            "name": concept["name"],
            "description": concept["description"] or "",
            "topic_id": concept["topic_id"],
            "page_number": concept["page_number"],
        }
        for concept in concepts_data
    ]
    
    # Upload chapter
    chapters_upserted = 0
    try:
        def _upsert_chapter():
            return client.table("chapters").upsert(chapter_record).execute()
        
        await asyncio.get_event_loop().run_in_executor(None, _upsert_chapter)
        chapters_upserted = 1
        logger.info(f"Upserted chapter: {chapter_data['name']} (id: {chapter_data['id']})")
    except Exception as e:
        logger.error(f"Failed to upsert chapter: {e}")
        raise
    
    # Upload topics
    topics_upserted = 0
    if topic_records:
        try:
            def _upsert_topics():
                return client.table("topics").upsert(topic_records).execute()
            
            await asyncio.get_event_loop().run_in_executor(None, _upsert_topics)
            topics_upserted = len(topic_records)
            logger.info(f"Upserted {topics_upserted} topics")
        except Exception as e:
            logger.error(f"Failed to upsert topics: {e}")
            raise
    
    # Upload concepts
    concepts_upserted = 0
    if concept_records:
        try:
            def _upsert_concepts():
                return client.table("concepts").upsert(concept_records).execute()
            
            await asyncio.get_event_loop().run_in_executor(None, _upsert_concepts)
            concepts_upserted = len(concept_records)
            logger.info(f"Upserted {concepts_upserted} concepts")
        except Exception as e:
            logger.error(f"Failed to upsert concepts: {e}")
            raise
    
    return {
        "chapter_name": chapter_data["name"],
        "chapters": chapters_upserted,
        "topics": topics_upserted,
        "concepts": concepts_upserted,
    }


async def upload_all_concepts(input_dir: Path) -> None:
    """Upload all concept CSVs from the input directory."""
    csv_files = get_csv_files(input_dir)
    logger.info(f"Found {len(csv_files)} concept CSV files to upload")
    
    client = create_supabase_client()
    
    total_chapters = 0
    total_topics = 0
    total_concepts = 0
    successful = 0
    failed = 0
    
    # Track per-chapter results for summary
    chapter_results: List[Dict[str, Any]] = []
    failed_chapters: List[str] = []
    
    for i, csv_path in enumerate(csv_files, 1):
        logger.info(f"[{i}/{len(csv_files)}] Uploading: {csv_path.name}")
        
        try:
            stats = await upload_concepts_from_csv(client, csv_path)
            total_chapters += stats["chapters"]
            total_topics += stats["topics"]
            total_concepts += stats["concepts"]
            successful += 1
            chapter_results.append({
                "name": stats["chapter_name"],
                "topics": stats["topics"],
                "concepts": stats["concepts"],
            })
        except Exception as e:
            logger.error(f"[{i}/{len(csv_files)}] Failed: {csv_path.name} - {e}")
            failed += 1
            failed_chapters.append(csv_path.name)
    
    # Log per-chapter summary
    logger.info("=" * 60)
    logger.info("UPLOAD SUMMARY")
    logger.info("=" * 60)
    for idx, result in enumerate(chapter_results, 1):
        logger.info(
            f"  {idx:2}. {result['name']:<40} | Topics: {result['topics']:3} | Concepts: {result['concepts']:3}"
        )
    
    # Log failed chapters if any
    if failed_chapters:
        logger.info("-" * 60)
        logger.error("FAILED CHAPTERS:")
        for chapter_file in failed_chapters:
            logger.error(f"  - {chapter_file}")
    
    logger.info("=" * 60)
    if failed > 0:
        logger.error(f"Upload complete: {successful} successful, {failed} failed")
    else:
        logger.info(f"Upload complete: {successful} successful, {failed} failed")
    logger.info(f"Total: {total_chapters} chapters, {total_topics} topics, {total_concepts} concepts")


def main():
    parser = argparse.ArgumentParser(
        description="Upload concept CSVs (with UUIDs) to Supabase"
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Directory containing concept CSV files"
    )
    
    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    
    logger.info(f"Input directory: {input_dir}")
    
    try:
        asyncio.run(upload_all_concepts(input_dir))
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
