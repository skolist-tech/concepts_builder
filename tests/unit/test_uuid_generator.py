"""Unit tests for uuid_generator module."""

import uuid
import pytest

from utils.uuid_generator import (
    generate_school_class_id,
    generate_subject_id,
    generate_chapter_id,
    generate_topic_id,
    generate_concept_id,
    generate_question_id,
    validate_uuid,
)


# Use fixed valid UUIDs for testing
TEST_BOARD_ID = "440e8400-e29b-41d4-a716-446655440000"
TEST_CLASS_ID = "550e8400-e29b-41d4-a716-446655440000"
TEST_SUBJECT_ID = "550e8400-e29b-41d4-a716-446655440000"


class TestGenerateSchoolClassId:
    """Tests for generate_school_class_id function."""

    def test_returns_valid_uuid(self):
        """Should return a valid UUID string."""
        result = generate_school_class_id(TEST_BOARD_ID, "Class 6")
        assert validate_uuid(result)

    def test_deterministic_same_input_same_output(self):
        """Same inputs should always produce the same UUID."""
        result1 = generate_school_class_id(TEST_BOARD_ID, "Class 6")
        result2 = generate_school_class_id(TEST_BOARD_ID, "Class 6")
        assert result1 == result2

    def test_different_school_class_different_uuid(self):
        """Different school_class names should produce different UUIDs."""
        result1 = generate_school_class_id(TEST_BOARD_ID, "Class 6")
        result2 = generate_school_class_id(TEST_BOARD_ID, "Class 7")
        assert result1 != result2

    def test_different_board_different_uuid(self):
        """Different board IDs should produce different UUIDs."""
        other_board = "660e8400-e29b-41d4-a716-446655440000"
        result1 = generate_school_class_id(TEST_BOARD_ID, "Class 6")
        result2 = generate_school_class_id(other_board, "Class 6")
        assert result1 != result2


class TestGenerateSubjectId:
    """Tests for generate_subject_id function."""

    def test_returns_valid_uuid(self):
        """Should return a valid UUID string."""
        result = generate_subject_id(TEST_CLASS_ID, "Mathematics")
        assert validate_uuid(result)

    def test_deterministic_same_input_same_output(self):
        """Same inputs should always produce the same UUID."""
        result1 = generate_subject_id(TEST_CLASS_ID, "Mathematics")
        result2 = generate_subject_id(TEST_CLASS_ID, "Mathematics")
        assert result1 == result2

    def test_different_subject_different_uuid(self):
        """Different subject names should produce different UUIDs."""
        result1 = generate_subject_id(TEST_CLASS_ID, "Mathematics")
        result2 = generate_subject_id(TEST_CLASS_ID, "Science")
        assert result1 != result2

    def test_different_school_class_different_uuid(self):
        """Different school_class IDs should produce different UUIDs."""
        other_school_class = "660e8400-e29b-41d4-a716-446655440000"
        result1 = generate_subject_id(TEST_CLASS_ID, "Mathematics")
        result2 = generate_subject_id(other_school_class, "Mathematics")
        assert result1 != result2


class TestGenerateChapterId:
    """Tests for generate_chapter_id function."""

    def test_returns_valid_uuid(self):
        """Should return a valid UUID string."""
        result = generate_chapter_id(TEST_SUBJECT_ID, "Chapter 1")
        assert validate_uuid(result)

    def test_deterministic_same_input_same_output(self):
        """Same inputs should always produce the same UUID."""
        result1 = generate_chapter_id(TEST_SUBJECT_ID, "Numbers")
        result2 = generate_chapter_id(TEST_SUBJECT_ID, "Numbers")
        assert result1 == result2

    def test_different_chapter_different_uuid(self):
        """Different chapter names should produce different UUIDs."""
        result1 = generate_chapter_id(TEST_SUBJECT_ID, "Chapter 1")
        result2 = generate_chapter_id(TEST_SUBJECT_ID, "Chapter 2")
        assert result1 != result2

    def test_different_subject_different_uuid(self):
        """Different subject IDs should produce different UUIDs."""
        other_subject = "660e8400-e29b-41d4-a716-446655440000"
        result1 = generate_chapter_id(TEST_SUBJECT_ID, "Chapter 1")
        result2 = generate_chapter_id(other_subject, "Chapter 1")
        assert result1 != result2

    def test_empty_chapter_name(self):
        """Empty chapter name should still produce a valid UUID."""
        result = generate_chapter_id(TEST_SUBJECT_ID, "")
        assert validate_uuid(result)


class TestGenerateTopicId:
    """Tests for generate_topic_id function."""

    def test_returns_valid_uuid(self):
        """Should return a valid UUID string."""
        chapter_id = generate_chapter_id(TEST_SUBJECT_ID, "Chapter 1")
        result = generate_topic_id(chapter_id, "Topic 1")
        assert validate_uuid(result)

    def test_deterministic_same_input_same_output(self):
        """Same inputs should always produce the same UUID."""
        chapter_id = generate_chapter_id(TEST_SUBJECT_ID, "Chapter 1")
        result1 = generate_topic_id(chapter_id, "Natural Numbers")
        result2 = generate_topic_id(chapter_id, "Natural Numbers")
        assert result1 == result2

    def test_different_topic_different_uuid(self):
        """Different topic names should produce different UUIDs."""
        chapter_id = generate_chapter_id(TEST_SUBJECT_ID, "Chapter 1")
        result1 = generate_topic_id(chapter_id, "Topic A")
        result2 = generate_topic_id(chapter_id, "Topic B")
        assert result1 != result2


