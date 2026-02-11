"""
JSON serialization for solved examples banks with UUID generation.

Handles saving and loading SolvedExamplesBank objects to/from JSON format,
generating deterministic UUIDs during serialization.
"""

import os
import json
import logging
from typing import Dict, Any, List

from schemas.bank_questions.question_bank_schema import SolvedExamplesBank
from utils.uuid_generator import generate_question_id, generate_chapter_id

logger = logging.getLogger(__name__)


def save_solved_bank_json(solved_bank: SolvedExamplesBank, path: str, subject_id: str):
    """
    Save the SolvedExamplesBank object as a JSON file with generated UUIDs.

    Args:
        solved_bank (SolvedExamplesBank): The solved examples bank object.
        path (str): The file path to save the JSON data.
        subject_id (str): Subject UUID for generating question UUIDs.
    """
    # Convert to dict and add UUIDs
    data = solved_bank.model_dump()
    
    # Generate chapter_id
    chapter_id = generate_chapter_id(subject_id, solved_bank.chapter_name)
    data["chapter_id"] = chapter_id
    data["subject_id"] = subject_id
    
    # Generate UUIDs for each question
    for question in data["solved_examples_questions"]:
        question_id = generate_question_id(subject_id, question)
        question["id"] = question_id
    
    # Create directory if needed
    base_dir = os.path.dirname(path)
    if base_dir and not os.path.exists(base_dir):
        os.makedirs(base_dir)
        logger.info(f"Created directory: {base_dir}")
    
    # Save to file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Solved examples bank saved with {len(data['solved_examples_questions'])} questions to {path}")


def _sanitize_question(question: dict) -> dict:
    """
    Sanitize a question dict by replacing null values with defaults for required fields.
    """
    # Default values for required string fields
    if question.get("answer_text") is None:
        question["answer_text"] = ""
    if question.get("explanation") is None:
        question["explanation"] = ""
    if question.get("question_text") is None:
        question["question_text"] = ""
    
    # Default for question_type - use "Short Answer" as fallback
    if question.get("question_type") is None:
        question["question_type"] = "Short Answer"
    
    if question.get("is_image_needed") is None:
        question["is_image_needed"] = 0
    
    return question


def load_solved_bank_json(path: str) -> Dict[str, Any]:
    """
    Load solved examples data from a JSON file including UUIDs.

    Args:
        path (str): The file path to load the JSON data from.

    Returns:
        Dictionary with chapter_id, subject_id, chapter_name and solved_examples_questions list.
        Each question includes its 'id' field.
    
    Raises:
        FileNotFoundError: If the JSON file does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found at {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Sanitize each question to handle null values
    if "solved_examples_questions" in data:
        data["solved_examples_questions"] = [
            _sanitize_question(q) for q in data["solved_examples_questions"]
        ]
    
    logger.info(f"Loaded SolvedExamplesBank from {path} with {len(data.get('solved_examples_questions', []))} questions")
    return data