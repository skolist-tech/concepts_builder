"""
Supabase upload pipeline.

Handles uploading question banks to Supabase database.
Provides unified upload logic for both solved examples and exercise questions.
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union, Literal

import supabase

from config import settings, get_subject_id
from schemas import (
    SolvedExamplesBank,
    ExerciseQuestionsBank,
    load_solved_bank_json,
    load_exercise_bank_json,
)
from schemas.bank_questions import BaseQuestion
from utils.paths import (
    get_chapter_paths,
    get_chapter_name,
    get_solved_examples_json_path,
    get_exercise_questions_json_path,
)

logger = logging.getLogger(__name__)


# Question type normalization mapping
QUESTION_TYPE_MAP = {
    "mcq": "mcq4",
    "multiple choice": "mcq4",
    "msq": "msq4",
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


def create_supabase_client() -> supabase.Client:
    """Create and return a Supabase client."""
    url = settings.supabase_url
    key = settings.supabase_service_key
    
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_SERVICE_KEY not set in environment")
    
    return supabase.Client(url, key)


async def fetch_chapter_id_by_name(
    client: supabase.Client,
    subject_id: str,
    chapter_name: str
) -> Optional[str]:
    """
    Fetch chapter ID by chapter name for a subject.
    
    Args:
        client: Supabase client instance.
        subject_id: The subject UUID.
        chapter_name: The chapter name to look up.
    
    Returns:
        The chapter UUID or None if not found.
    """
    try:
        def _fetch():
            return (
                client.table("chapters")
                .select("id, name")
                .eq("subject_id", subject_id)
                .execute()
            )
        
        response = await asyncio.get_event_loop().run_in_executor(None, _fetch)
        
        if hasattr(response, 'data') and response.data:
            # Try exact match first
            for chapter in response.data:
                if chapter['name'].lower() == chapter_name.lower():
                    logger.info(f"Found chapter_id for '{chapter_name}': {chapter['id']}")
                    return chapter['id']
            
            # Try partial match (e.g., "Knowing Our Numbers" in "01_knowing_our_numbers")
            chapter_name_lower = chapter_name.lower().replace("_", " ")
            for chapter in response.data:
                if chapter['name'].lower() in chapter_name_lower or chapter_name_lower in chapter['name'].lower():
                    logger.info(f"Found chapter_id for '{chapter_name}' (partial match): {chapter['id']}")
                    return chapter['id']
            
            logger.warning(f"Chapter '{chapter_name}' not found for subject_id {subject_id}")
            logger.debug(f"Available chapters: {[c['name'] for c in response.data]}")
        else:
            logger.warning(f"No chapters found for subject_id {subject_id}")
            
    except Exception as e:
        logger.error(f"Failed to fetch chapter_id: {e}")
    
    return None


async def fetch_concept_id_mapping(
    client: supabase.Client,
    subject_id: str
) -> Dict[str, str]:
    """
    Fetch concept name to ID mapping for a subject.
    
    Args:
        client: Supabase client instance.
        subject_id: The subject UUID.
    
    Returns:
        Dictionary mapping concept names to their UUIDs.
    """
    concept_to_id = {}
    
    try:
        def _fetch():
            return (
                client.table("concepts")
                .select("id, name, topics!inner(chapters!inner(subject_id))")
                .eq("topics.chapters.subject_id", subject_id)
                .execute()
            )
        
        response = await asyncio.get_event_loop().run_in_executor(None, _fetch)
        
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
    question: BaseQuestion,
    subject_id: str,
    is_solved_example: bool,
    chapter_id: Optional[str] = None
) -> dict:
    """
    Convert a question object to a database record.
    
    Args:
        question: The question object (SolvedExample or ExerciseQuestion).
        subject_id: The subject UUID.
        is_solved_example: True if this is a solved example, False for exercise.
        chapter_id: The chapter UUID (optional).
    
    Returns:
        Dictionary ready for database insertion.
    """
    # Generate deterministic ID based on content
    content_fingerprint = f"{subject_id}_{str(question.question_text)}"
    if question.explanation:
        content_fingerprint += f"_{str(question.explanation)}"
    
    question_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, content_fingerprint))
    
    # Determine incompleteness
    is_incomplete = 0
    if is_empty_string(question.question_text):
        is_incomplete = 1
    if is_empty_string(question.explanation):
        is_incomplete = 1
    if question.is_image_needed:
        is_incomplete = 1
    
    return {
        "id": question_id,
        "subject_id": subject_id,
        "chapter_id": chapter_id,
        "question_text": question.question_text,
        "option1": question.option1,
        "option2": question.option2,
        "option3": question.option3,
        "option4": question.option4,
        "match_columns": str(question.match_columns) if question.match_columns else None,
        "svgs": str(question.svgs) if question.svgs else None,
        "correct_mcq_option": question.correct_mcq_option,
        "msq_option1_answer": question.msq_option1_answer,
        "msq_option2_answer": question.msq_option2_answer,
        "msq_option3_answer": question.msq_option3_answer,
        "msq_option4_answer": question.msq_option4_answer,
        "is_true": question.istrue,
        "answer_text": question.answer_text,
        "explanation": question.explanation,
        "hardness_level": question.hardness_level,
        "question_type": normalize_question_type(question.question_type),
        "is_image_needed": 1 if question.is_image_needed else 0,
        "is_solved_example": 1 if is_solved_example else 0,
        "is_from_exercise": 0 if is_solved_example else 1,
        "is_incomplete": is_incomplete,
    }


async def upload_questions_to_supabase(
    client: supabase.Client,
    questions: List[BaseQuestion],
    subject_id: str,
    is_solved_example: bool,
    chapter_name: Optional[str] = None
) -> dict:
    """
    Upload a list of questions to Supabase.
    
    Args:
        client: Supabase client instance.
        questions: List of question objects.
        subject_id: The subject UUID.
        is_solved_example: True if these are solved examples.
        chapter_name: The chapter name to look up chapter_id.
    
    Returns:
        Statistics dictionary with upload results.
    """
    if not questions:
        return {
            "questions_total": 0,
            "questions_upserted": 0,
            "maps_total": 0,
            "maps_upserted": 0,
        }
    
    # Fetch chapter_id if chapter_name is provided
    chapter_id = None
    if chapter_name:
        chapter_id = await fetch_chapter_id_by_name(client, subject_id, chapter_name)
        if not chapter_id:
            logger.warning(f"Could not find chapter_id for '{chapter_name}', proceeding without it")
    
    # Fetch concept mapping
    concept_to_id = await fetch_concept_id_mapping(client, subject_id)
    
    # Use dicts to deduplicate by ID (prevents "cannot affect row a second time" error)
    questions_by_id = {}
    concept_maps_by_id = {}
    duplicate_count = 0
    
    for q in questions:
        record = question_to_db_record(q, subject_id, is_solved_example, chapter_id)
        
        # Deduplicate questions by ID
        if record['id'] not in questions_by_id:
            questions_by_id[record['id']] = record
        else:
            duplicate_count += 1
            question_preview = (q.question_text[:100] + "...") if len(q.question_text or "") > 100 else q.question_text
            logger.warning(f"Duplicate question #{duplicate_count}: '{question_preview}'")
        
        # Create concept mappings
        if q.concepts:
            for concept_name in q.concepts:
                concept_id = concept_to_id.get(concept_name)
                if concept_id:
                    map_id = str(uuid.uuid5(
                        uuid.NAMESPACE_DNS, 
                        f"{record['id']}_{concept_id}"
                    ))
                    # Deduplicate concept maps by ID
                    if map_id not in concept_maps_by_id:
                        concept_maps_by_id[map_id] = {
                            "id": map_id,
                            "concept_id": concept_id,
                            "bank_question_id": record['id'],
                        }
                else:
                    logger.warning(
                        f"Concept '{concept_name}' not found for subject {subject_id}"
                    )
    
    batch_questions = list(questions_by_id.values())
    batch_concept_maps = list(concept_maps_by_id.values())
    
    if len(batch_questions) < len(questions):
        logger.info(f"Deduplicated: {len(questions)} → {len(batch_questions)} unique questions")
    
    # Upload questions
    questions_upserted = 0
    if batch_questions:
        def _upsert_questions():
            # return
            return client.table("bank_questions").upsert(batch_questions).execute()
        
        await asyncio.get_event_loop().run_in_executor(None, _upsert_questions)
        questions_upserted = len(batch_questions)
        logger.info(f"Upserted {questions_upserted} questions")
    
    # Upload concept maps
    maps_upserted = 0
    if batch_concept_maps:
        def _upsert_maps():
            # return
            return client.table("bank_questions_concepts_maps").upsert(batch_concept_maps).execute()
        
        await asyncio.get_event_loop().run_in_executor(None, _upsert_maps)
        maps_upserted = len(batch_concept_maps)
        logger.info(f"Upserted {maps_upserted} concept maps")
    
    return {
        "questions_total": len(questions),
        "questions_upserted": questions_upserted,
        "maps_total": len(batch_concept_maps),
        "maps_upserted": maps_upserted,
    }


async def upload_solved_examples_to_supabase(
    client: supabase.Client,
    solved_bank: SolvedExamplesBank,
    subject_id: str
) -> dict:
    """Upload solved examples bank to Supabase."""
    if not solved_bank or not solved_bank.solved_examples_questions:
        logger.warning("Empty solved examples bank")
        return {"questions_total": 0, "questions_upserted": 0, "maps_total": 0, "maps_upserted": 0}
    
    # Get chapter_name from the bank if available
    chapter_name = getattr(solved_bank, 'chapter_name', None)
    
    return await upload_questions_to_supabase(
        client=client,
        questions=solved_bank.solved_examples_questions,
        subject_id=subject_id,
        is_solved_example=True,
        chapter_name=chapter_name,
    )


async def upload_exercise_questions_to_supabase(
    client: supabase.Client,
    exercise_bank: ExerciseQuestionsBank,
    subject_id: str
) -> dict:
    """Upload exercise questions bank to Supabase."""
    if not exercise_bank or not exercise_bank.exercise_questions:
        logger.warning("Empty exercise questions bank")
        return {"questions_total": 0, "questions_upserted": 0, "maps_total": 0, "maps_upserted": 0}
    
    # Get chapter_name from the bank if available
    chapter_name = getattr(exercise_bank, 'chapter_name', None)
    
    return await upload_questions_to_supabase(
        client=client,
        questions=exercise_bank.exercise_questions,
        subject_id=subject_id,
        is_solved_example=False,
        chapter_name=chapter_name,
    )


async def upload_chapter(
    client: supabase.Client,
    chapter_pdf_path: Path,
    subject_id: str,
    question_type: Literal["solved", "exercise", "both"] = "both"
) -> dict:
    """
    Upload a single chapter's questions to Supabase.
    
    Args:
        client: Supabase client instance.
        chapter_pdf_path: Path to the chapter PDF.
        subject_id: The subject UUID.
        question_type: Which questions to upload.
    
    Returns:
        Combined statistics dictionary.
    """
    chapter_name = get_chapter_name(chapter_pdf_path)
    stats = {
        "chapter": chapter_name,
        "solved": {"questions_total": 0, "questions_upserted": 0, "maps_total": 0, "maps_upserted": 0},
        "exercise": {"questions_total": 0, "questions_upserted": 0, "maps_total": 0, "maps_upserted": 0},
    }
    
    # Upload solved examples
    if question_type in ("solved", "both"):
        json_path = get_solved_examples_json_path(chapter_pdf_path)
        if json_path.exists():
            try:
                bank = await asyncio.to_thread(load_solved_bank_json, str(json_path))
                stats["solved"] = await upload_solved_examples_to_supabase(
                    client, bank, subject_id
                )
                logger.info(f"Uploaded solved examples for {chapter_name}")
            except Exception as e:
                logger.error(f"Failed to upload solved examples for {chapter_name}: {e}")
        else:
            logger.warning(f"Solved examples JSON not found: {json_path}")
    
    # Upload exercise questions
    if question_type in ("exercise", "both"):
        json_path = get_exercise_questions_json_path(chapter_pdf_path)
        if json_path.exists():
            try:
                bank = await asyncio.to_thread(load_exercise_bank_json, str(json_path))
                stats["exercise"] = await upload_exercise_questions_to_supabase(
                    client, bank, subject_id
                )
                logger.info(f"Uploaded exercise questions for {chapter_name}")
            except Exception as e:
                logger.error(f"Failed to upload exercise questions for {chapter_name}: {e}")
        else:
            logger.warning(f"Exercise questions JSON not found: {json_path}")
    
    return stats


async def upload_all_chapters(
    subject_name: str = "maths_6_corodova",
    chapter_paths: Optional[List[Path]] = None,
    question_type: Literal["solved", "exercise", "both"] = "both",
    max_concurrent: int = 1
) -> dict:
    """
    Upload all chapters' questions to Supabase.
    
    Args:
        subject_name: Name of the subject (used to get subject_id).
        chapter_paths: List of chapter paths. Uses default if not provided.
        question_type: Which questions to upload.
        max_concurrent: Maximum concurrent uploads.
    
    Returns:
        Summary statistics dictionary.
    """
    client = create_supabase_client()
    subject_id = get_subject_id(subject_name)
    
    if chapter_paths is None:
        chapter_paths = get_chapter_paths()
    
    # Use semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def upload_with_semaphore(chapter_path: Path) -> dict:
        async with semaphore:
            return await upload_chapter(client, chapter_path, subject_id, question_type)
    
    logger.info(f"Starting upload of {len(chapter_paths)} chapters (concurrency: {max_concurrent})")
    
    tasks = [upload_with_semaphore(path) for path in chapter_paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Aggregate results
    summary = {
        "chapters_processed": 0,
        "chapters_failed": 0,
        "solved": {"questions_total": 0, "questions_upserted": 0, "maps_total": 0, "maps_upserted": 0},
        "exercise": {"questions_total": 0, "questions_upserted": 0, "maps_total": 0, "maps_upserted": 0},
    }
    
    for result in results:
        if isinstance(result, Exception):
            summary["chapters_failed"] += 1
            logger.error(f"Upload failed: {result}")
        else:
            summary["chapters_processed"] += 1
            for key in ("solved", "exercise"):
                for stat_key in summary[key]:
                    summary[key][stat_key] += result[key].get(stat_key, 0)
    
    # Log summary
    logger.info("=" * 50)
    logger.info("UPLOAD SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Chapters: {summary['chapters_processed']}/{len(chapter_paths)} processed")
    logger.info(f"Solved Examples: {summary['solved']['questions_upserted']} questions, {summary['solved']['maps_upserted']} maps")
    logger.info(f"Exercise Questions: {summary['exercise']['questions_upserted']} questions, {summary['exercise']['maps_upserted']} maps")
    logger.info("=" * 50)
    
    return summary
