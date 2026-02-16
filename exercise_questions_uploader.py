#!/usr/bin/env python
"""
Exercise Questions Uploader CLI

Uploads exercise question JSONs (with UUIDs) to Supabase.

Usage:
    python exercise_questions_uploader.py --input_dir <exercise_question_json_directory_path>
"""

import argparse
import asyncio
import logging
import uuid
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from supabase import acreate_client, AsyncClient

from config import setup_logging, settings
from schemas.bank_questions.exercise_bank_to_json import load_exercise_bank_json

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)


# Question type normalization mapping
QUESTION_TYPE_MAP = {
    "mcq": "mcq4",
    "mcq4": "mcq4",
    "multiple choice": "mcq4",
    "msq": "msq4",
    "msq4": "msq4",
    "multiple select": "msq4",
    "short answer": "short_answer",
    "shortanswer": "short_answer",
    "short_answer": "short_answer",
    "long answer": "long_answer",
    "longanswer": "long_answer",
    "long_answer": "long_answer",
    "true false": "true_or_false",
    "true/false": "true_or_false",
    "true or false": "true_or_false",
    "truefalse": "true_or_false",
    "fill in the blanks": "fill_in_the_blanks",
    "fill_in_the_blanks": "fill_in_the_blanks",
    "fillintheblank": "fill_in_the_blanks",
    "fillintheblanks": "fill_in_the_blanks",
    "match": "match_the_following",
    "match the following": "match_the_following",
    "match_the_following": "match_the_following",
    "matchthefollowing": "match_the_following",
}


def normalize_question_type(q_type: Optional[str]) -> Optional[str]:
    """Normalize question type string for database consistency."""
    if not q_type:
        return None
    q_type_lower = q_type.lower().strip()
    return QUESTION_TYPE_MAP.get(q_type_lower, q_type_lower.replace(" ", "_"))


def is_empty_string(s: Optional[str]) -> bool:
    """Check if a string is empty or None."""
    return s is None or str(s).strip() == ""


async def create_supabase_client() -> AsyncClient:
    """Create and return a Supabase async client."""
    url = settings.supabase_url
    key = settings.supabase_service_key
    
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_SERVICE_KEY not set in environment")
    
    return await acreate_client(url, key)


