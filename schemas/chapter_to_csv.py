"""
CSV serialization for Chapter objects with UUID generation.

Handles saving and loading Chapter objects to/from CSV format,
generating deterministic UUIDs during serialization.
"""

import os
import logging
import csv
from typing import Tuple, List, Dict, Any

from schemas.concept_schema import Chapter, Topic, Concept
from utils.uuid_generator import generate_chapter_id, generate_topic_id, generate_concept_id

logger = logging.getLogger(__name__)


def create_csv_with_uuids(chapter: Chapter, position: int, subject_id: str) -> Tuple[List[str], List[List[Any]]]:
    """
    Convert a Chapter object to CSV headers and rows with UUIDs.
    
    Flattens the chapter → topic → concept hierarchy into rows,
    with one row per concept containing all parent information and UUIDs.
    
    Args:
        chapter: The Chapter object to convert.
        position: Position of the chapter in the book (1-indexed).
        subject_id: Subject UUID for generating chapter/topic/concept UUIDs.
    
    Returns:
        Tuple of (headers, rows) where headers is a list of column names
        and rows is a list of row data lists.
    """
    headers = [
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

    # Generate chapter UUID
    chapter_id = generate_chapter_id(subject_id, chapter.name)
    
    rows = []
    for topic in chapter.topics:
        # Generate topic UUID
        topic_id = generate_topic_id(chapter_id, topic.name)
        
        for concept in topic.concepts:
            # Generate concept UUID
            concept_id = generate_concept_id(topic_id, concept.name)
            
            rows.append([
                concept_id,
                concept.name,
                concept.description,
                concept.page_number,
                topic_id,
                topic.name,
                topic.description,
                topic.position,
                chapter_id,
                chapter.name,
                chapter.description,
                position,
                subject_id,
            ])
    
    logger.info(f"CSV data created with {len(rows)} rows, for chapter {chapter.name}")
    return headers, rows


def save_csv(chapter: Chapter, path: str, position: int, subject_id: str):
    """
    Save a Chapter object to a CSV file with generated UUIDs.
    
    Creates parent directories if they don't exist.
    Generates deterministic UUIDs for chapter, topics, and concepts.
    
    Args:
        chapter: The Chapter object to save.
        path: File path where the CSV will be saved.
        position: Position of the chapter in the book (1-indexed).
        subject_id: Subject UUID for generating deterministic UUIDs.
    """
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)
        logger.info(f"Created directory: {folder}")

    headers, rows = create_csv_with_uuids(chapter, position, subject_id)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    logger.info(f"CSV saved successfully at: {path}")


def load_csv_with_uuids(csv_path: str) -> Dict[str, Any]:
    """
    Load concepts data from a CSV file including UUIDs.
    
    Parses the CSV format into a structured dictionary with all UUID information.
    
    Args:
        csv_path: Path to the CSV file to load.
    
    Returns:
        Dictionary with structure:
        {
            "subject_id": str,
            "chapter": {"id": str, "name": str, "description": str, "position": int},
            "topics": {topic_id: {"id": str, "name": str, "description": str, "position": int, "chapter_id": str}},
            "concepts": [{"id": str, "name": str, "description": str, "page_number": int, "topic_id": str}]
        }
    
    Raises:
        FileNotFoundError: If the CSV file does not exist.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        raise ValueError(f"Empty CSV file: {csv_path}")
    
    first_row = rows[0]
    
    result = {
        "subject_id": first_row["subject_id"],
        "chapter": {
            "id": first_row["chapter_id"],
            "name": first_row["chapter_name"],
            "description": first_row["chapter_description"],
            "position": int(first_row["chapter_position"]),
        },
        "topics": {},
        "concepts": [],
    }
    
    for row in rows:
        topic_id = row["topic_id"]
        
        # Add topic if not seen
        if topic_id not in result["topics"]:
            result["topics"][topic_id] = {
                "id": topic_id,
                "name": row["topic_name"],
                "description": row["topic_description"],
                "position": int(row["topic_position"]),
                "chapter_id": row["chapter_id"],
            }
        
        # Add concept
        result["concepts"].append({
            "id": row["concept_id"],
            "name": row["concept_name"],
            "description": row["concept_description"],
            "page_number": int(row["concept_page_number"]),
            "topic_id": topic_id,
        })
    
    logger.info(f"Loaded CSV with {len(result['concepts'])} concepts from {csv_path}")
    return result


def csv_to_chapter(csv_path: str) -> Chapter:
    """
    Load a Chapter object from a CSV file (without UUIDs).
    
    Parses the flattened CSV format back into the hierarchical
    Chapter → Topic → Concept structure.
    
    Args:
        csv_path: Path to the CSV file to load.
    
    Returns:
        A Chapter object reconstructed from the CSV data.
    
    Raises:
        FileNotFoundError: If the CSV file does not exist.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        topics_dict = {}
        chapter_info = None
        
        for row in reader:
            chapter_info = row
            topic_name = row["topic_name"]
            
            if topic_name not in topics_dict:
                topics_dict[topic_name] = {
                    "name": topic_name,
                    "description": row["topic_description"],
                    "concepts": [],
                    "position": int(row["topic_position"]),
                }
            
            concept = {
                "name": row["concept_name"],
                "description": row["concept_description"],
                "page_number": int(row["concept_page_number"]),
            }
            topics_dict[topic_name]["concepts"].append(concept)

        if not chapter_info:
            raise ValueError(f"Empty CSV file: {csv_path}")

        topics = []
        for topic_data in topics_dict.values():
            topic = Topic(
                name=topic_data["name"],
                description=topic_data["description"],
                concepts=[
                    Concept(
                        name=concept["name"],
                        description=concept["description"],
                        page_number=concept["page_number"],
                    )
                    for concept in topic_data["concepts"]
                ],
                position=topic_data["position"],
            )
            topics.append(topic)

        chapter = Chapter(
            name=chapter_info["chapter_name"],
            description=chapter_info["chapter_description"],
            topics=topics,
        )
        return chapter


def get_concept_names_from_csv(csv_path: str) -> List[str]:
    """
    Load just the concept names from a CSV file.
    
    Args:
        csv_path: Path to the CSV file.
    
    Returns:
        List of concept names.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row["concept_name"] for row in reader]