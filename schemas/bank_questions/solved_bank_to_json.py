import os
import json
import logging

from schemas.bank_questions.question_bank_schema import SolvedExamplesBank

logger = logging.getLogger(__name__)

def solved_bank_to_json(solved_bank: SolvedExamplesBank ) -> str:
    """
    Convert a SolvedExamplesBank object to a JSON string.

    Args:
        solved_bank (SolvedExamplesBank): The solved examples bank object.

    Returns:
        str: JSON string representation of the solved examples bank.
    """
    return solved_bank.model_dump_json(indent=4)

def save_solved_bank_json(solved_bank: SolvedExamplesBank, path: str):
    """
    Save the SolvedExamplesBank object as a JSON file.

    Args:
        solved_bank (SolvedExamplesBank): The solved examples bank object.
        path (str): The file path to save the JSON data.
    """
    json_data = solved_bank_to_json(solved_bank)
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
    
    return question


def load_solved_bank_json(path: str) -> SolvedExamplesBank:
    """
    Load a SolvedExamplesBank object from a JSON file.

    Args:
        path (str): The file path to load the JSON data from.

    Returns:
        SolvedExamplesBank: The parsed SolvedExamplesBank object.
    
    Raises:
        FileNotFoundError: If the JSON file does not exist.
        ValueError: If the JSON is invalid or doesn't match the schema.
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
    
    solved_bank = SolvedExamplesBank.model_validate(data)
    logger.info(f"Loaded SolvedExamplesBank from {path} with {len(solved_bank.solved_examples_questions)} questions")
    return solved_bank