"""Unit tests for question utility functions in uploaders."""

import pytest

from exercise_questions_uploader import (
    normalize_question_type,
    is_empty_string,
    question_to_db_record,
)


class TestNormalizeQuestionType:
    """Tests for normalize_question_type function."""

    def test_none_input(self):
        """Should return None for None input."""
        assert normalize_question_type(None) is None

    def test_empty_string(self):
        """Should return None for empty string."""
        assert normalize_question_type("") is None

    def test_mcq_variations(self):
        """Should normalize MCQ variations."""
        assert normalize_question_type("mcq") == "mcq4"
        assert normalize_question_type("MCQ") == "mcq4"
        assert normalize_question_type("mcq4") == "mcq4"
        assert normalize_question_type("multiple choice") == "mcq4"

    def test_msq_variations(self):
        """Should normalize MSQ variations."""
        assert normalize_question_type("msq") == "msq4"
        assert normalize_question_type("MSQ") == "msq4"
        assert normalize_question_type("multiple select") == "msq4"

    def test_short_answer_variations(self):
        """Should normalize short answer variations."""
        assert normalize_question_type("short answer") == "short_answer"
        assert normalize_question_type("shortanswer") == "short_answer"
        assert normalize_question_type("Short Answer") == "short_answer"

    def test_long_answer_variations(self):
        """Should normalize long answer variations."""
        assert normalize_question_type("long answer") == "long_answer"
        assert normalize_question_type("longanswer") == "long_answer"

    def test_true_false_variations(self):
        """Should normalize true/false variations."""
        assert normalize_question_type("true false") == "true_or_false"
        assert normalize_question_type("true/false") == "true_or_false"
        assert normalize_question_type("true or false") == "true_or_false"

    def test_fill_in_the_blanks_variations(self):
        """Should normalize fill in the blanks variations."""
        assert normalize_question_type("fill in the blanks") == "fill_in_the_blanks"
        assert normalize_question_type("fillintheblank") == "fill_in_the_blanks"

    def test_match_the_following_variations(self):
        """Should normalize match the following variations."""
        assert normalize_question_type("match") == "match_the_following"
        assert normalize_question_type("match the following") == "match_the_following"

    def test_unknown_type_passthrough(self):
        """Unknown types should pass through with space-to-underscore replacement."""
        assert normalize_question_type("custom type") == "custom_type"
        assert normalize_question_type("NEW STYLE") == "new_style"

    def test_whitespace_handling(self):
        """Should handle leading/trailing whitespace."""
        assert normalize_question_type("  mcq  ") == "mcq4"
        assert normalize_question_type("\tshort answer\n") == "short_answer"


class TestIsEmptyString:
    """Tests for is_empty_string function."""

    def test_none_is_empty(self):
        """None should be considered empty."""
        assert is_empty_string(None) is True

    def test_empty_string_is_empty(self):
        """Empty string should be considered empty."""
        assert is_empty_string("") is True

    def test_whitespace_only_is_empty(self):
        """Whitespace-only strings should be considered empty."""
        assert is_empty_string("   ") is True
        assert is_empty_string("\t\n") is True

    def test_non_empty_string(self):
        """Regular strings should not be considered empty."""
        assert is_empty_string("hello") is False
        assert is_empty_string("  hello  ") is False

    def test_numeric_string(self):
        """Numeric strings should not be empty."""
        assert is_empty_string("123") is False

    def test_special_characters(self):
        """Special characters should not be empty."""
        assert is_empty_string("!@#") is False