def get_json_files(input_dir: Path) -> List[Path]:
    """Get all exercise question JSON files from the input directory."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    json_files = sorted(input_dir.glob("*_exercise_questions.json"))
    if not json_files:
        raise ValueError(f"No exercise question JSON files found in: {input_dir}")
    
    return json_files


async def fetch_concept_id_mapping(
    client: AsyncClient,
    subject_id: str
) -> Dict[str, str]:
    """Fetch concept name to ID mapping for a subject."""
    concept_to_id = {}
    
    try:
        response = await (
            client.table("concepts")
            .select("id, name, topics!inner(chapters!inner(subject_id))")
            .eq("topics.chapters.subject_id", subject_id)
            .execute()
        )
        
        if hasattr(response, 'data') and response.data:
            for concept in response.data:
                concept_to_id[concept['name']] = concept['id']
        else:
            logger.warning(f"No concepts found for subject_id {subject_id}")
            
    except Exception as e:
        logger.error(f"Failed to fetch concepts: {e}")
        raise
    
    return concept_to_id


def question_to_db_record(
    question: Dict[str, Any],
    subject_id: str,
    chapter_id: Optional[str] = None
) -> Dict[str, Any]:
    """Convert a question dict to a database record."""
    # Use the pre-generated ID from the JSON file
    question_id = question.get("id")
    if not question_id:
        raise ValueError("Question missing 'id' field - regenerate JSON with concepts_builder")
    
    # Determine incompleteness
    is_incomplete = 0
    if is_empty_string(question.get("question_text")):
        is_incomplete = 1
    if is_empty_string(question.get("explanation")):
        is_incomplete = 1
    if question.get("is_image_needed"):
        is_incomplete = 1
    
    return {
        "id": question_id,
        "subject_id": subject_id,
        "chapter_id": chapter_id,
        "question_text": question.get("question_text", ""),
        "option1": question.get("option1"),
        "option2": question.get("option2"),
        "option3": question.get("option3"),
        "option4": question.get("option4"),
        "match_columns": str(question.get("match_columns")) if question.get("match_columns") else None,
        "svgs": str(question.get("svgs")) if question.get("svgs") else None,
        "correct_mcq_option": question.get("correct_mcq_option"),
        "msq_option1_answer": question.get("msq_option1_answer"),
        "msq_option2_answer": question.get("msq_option2_answer"),
        "msq_option3_answer": question.get("msq_option3_answer"),
        "msq_option4_answer": question.get("msq_option4_answer"),
        "is_true": question.get("istrue"),
        "answer_text": question.get("answer_text", ""),
        "explanation": question.get("explanation", ""),
        "hardness_level": question.get("hardness_level", "").lower() if question.get("hardness_level") else None,
        "question_type": normalize_question_type(question.get("question_type")),
        "is_image_needed": 1 if question.get("is_image_needed") else 0,
        "is_solved_example": 0,
        "is_from_exercise": 1,
        "is_incomplete": is_incomplete,
    }


async def upload_exercise_questions_from_json(
    client: AsyncClient,
    json_path: Path
) -> Dict[str, int]:
    """
    Upload exercise questions from a JSON file to Supabase.
    
    Reads UUIDs from the JSON file (question IDs already embedded).
    
    Args:
        client: Supabase client instance.
        json_path: Path to the exercise questions JSON file.
    
    Returns:
        Statistics dictionary with upload results.
    """
    logger.info(f"Loading exercise questions from JSON: {json_path}")
    
    # Load JSON with UUIDs
    data = load_exercise_bank_json(str(json_path))
    
    subject_id = data.get("subject_id")
    chapter_id = data.get("chapter_id")
    chapter_name = data.get("chapter_name", "")
    questions = data.get("exercise_questions", [])
    
    if not subject_id:
        raise ValueError(f"Missing subject_id in JSON - regenerate with exercise_questions_builder")
    
    logger.info(f"Found {len(questions)} exercise questions for chapter: {chapter_name}")
    
    # Fetch concept mapping
    concept_to_id = await fetch_concept_id_mapping(client, subject_id)
    
    # Build question records and concept maps
    questions_by_id = {}
    concept_maps_by_id = {}
    failed_maps_count = 0
    
    for question in questions:
        record = question_to_db_record(question, subject_id, chapter_id)
        
        # Deduplicate by ID
        if record['id'] not in questions_by_id:
            questions_by_id[record['id']] = record
        
        # Create concept mappings
        concepts = question.get("concepts", [])
        for concept_name in concepts:
            concept_id = concept_to_id.get(concept_name)
            if concept_id:
                map_id = str(uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    f"{record['id']}_{concept_id}"
                ))
                if map_id not in concept_maps_by_id:
                    concept_maps_by_id[map_id] = {
                        "id": map_id,
                        "concept_id": concept_id,
                        "bank_question_id": record['id'],
                    }
            else:
                logger.warning(f"Concept '{concept_name}' not found for subject {subject_id}")
                failed_maps_count += 1
    
    batch_questions = list(questions_by_id.values())
    batch_concept_maps = list(concept_maps_by_id.values())
    
    # Upload questions
    questions_upserted = 0
    if batch_questions:
        try:
            await client.table("bank_questions").upsert(batch_questions).execute()
            questions_upserted = len(batch_questions)
            logger.info(f"Upserted {questions_upserted} questions")
        except Exception as e:
            logger.error(f"Failed to upsert questions: {e}")
            raise
    
    # Upload concept maps
    maps_upserted = 0
    if batch_concept_maps:
        try:
            await client.table("bank_questions_concepts_maps").upsert(batch_concept_maps).execute()
            maps_upserted = len(batch_concept_maps)
            logger.info(f"Upserted {maps_upserted} concept maps")
        except Exception as e:
            logger.error(f"Failed to upsert concept maps: {e}")
            raise
    
    return {
        "chapter_name": chapter_name,
        "questions": questions_upserted,
        "concept_maps": maps_upserted,
        "failed_maps": failed_maps_count,
    }


async def upload_all_exercise_questions(input_dir: Path) -> None:
    """Upload all exercise question JSONs from the input directory."""
    json_files = get_json_files(input_dir)
    logger.info(f"Found {len(json_files)} exercise question JSON files to upload")
    
    client = await create_supabase_client()
    
    total_questions = 0
    total_maps = 0
    total_failed_maps = 0
    successful = 0
    failed = 0
    
    # Track per-chapter results for summary (both successful and failed)
    chapter_results: List[Dict[str, Any]] = []
    
    for i, json_path in enumerate(json_files, 1):
        logger.info(f"[{i}/{len(json_files)}] Uploading: {json_path.name}")
        
        try:
            stats = await upload_exercise_questions_from_json(client, json_path)
            total_questions += stats["questions"]
            total_maps += stats["concept_maps"]
            total_failed_maps += stats["failed_maps"]
            successful += 1
            chapter_results.append({
                "name": stats["chapter_name"],
                "questions": stats["questions"],
                "concept_maps": stats["concept_maps"],
                "failed_maps": stats["failed_maps"],
                "failed": False,
            })
        except Exception as e:
            logger.error(f"[{i}/{len(json_files)}] Failed: {json_path.name} - {e}")
            failed += 1
            # Extract chapter name from filename (remove suffix and leading numbers)
            chapter_name = json_path.stem.replace("_exercise_questions", "").lstrip("0123456789_")
            chapter_results.append({
                "name": chapter_name,
                "questions": 0,
                "concept_maps": 0,
                "failed_maps": 0,
                "failed": True,
            })
    
    # Log per-chapter summary
    logger.info("=" * 60)
    logger.info("UPLOAD SUMMARY")
    logger.info("=" * 60)
    for idx, result in enumerate(chapter_results, 1):
        line = f"  {idx:2}. {result['name']:<40} | Questions: {result['questions']:3} | Maps: {result['concept_maps']:3}"
        if result["failed"]:
            logger.error(f"{line}  [FAILED]")
        elif result["failed_maps"] > 0:
            logger.info(line)
            logger.error(f"      {'':40}   Failed Maps: {result['failed_maps']:3}")
        else:
            logger.info(line)
    
    logger.info("=" * 60)
    if failed > 0:
        logger.error(f"Upload complete: {successful} successful, {failed} failed")
    else:
        logger.info(f"Upload complete: {successful} successful, {failed} failed")
    logger.info(f"Total: {total_questions} questions, {total_maps} concept maps")
    if total_failed_maps > 0:
        logger.error(f"Total failed concept maps: {total_failed_maps}")


def main():
    parser = argparse.ArgumentParser(
        description="Upload exercise question JSONs (with UUIDs) to Supabase"
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Directory containing exercise question JSON files"
    )
    
    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    
    logger.info(f"Input directory: {input_dir}")
    
    try:
        asyncio.run(upload_all_exercise_questions(input_dir))
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
