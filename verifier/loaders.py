"""
File loading utilities for the verifier package.

This module provides functions for loading and parsing concept CSVs and question JSON files,
as well as applying concept replacements.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def get_file_groups(input_dir: Path) -> List[Dict[str, Optional[Path]]]:
    """
    Group related files by chapter prefix.
    
    Scans the input directory for concept CSV files and finds their corresponding
    exercise questions and solved examples JSON files.
    
    Args:
        input_dir: Directory containing the concept CSVs and question JSONs.
        
    Returns:
        List of dictionaries, each containing:
            - 'prefix': The chapter prefix (e.g., "01_knowing_our_numbers")
            - 'concepts_csv': Path to the concepts CSV file
            - 'exercise_json': Path to exercise questions JSON (or None if not found)
            - 'solved_json': Path to solved examples JSON (or None if not found)
            
    Raises:
        FileNotFoundError: If the input directory does not exist.
        ValueError: If no concept CSV files are found in the directory.
        
    Example:
        >>> groups = get_file_groups(Path("data/output"))
        >>> groups[0]
        {'prefix': '01_numbers', 'concepts_csv': Path(...), 'exercise_json': Path(...), 'solved_json': Path(...)}
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    csv_files = sorted(input_dir.glob("*_concepts.csv"))
    if not csv_files:
        raise ValueError(f"No concept CSV files found in: {input_dir}")
    
    groups = []
    for csv_file in csv_files:
        # Extract prefix (e.g., "01_knowing_our_numbers" from "01_knowing_our_numbers_concepts.csv")
        prefix = csv_file.stem.replace("_concepts", "")
        
        exercise_json = input_dir / f"{prefix}_exercise_questions.json"
        solved_json = input_dir / f"{prefix}_solved_examples.json"
        
        groups.append({
            "prefix": prefix,
            "concepts_csv": csv_file,
            "exercise_json": exercise_json if exercise_json.exists() else None,
            "solved_json": solved_json if solved_json.exists() else None,
        })
    
    return groups


def load_csv_chapter_info(csv_path: Path) -> Dict[str, Any]:
    """
    Load chapter info and concept names from a concepts CSV.
    
    Parses a concepts CSV file to extract chapter metadata and all concept definitions.
    Also validates internal consistency (all rows should have same chapter_name/chapter_id).
    
    Args:
        csv_path: Path to the concepts CSV file.
        
    Returns:
        Dictionary containing:
            - 'chapter_name': The chapter name from the first row
            - 'chapter_id': The chapter ID from the first row
            - 'chapter_position': The chapter position/number from the first row
            - 'concepts': Set of all concept names in the CSV
            - 'concepts_with_desc': Dict mapping concept names to their descriptions
            - 'internal_inconsistencies': List of any row-level inconsistencies found
            
    Example:
        >>> info = load_csv_chapter_info(Path("01_numbers_concepts.csv"))
        >>> info['chapter_name']
        'Knowing Our Numbers'
        >>> len(info['concepts'])
        15
    """
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        return {
            "chapter_name": None,
            "chapter_id": None,
            "chapter_position": None,
            "concepts": set(),
            "concepts_with_desc": {},
            "internal_inconsistencies": [],
        }
    
    first_row = rows[0]
    chapter_name = first_row.get("chapter_name", "").strip()
    chapter_id = first_row.get("chapter_id", "").strip()
    chapter_position = first_row.get("chapter_position", "").strip()
    
    # Check all rows have consistent chapter_name and chapter_id
    internal_inconsistencies = []
    concepts = set()
    concepts_with_desc = {}
    
    for i, row in enumerate(rows, 1):
        row_chapter_name = row.get("chapter_name", "").strip()
        row_chapter_id = row.get("chapter_id", "").strip()
        concept_name = row.get("concept_name", "").strip()
        concept_desc = row.get("concept_description", "").strip()
        
        if concept_name:
            concepts.add(concept_name)
            concepts_with_desc[concept_name] = concept_desc

        if row_chapter_name != chapter_name:
            internal_inconsistencies.append(
                f"Row {i}: chapter_name '{row_chapter_name}' != first row '{chapter_name}'"
            )
        
        if row_chapter_id != chapter_id:
            internal_inconsistencies.append(
                f"Row {i}: chapter_id '{row_chapter_id}' != first row '{chapter_id}'"
            )
    
    return {
        "chapter_name": chapter_name,
        "chapter_id": chapter_id,
        "chapter_position": chapter_position,
        "concepts": concepts,
        "concepts_with_desc": concepts_with_desc,
        "internal_inconsistencies": internal_inconsistencies,
    }


