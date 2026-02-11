"""
UUID Migration Utility.

Adds deterministic UUIDs to existing CSV and JSON files that don't have them.
This is useful for migrating legacy data to the new UUID-based system.

Usage:
    python -m utils.add_uuids_to_existing --help
"""

import os
import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from utils.uuid_generator import (
    generate_chapter_id,
    generate_topic_id,
    generate_concept_id,
    generate_question_id
)

logger = logging.getLogger(__name__)


def add_uuids_to_concepts_csv(
    input_csv_path: str,
    output_csv_path: str,
    subject_id: str
) -> Dict[str, int]:
    """
    Add UUIDs to an existing concepts CSV file.
    
    Reads a CSV with columns: concept_name, concept_description, concept_page_number,
    topic_name, topic_description, topic_position, chapter_name, chapter_description,
    chapter_position
    
    Outputs a CSV with additional columns: concept_id, topic_id, chapter_id, subject_id
    
    Args:
        input_csv_path: Path to the input CSV without UUIDs.
        output_csv_path: Path to save the output CSV with UUIDs.
        subject_id: Subject UUID for generating deterministic UUIDs.
    
    Returns:
        Statistics dict with counts of processed rows.
    
    Raises:
        FileNotFoundError: If input CSV doesn't exist.
        ValueError: If required columns are missing.
    """
    input_path = Path(input_csv_path)
    output_path = Path(output_csv_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv_path}")
    
    # Read input CSV
    with open(input_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        input_fieldnames = reader.fieldnames or []
    
    if not rows:
        raise ValueError(f"Empty CSV: {input_csv_path}")
    
    # Check required columns
    required_columns = ["concept_name", "topic_name", "chapter_name"]
    missing = [col for col in required_columns if col not in input_fieldnames]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Check if UUIDs already exist
    if "concept_id" in input_fieldnames:
        logger.warning(f"CSV already has UUID columns: {input_csv_path}")
    
    # Define output columns (UUIDs first for clarity)
    output_fieldnames = [
        "concept_id",
        "concept_name",
        "concept_description",
        "concept_page_number",
        "topic_id",
        "topic_name",
        "topic_description",
        "topic_position",
        "chapter_id",
        "chapter_name",
        "chapter_description",
        "chapter_position",
        "subject_id",
    ]
    
    # Cache for generated UUIDs to ensure consistency
    chapter_ids: Dict[str, str] = {}
    topic_ids: Dict[str, str] = {}
    
    output_rows = []
    for row in rows:
        chapter_name = row.get("chapter_name", "")
        topic_name = row.get("topic_name", "")
        concept_name = row.get("concept_name", "")
        
        # Generate or retrieve chapter_id
        if chapter_name not in chapter_ids:
            chapter_ids[chapter_name] = generate_chapter_id(subject_id, chapter_name)
        chapter_id = chapter_ids[chapter_name]
        
        # Generate or retrieve topic_id (using chapter_id + topic_name as key)
        topic_key = f"{chapter_id}:{topic_name}"
        if topic_key not in topic_ids:
            topic_ids[topic_key] = generate_topic_id(chapter_id, topic_name)
        topic_id = topic_ids[topic_key]
        
        # Generate concept_id
        concept_id = generate_concept_id(topic_id, concept_name)
        
        output_row = {
            "concept_id": concept_id,
            "concept_name": concept_name,
            "concept_description": row.get("concept_description", ""),
            "concept_page_number": row.get("concept_page_number", ""),
            "topic_id": topic_id,
            "topic_name": topic_name,
            "topic_description": row.get("topic_description", ""),
            "topic_position": row.get("topic_position", ""),
            "chapter_id": chapter_id,
            "chapter_name": chapter_name,
            "chapter_description": row.get("chapter_description", ""),
            "chapter_position": row.get("chapter_position", ""),
            "subject_id": subject_id,
        }
        output_rows.append(output_row)
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    
    stats = {
        "concepts": len(output_rows),
        "topics": len(topic_ids),
        "chapters": len(chapter_ids)
    }
    logger.info(f"Added UUIDs to CSV: {len(output_rows)} concepts, saved to {output_csv_path}")
    return stats


def add_uuids_to_exercise_json(
    input_json_path: str,
    output_json_path: str,
    subject_id: str
) -> Dict[str, int]:
    """
    Add UUIDs to an existing exercise questions JSON file.
    
    Reads a JSON with structure: {chapter_name, exercise_questions: [...]}
    Outputs a JSON with added: chapter_id, subject_id at top level, id for each question.
    
    Args:
        input_json_path: Path to the input JSON without UUIDs.
        output_json_path: Path to save the output JSON with UUIDs.
        subject_id: Subject UUID for generating deterministic UUIDs.
    
    Returns:
        Statistics dict with counts of processed items.
    
    Raises:
        FileNotFoundError: If input JSON doesn't exist.
        ValueError: If required fields are missing.
    """
    input_path = Path(input_json_path)
    output_path = Path(output_json_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input JSON not found: {input_json_path}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if "chapter_name" not in data:
        raise ValueError(f"Missing 'chapter_name' field in JSON: {input_json_path}")
    
    if "exercise_questions" not in data:
        raise ValueError(f"Missing 'exercise_questions' field in JSON: {input_json_path}")
    
    # Check if UUIDs already exist
    if "chapter_id" in data:
        logger.warning(f"JSON already has UUIDs: {input_json_path}")
    
    chapter_name = data["chapter_name"]
    questions = data["exercise_questions"]
    
    # Generate chapter_id
    chapter_id = generate_chapter_id(subject_id, chapter_name)
    
    # Add UUIDs to each question
    for question in questions:
        question_id = generate_question_id(subject_id, question)
        question["id"] = question_id
    
    # Build output data
    output_data = {
        "chapter_name": chapter_name,
        "chapter_id": chapter_id,
        "subject_id": subject_id,
        "exercise_questions": questions
    }
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    stats = {"questions": len(questions)}
    logger.info(f"Added UUIDs to exercise JSON: {len(questions)} questions, saved to {output_json_path}")
    return stats


def add_uuids_to_solved_json(
    input_json_path: str,
    output_json_path: str,
    subject_id: str
) -> Dict[str, int]:
    """
    Add UUIDs to an existing solved examples JSON file.
    
    Reads a JSON with structure: {chapter_name, solved_examples_questions: [...]}
    Outputs a JSON with added: chapter_id, subject_id at top level, id for each question.
    
    Args:
        input_json_path: Path to the input JSON without UUIDs.
        output_json_path: Path to save the output JSON with UUIDs.
        subject_id: Subject UUID for generating deterministic UUIDs.
    
    Returns:
        Statistics dict with counts of processed items.
    
    Raises:
        FileNotFoundError: If input JSON doesn't exist.
        ValueError: If required fields are missing.
    """
    input_path = Path(input_json_path)
    output_path = Path(output_json_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input JSON not found: {input_json_path}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if "chapter_name" not in data:
        raise ValueError(f"Missing 'chapter_name' field in JSON: {input_json_path}")
    
    if "solved_examples_questions" not in data:
        raise ValueError(f"Missing 'solved_examples_questions' field in JSON: {input_json_path}")
    
    # Check if UUIDs already exist
    if "chapter_id" in data:
        logger.warning(f"JSON already has UUIDs: {input_json_path}")
    
    chapter_name = data["chapter_name"]
    questions = data["solved_examples_questions"]
    
    # Generate chapter_id
    chapter_id = generate_chapter_id(subject_id, chapter_name)
    
    # Add UUIDs to each question
    for question in questions:
        question_id = generate_question_id(subject_id, question)
        question["id"] = question_id
    
    # Build output data
    output_data = {
        "chapter_name": chapter_name,
        "chapter_id": chapter_id,
        "subject_id": subject_id,
        "solved_examples_questions": questions
    }
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    stats = {"questions": len(questions)}
    logger.info(f"Added UUIDs to solved JSON: {len(questions)} questions, saved to {output_json_path}")
    return stats


def add_uuids_to_directory(
    input_dir: str,
    output_dir: str,
    subject_id: str
) -> Dict[str, Any]:
    """
    Add UUIDs to all CSV and JSON files in a directory.
    
    Processes:
    - *_concepts.csv files
    - *_exercise_questions.json files
    - *_solved_examples.json files
    
    Args:
        input_dir: Directory containing files without UUIDs.
        output_dir: Directory to save files with UUIDs.
        subject_id: Subject UUID for generating deterministic UUIDs.
    
    Returns:
        Summary statistics of all processed files.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "concepts_csvs": 0,
        "exercise_jsons": 0,
        "solved_jsons": 0,
        "total_concepts": 0,
        "total_questions": 0,
        "errors": []
    }
    
    # Process concept CSVs
    for csv_file in sorted(input_path.glob("*_concepts.csv")):
        output_csv = output_path / csv_file.name
        try:
            result = add_uuids_to_concepts_csv(str(csv_file), str(output_csv), subject_id)
            stats["concepts_csvs"] += 1
            stats["total_concepts"] += result["concepts"]
        except Exception as e:
            stats["errors"].append(f"{csv_file.name}: {e}")
            logger.error(f"Failed to process {csv_file.name}: {e}")
    
    # Process exercise question JSONs
    for json_file in sorted(input_path.glob("*_exercise_questions.json")):
        output_json = output_path / json_file.name
        try:
            result = add_uuids_to_exercise_json(str(json_file), str(output_json), subject_id)
            stats["exercise_jsons"] += 1
            stats["total_questions"] += result["questions"]
        except Exception as e:
            stats["errors"].append(f"{json_file.name}: {e}")
            logger.error(f"Failed to process {json_file.name}: {e}")
    
    # Process solved examples JSONs
    for json_file in sorted(input_path.glob("*_solved_examples.json")):
        output_json = output_path / json_file.name
        try:
            result = add_uuids_to_solved_json(str(json_file), str(output_json), subject_id)
            stats["solved_jsons"] += 1
            stats["total_questions"] += result["questions"]
        except Exception as e:
            stats["errors"].append(f"{json_file.name}: {e}")
            logger.error(f"Failed to process {json_file.name}: {e}")
    
    logger.info(
        f"Migration complete: {stats['concepts_csvs']} CSVs, "
        f"{stats['exercise_jsons']} exercise JSONs, {stats['solved_jsons']} solved JSONs"
    )
    return stats
