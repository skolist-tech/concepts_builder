"""
JSON serialization for exercise questions banks.

Handles saving and loading ExerciseQuestionsBank objects to/from JSON format.
"""

import os
import json
import logging


from schemas.bank_questions.question_bank_schema import ExerciseQuestionsBank

logger = logging.getLogger(__name__)

def exercise_bank_to_json(exercise_bank: ExerciseQuestionsBank ) -> str:
    """
    Convert a ExerciseQuestionsBank object to a JSON string.

    Args:
        exercise_bank (ExerciseQuestionsBank): The exercise questions bank object.

    Returns:
        str: JSON string representation of the exercise questions bank.
    """
    return exercise_bank.model_dump_json(indent=4)

def save_exercise_bank_json(exercise_bank: ExerciseQuestionsBank, path: str):
    """
    Save the ExerciseQuestionsBank object as a JSON file.

    Args:
        exercise_bank (ExerciseQuestionsBank): The exercise questions bank object.
        path (str): The file path to save the JSON data.
    """
    json_data = exercise_bank_to_json(exercise_bank)
    base_dir = os.path.dirname(path)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        logger.info(f"Created directory: {base_dir}")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(json_data)


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


def load_exercise_bank_json(path: str) -> ExerciseQuestionsBank:
    """
    Load a ExerciseQuestionsBank object from a JSON file.

    Args:
        path (str): The file path to load the JSON data from.

    Returns:
        ExerciseQuestionsBank: The parsed ExerciseQuestionsBank object.
    
    Raises:
        FileNotFoundError: If the JSON file does not exist.
        ValueError: If the JSON is invalid or doesn't match the schema.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found at {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Sanitize each question to handle null values
    if "exercise_questions" in data:
        data["exercise_questions"] = [
            _sanitize_question(q) for q in data["exercise_questions"]
        ]
    
    exercise_bank = ExerciseQuestionsBank.model_validate(data)
    logger.info(f"Loaded ExerciseQuestionsBank from {path} with {len(exercise_bank.exercise_questions)} questions")
    return exercise_bank