class TestQuestionToDbRecord:
    """Tests for question_to_db_record function."""

    SUBJECT_ID = "550e8400-e29b-41d4-a716-446655440000"
    CHAPTER_ID = "660e8400-e29b-41d4-a716-446655440000"

    def test_valid_question_record(self):
        """Should create valid database record from question dict."""
        question = {
            "id": "770e8400-e29b-41d4-a716-446655440000",
            "question_text": "What is 2+2?",
            "explanation": "Simple addition",
            "question_type": "mcq",
            "option1": "2",
            "option2": "3",
            "option3": "4",
            "option4": "5",
            "correct_mcq_option": 3,
        }
        record = question_to_db_record(question, self.SUBJECT_ID, self.CHAPTER_ID)
        
        assert record["id"] == question["id"]
        assert record["subject_id"] == self.SUBJECT_ID
        assert record["chapter_id"] == self.CHAPTER_ID
        assert record["question_text"] == "What is 2+2?"
        assert record["question_type"] == "mcq4"
        assert record["option1"] == "2"
        assert record["correct_mcq_option"] == 3

    def test_missing_id_raises_error(self):
        """Should raise ValueError when question has no ID."""
        question = {"question_text": "What is 2+2?"}
        with pytest.raises(ValueError, match="missing 'id' field"):
            question_to_db_record(question, self.SUBJECT_ID)

    def test_is_incomplete_empty_question_text(self):
        """Should mark as incomplete when question_text is empty."""
        question = {
            "id": "770e8400-e29b-41d4-a716-446655440000",
            "question_text": "",
            "explanation": "Valid explanation"
        }
        record = question_to_db_record(question, self.SUBJECT_ID)
        assert record["is_incomplete"] == 1

    def test_is_incomplete_empty_explanation(self):
        """Should mark as incomplete when explanation is empty."""
        question = {
            "id": "770e8400-e29b-41d4-a716-446655440000",
            "question_text": "Valid question",
            "explanation": ""
        }
        record = question_to_db_record(question, self.SUBJECT_ID)
        assert record["is_incomplete"] == 1

    def test_is_incomplete_image_needed(self):
        """Should mark as incomplete when image is needed."""
        question = {
            "id": "770e8400-e29b-41d4-a716-446655440000",
            "question_text": "Valid question",
            "explanation": "Valid explanation",
            "is_image_needed": True
        }
        record = question_to_db_record(question, self.SUBJECT_ID)
        assert record["is_incomplete"] == 1
        assert record["is_image_needed"] == 1

    def test_complete_question(self):
        """Should mark as complete when all fields are valid."""
        question = {
            "id": "770e8400-e29b-41d4-a716-446655440000",
            "question_text": "Valid question",
            "explanation": "Valid explanation",
            "is_image_needed": False
        }
        record = question_to_db_record(question, self.SUBJECT_ID)
        assert record["is_incomplete"] == 0
        assert record["is_image_needed"] == 0

    def test_is_from_exercise_flag(self):
        """Exercise questions should have is_from_exercise=1."""
        question = {
            "id": "770e8400-e29b-41d4-a716-446655440000",
            "question_text": "Test",
            "explanation": "Test"
        }
        record = question_to_db_record(question, self.SUBJECT_ID)
        assert record["is_from_exercise"] == 1
        assert record["is_solved_example"] == 0

    def test_match_columns_serialization(self):
        """Should serialize match_columns to string."""
        question = {
            "id": "770e8400-e29b-41d4-a716-446655440000",
            "question_text": "Match the following",
            "explanation": "Test",
            "match_columns": [["A", "1"], ["B", "2"]]
        }
        record = question_to_db_record(question, self.SUBJECT_ID)
        assert record["match_columns"] == "[['A', '1'], ['B', '2']]"

    def test_svgs_serialization(self):
        """Should serialize svgs to string."""
        question = {
            "id": "770e8400-e29b-41d4-a716-446655440000",
            "question_text": "Test",
            "explanation": "Test",
            "svgs": ["<svg>...</svg>"]
        }
        record = question_to_db_record(question, self.SUBJECT_ID)
        assert "svg" in record["svgs"]

    def test_no_chapter_id(self):
        """Should handle missing chapter_id."""
        question = {
            "id": "770e8400-e29b-41d4-a716-446655440000",
            "question_text": "Test",
            "explanation": "Test"
        }
        record = question_to_db_record(question, self.SUBJECT_ID)
        assert record["chapter_id"] is None