class TestGenerateConceptId:
    """Tests for generate_concept_id function."""

    def test_returns_valid_uuid(self):
        """Should return a valid UUID string."""
        chapter_id = generate_chapter_id(TEST_SUBJECT_ID, "Chapter 1")
        topic_id = generate_topic_id(chapter_id, "Topic 1")
        result = generate_concept_id(topic_id, "Concept 1")
        assert validate_uuid(result)

    def test_deterministic_same_input_same_output(self):
        """Same inputs should always produce the same UUID."""
        chapter_id = generate_chapter_id(TEST_SUBJECT_ID, "Chapter 1")
        topic_id = generate_topic_id(chapter_id, "Topic 1")
        result1 = generate_concept_id(topic_id, "Counting")
        result2 = generate_concept_id(topic_id, "Counting")
        assert result1 == result2

    def test_uuid_hierarchy_chain(self):
        """UUID chain should be reproducible across calls."""
        # First chain
        chap1 = generate_chapter_id(TEST_SUBJECT_ID, "Algebra")
        topic1 = generate_topic_id(chap1, "Equations")
        concept1 = generate_concept_id(topic1, "Linear Equations")

        # Second chain with same inputs
        chap2 = generate_chapter_id(TEST_SUBJECT_ID, "Algebra")
        topic2 = generate_topic_id(chap2, "Equations")
        concept2 = generate_concept_id(topic2, "Linear Equations")

        assert chap1 == chap2
        assert topic1 == topic2
        assert concept1 == concept2


class TestGenerateQuestionId:
    """Tests for generate_question_id function."""

    def test_returns_valid_uuid(self):
        """Should return a valid UUID string."""
        question_data = {
            "question_text": "What is 2+2?",
            "explanation": "Simple addition"
        }
        result = generate_question_id(TEST_SUBJECT_ID, question_data)
        assert validate_uuid(result)

    def test_deterministic_same_input_same_output(self):
        """Same inputs should always produce the same UUID."""
        question_data = {
            "question_text": "What is 2+2?",
            "explanation": "Simple addition"
        }
        result1 = generate_question_id(TEST_SUBJECT_ID, question_data)
        result2 = generate_question_id(TEST_SUBJECT_ID, question_data)
        assert result1 == result2

    def test_different_question_text_different_uuid(self):
        """Different question text should produce different UUIDs."""
        q1 = {"question_text": "What is 2+2?", "explanation": "Addition"}
        q2 = {"question_text": "What is 3+3?", "explanation": "Addition"}
        result1 = generate_question_id(TEST_SUBJECT_ID, q1)
        result2 = generate_question_id(TEST_SUBJECT_ID, q2)
        assert result1 != result2

    def test_different_explanation_different_uuid(self):
        """Different explanation should produce different UUIDs."""
        q1 = {"question_text": "What is 2+2?", "explanation": "Simple"}
        q2 = {"question_text": "What is 2+2?", "explanation": "Complex"}
        result1 = generate_question_id(TEST_SUBJECT_ID, q1)
        result2 = generate_question_id(TEST_SUBJECT_ID, q2)
        assert result1 != result2

    def test_empty_question_data(self):
        """Empty question data should still produce a valid UUID."""
        result = generate_question_id(TEST_SUBJECT_ID, {})
        assert validate_uuid(result)

    def test_missing_explanation(self):
        """Missing explanation should still work."""
        question_data = {"question_text": "What is 2+2?"}
        result = generate_question_id(TEST_SUBJECT_ID, question_data)
        assert validate_uuid(result)


class TestValidateUuid:
    """Tests for validate_uuid function."""

    def test_valid_uuid_v4(self):
        """Should return True for valid UUID v4."""
        valid_uuid = str(uuid.uuid4())
        assert validate_uuid(valid_uuid) is True

    def test_valid_uuid_v5(self):
        """Should return True for valid UUID v5."""
        valid_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, "test"))
        assert validate_uuid(valid_uuid) is True

    def test_valid_uuid_string(self):
        """Should return True for a known valid UUID string."""
        assert validate_uuid("550e8400-e29b-41d4-a716-446655440000") is True

    def test_invalid_uuid_string(self):
        """Should return False for invalid UUID string."""
        assert validate_uuid("not-a-uuid") is False

    def test_empty_string(self):
        """Should return False for empty string."""
        assert validate_uuid("") is False

    def test_none_value(self):
        """Should return False for None."""
        assert validate_uuid(None) is False

    def test_partial_uuid(self):
        """Should return False for partial UUID."""
        assert validate_uuid("550e8400-e29b") is False

    def test_uuid_without_dashes(self):
        """UUID without dashes should still be valid."""
        assert validate_uuid("550e8400e29b41d4a716446655440000") is True
