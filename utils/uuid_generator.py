"""
UUID generation utilities for deterministic ID creation.

Uses UUID5 (name-based, SHA-1) for deterministic IDs based on content.
This ensures the same input always produces the same UUID, enabling idempotent uploads.

UUID Hierarchy:
    board_id (provided) → school_class_id → subject_id → chapter_id → topic_id → concept_id
    subject_id → question_id (based on question JSON content)
"""

import uuid
import json
from typing import Any


def generate_school_class_id(board_id: str, school_class_name: str) -> str:
    """
    Generate a deterministic school_class UUID based on board and school_class name.
    
    Args:
        board_id: The parent board UUID.
        school_class_name: Name of the school_class (e.g., "Class 6", "Class 10").
    
    Returns:
        Deterministic UUID5 string for the school_class.
    """
    namespace = uuid.UUID(board_id)
    return str(uuid.uuid5(namespace, school_class_name))


def generate_subject_id(school_class_id: str, subject_name: str) -> str:
    """
    Generate a deterministic subject UUID based on school_class and subject name.
    
    Args:
        school_class_id: The parent school_class UUID.
        subject_name: Name of the subject (e.g., "Mathematics", "Science").
    
    Returns:
        Deterministic UUID5 string for the subject.
    """
    namespace = uuid.UUID(school_class_id)
    return str(uuid.uuid5(namespace, subject_name))


def generate_chapter_id(subject_id: str, chapter_name: str) -> str:
    """
    Generate a deterministic chapter UUID based on subject and chapter name.
    
    Args:
        subject_id: The parent subject UUID.
        chapter_name: Name of the chapter.
    
    Returns:
        Deterministic UUID5 string for the chapter.
    """
    namespace = uuid.UUID(subject_id)
    return str(uuid.uuid5(namespace, chapter_name))


def generate_topic_id(chapter_id: str, topic_name: str) -> str:
    """
    Generate a deterministic topic UUID based on chapter and topic name.
    
    Args:
        chapter_id: The parent chapter UUID.
        topic_name: Name of the topic.
    
    Returns:
        Deterministic UUID5 string for the topic.
    """
    namespace = uuid.UUID(chapter_id)
    return str(uuid.uuid5(namespace, topic_name))


def generate_concept_id(topic_id: str, concept_name: str) -> str:
    """
    Generate a deterministic concept UUID based on topic and concept name.
    
    Args:
        topic_id: The parent topic UUID.
        concept_name: Name of the concept.
    
    Returns:
        Deterministic UUID5 string for the concept.
    """
    namespace = uuid.UUID(topic_id)
    return str(uuid.uuid5(namespace, concept_name))


def generate_question_id(subject_id: str, question_data: dict) -> str:
    """
    Generate a deterministic question UUID based on subject and question content.
    
    Uses a JSON serialization of key question fields to create a fingerprint.
    
    Args:
        subject_id: The subject UUID.
        question_data: Dictionary containing question fields.
    
    Returns:
        Deterministic UUID5 string for the question.
    """
    namespace = uuid.UUID(subject_id)
    
    # Create fingerprint from question text and explanation
    fingerprint_parts = [subject_id]
    
    if question_data.get("question_text"):
        fingerprint_parts.append(str(question_data["question_text"]))
    
    if question_data.get("explanation"):
        fingerprint_parts.append(str(question_data["explanation"]))
    
    fingerprint = "_".join(fingerprint_parts)
    return str(uuid.uuid5(namespace, fingerprint))


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate that a string is a valid UUID.
    
    Args:
        uuid_string: String to validate.
    
    Returns:
        True if valid UUID, False otherwise.
    """
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, AttributeError, TypeError):
        return False