def load_json_info(json_path: Path, questions_key: str) -> Dict[str, Any]:
    """
    Load chapter info and concept references from a JSON file.
    
    Parses a questions JSON file (exercise or solved examples) to extract
    chapter metadata and all concepts referenced by questions.
    
    Args:
        json_path: Path to the JSON file.
        questions_key: Key to access the questions list (e.g., 'exercise_questions'
                      or 'solved_examples_questions').
        
    Returns:
        Dictionary containing:
            - 'chapter_name': The chapter name from the JSON
            - 'chapter_id': The chapter ID from the JSON
            - 'concepts_referenced': Set of all concept names referenced by questions
            - 'question_count': Number of questions in the file
            
    Example:
        >>> info = load_json_info(Path("01_numbers_exercise_questions.json"), "exercise_questions")
        >>> info['question_count']
        25
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    concepts_referenced = set()
    questions = data.get(questions_key, [])
    for question in questions:
        for concept in question.get("concepts", []):
            if concept:
                concepts_referenced.add(concept.strip())
    
    return {
        "chapter_name": data.get("chapter_name", "").strip(),
        "chapter_id": data.get("chapter_id", "").strip(),
        "concepts_referenced": concepts_referenced,
        "question_count": len(questions),
    }


def load_json_questions_with_concepts(json_path: Path, questions_key: str) -> List[Dict[str, Any]]:
    """
    Load questions with their text and concepts for suggestion purposes.
    
    Parses a questions JSON file and returns detailed question information
    that can be used for AI-based concept suggestions.
    
    Args:
        json_path: Path to the JSON file.
        questions_key: Key to access the questions list (e.g., 'exercise_questions').
        
    Returns:
        List of dictionaries, each containing:
            - 'question_index': 1-based index of the question
            - 'question_text': The question text content
            - 'concepts': List of concept names associated with the question
            
    Example:
        >>> questions = load_json_questions_with_concepts(Path("exercises.json"), "exercise_questions")
        >>> questions[0]
        {'question_index': 1, 'question_text': 'What is...', 'concepts': ['Numbers', 'Addition']}
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    result = []
    questions = data.get(questions_key, [])
    for idx, question in enumerate(questions, 1):
        question_text = question.get("question_text", "").strip()
        concepts = [c.strip() for c in question.get("concepts", []) if c]
        result.append({
            "question_index": idx,
            "question_text": question_text,
            "concepts": concepts,
        })
    return result


def apply_concept_replacement(
    json_path: Path,
    questions_key: str,
    question_index: int,
    old_concept: str,
    new_concept: str,
) -> bool:
    """
    Replace a concept in a specific question within a JSON file.
    
    Finds a question by index, locates the old concept in its concepts list,
    and replaces it with the new concept. The file is written back with the change.
    
    Args:
        json_path: Path to the JSON file to modify.
        questions_key: Key to access the questions list (e.g., 'exercise_questions').
        question_index: 1-based index of the question to modify.
        old_concept: The concept name to replace.
        new_concept: The replacement concept name.
        
    Returns:
        True if replacement was successful, False otherwise.
        
    Note:
        This function modifies the file in place. Only the first occurrence
        of the old concept in the question's concepts list is replaced.
        
    Example:
        >>> success = apply_concept_replacement(
        ...     Path("exercises.json"),
        ...     "exercise_questions",
        ...     question_index=5,
        ...     old_concept="Numbrs",  # typo
        ...     new_concept="Numbers"
        ... )
        >>> success
        True
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        questions = data.get(questions_key, [])
        if question_index < 1 or question_index > len(questions):
            logger.error(f"Question index {question_index} out of range for {json_path}")
            return False
        
        question = questions[question_index - 1]  # Convert to 0-based index
        concepts = question.get("concepts", [])
        
        # Find and replace the concept
        replaced = False
        for i, concept in enumerate(concepts):
            if concept.strip() == old_concept.strip():
                concepts[i] = new_concept
                replaced = True
                break
        
        if not replaced:
            logger.warning(f"Concept '{old_concept}' not found in question {question_index}")
            return False
        
        question["concepts"] = concepts
        
        # Write back to file
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply replacement in {json_path}: {e}")
        return False
