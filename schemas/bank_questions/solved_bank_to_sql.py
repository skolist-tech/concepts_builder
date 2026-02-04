import os
import logging
import asyncio
import uuid
from typing import Dict, List, Any, Optional

import uuid6
import supabase
from dotenv import load_dotenv

from schemas.bank_questions import SolvedExamplesBank

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


async def concept_to_id_in_subject(client: supabase.Client, subject_id: str) -> Dict[str, str]:
    """
    Fetch concept to ID mapping for concepts in a given subject from the database.
    Concepts are linked to subjects through topics and chapters: concepts -> topic -> chapter -> subject

    Args:
        client (supabase.Client): The Supabase client instance.
        subject_id (str): The subject ID to fetch concepts for.

    Returns:
        dict: A dictionary mapping concept names to their IDs.
    """
    concept_to_id_dict = {}
    try:
        # Run database query in thread pool to avoid blocking
        def _fetch_concepts():
            return client.table("concepts").select("id, name, topics!inner(chapters!inner(subject_id))").eq("topics.chapters.subject_id", subject_id).execute()
        
        response = await asyncio.get_event_loop().run_in_executor(None, _fetch_concepts)
        
        # Handle different response formats
        if hasattr(response, 'data') and response.data is not None:
            concepts = response.data
            for concept in concepts:
                concept_to_id_dict[concept['name']] = concept['id']
        else:
            logger.warning(f"No concepts found for subject_id {subject_id}")
            
    except Exception as e:
        logger.error(f"Exception occurred while fetching concepts: {e}")
        raise e
    
    return concept_to_id_dict



def normalize_question_type(q_type: Optional[str]) -> Optional[str]:
    if not q_type:
        return None
    
    q_type_lower = q_type.lower().strip()
    
    mapping = {
        "mcq": "mcq4",
        "multiple choice": "mcq4",
        "msq": "msq4",
        "multiple select": "msq4",
        "short answer": "short_answer",
        "shortanswer" : "short_answer",
        "short_answer": "short_answer",
        "long answer": "long_answer",
        "longanswer" : "long_answer",
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
    
    return mapping.get(q_type_lower, q_type_lower.replace(" ", "_"))

async def upload_solved_bank_to_supabase(
    client: supabase.Client, 
    solved_bank: SolvedExamplesBank, 
    subject_id: str
) -> dict:
    """
    Convert a SolvedExamplesBank object to dictionary records and upload to Supabase.

    Args:
        client (supabase.Client): The Supabase client instance.
        solved_bank (SolvedExamplesBank): The solved examples bank object.
        subject_id (str): The subject ID for the questions.

    Returns:
        int: Number of questions uploaded.
    """
    if not solved_bank:
        logger.warning("Solved bank is empty.")
        return 0
    if not solved_bank.solved_examples_questions:
        logger.warning("No examples found in the solved bank.")
        return 0
    
    # helper for checking empty strings
    def is_empty(s: Optional[str]) -> bool:
        return s is None or str(s).strip() == ""

    try:
        # Fetch concept mappings
        concept_to_id_dict = await concept_to_id_in_subject(client=client, subject_id=subject_id)
        
        batch_questions = []
        batch_concept_maps = []
        

        for q in solved_bank.solved_examples_questions:
            # Generate deterministic ID to prevent duplicates on re-runs
            # We use subject_id, question_text, and explanation to create a unique fingerprint
            # If the source content is the same, the ID will be identical, allowing consistent updates (upsert)
            content_fingerprint = f"{subject_id}_{str(q.question_text)}"
            # Append explanation to fingerprint if available for added uniqueness (e.g. same question text, different context)
            if q.explanation:
                content_fingerprint += f"_{str(q.explanation)}"
            
            question_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, content_fingerprint))

            # Determine is_incomplete status
            is_incomplete = 0
            if is_empty(q.question_text):
                is_incomplete = 1
            if is_empty(q.explanation):
                is_incomplete = 1
            if q.is_image_needed: # If True/1
                is_incomplete = 1
            
            # Prepare question record
            question_record = {
                "id": question_id,
                "subject_id": subject_id,
                "question_text": q.question_text,
                "option1": q.option1,
                "option2": q.option2,
                "option3": q.option3,
                "option4": q.option4,
                "match_columns": str(q.match_columns) if q.match_columns else None,
                "svgs": str(q.svgs) if q.svgs else None,
                "correct_mcq_option": q.correct_mcq_option,
                "msq_option1_answer": q.msq_option1_answer,
                "msq_option2_answer": q.msq_option2_answer,
                "msq_option3_answer": q.msq_option3_answer,
                "msq_option4_answer": q.msq_option4_answer,
                "is_true": q.istrue,
                "answer_text": q.answer_text,
                "explanation": q.explanation,
                "hardness_level": q.hardness_level,
                "question_type": normalize_question_type(q.question_type),
                "is_image_needed": 1 if q.is_image_needed else 0,
                "is_solved_example": 1,
                "is_from_exercise": 0,
                "is_incomplete": is_incomplete
            }
            batch_questions.append(question_record)
            
            # Prepare concept maps
            if q.concepts:
                for concept_name in q.concepts:
                    concept_id = concept_to_id_dict.get(concept_name)
                    if concept_id:
                        # Deterministic ID for the map relation
                        map_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{question_id}_{concept_id}"))
                        batch_concept_maps.append({
                            "id": map_id,
                            "concept_id": concept_id,
                            "bank_question_id": question_id
                        })
                    else:
                        logger.warning(f"Concept '{concept_name}' not found in database for subject {subject_id}")

        # Execute inserts in thread pool
        questions_upserted = 0
        maps_upserted = 0

        if batch_questions:
            def _insert_questions():
                return client.table("bank_questions").upsert(batch_questions).execute()
            
            # execute returns postgrest.APIResponse, not just data directly depending on version, 
            # usually it has .data matching the upserted rows if select() is implied or returned.
            # Upsert counts are generally the length of the batch if successful.
            await asyncio.get_event_loop().run_in_executor(None, _insert_questions)
            questions_upserted = len(batch_questions)
            logger.info(f"Chapter Questions: {len(batch_questions)} prepared, {questions_upserted} upserted.")

        if batch_concept_maps:
            def _insert_maps():
                return client.table("bank_questions_concepts_maps").upsert(batch_concept_maps).execute()
            
            await asyncio.get_event_loop().run_in_executor(None, _insert_maps)
            maps_upserted = len(batch_concept_maps)
            logger.info(f"Chapter Concept Maps: {len(batch_concept_maps)} prepared, {maps_upserted} upserted.")

        return {
            "questions_total": len(solved_bank.solved_examples_questions),
            "questions_upserted": questions_upserted,
            "maps_total": len(batch_concept_maps), # Total maps prepared
            "maps_upserted": maps_upserted
        }

    except Exception as e:
        logger.error(f"Error uploading solved bank to Supabase: {e}")
        # Re-raise to alert caller
        raise e