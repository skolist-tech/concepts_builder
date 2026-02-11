"""Unit tests for question sanitization functions."""

import pytest

from schemas.bank_questions.exercise_bank_to_json import _sanitize_question


class TestSanitizeQuestion:
    """Tests for _sanitize_question function."""

    def test_null_answer_text_becomes_empty_string(self):
        """Should replace None answer_text with empty string."""
        question = {"answer_text": None}
        result = _sanitize_question(question)
        assert result["answer_text"] == ""

    def test_null_explanation_becomes_empty_string(self):
        """Should replace None explanation with empty string."""
        question = {"explanation": None}
        result = _sanitize_question(question)
        assert result["explanation"] == ""

    def test_null_question_text_becomes_empty_string(self):
        """Should replace None question_text with empty string."""
        question = {"question_text": None}
        result = _sanitize_question(question)
        assert result["question_text"] == ""

    def test_null_question_type_becomes_short_answer(self):
        """Should replace None question_type with 'Short Answer'."""
        question = {"question_type": None}
        result = _sanitize_question(question)
        assert result["question_type"] == "Short Answer"

    def test_null_is_image_needed_becomes_zero(self):
        """Should replace None is_image_needed with 0."""
        question = {"is_image_needed": None}
        result = _sanitize_question(question)
        assert result["is_image_needed"] == 0

    def test_preserves_existing_values(self):
        """Should not modify existing non-None values."""
        question = {
            "answer_text": "Answer",
            "explanation": "Explanation",
            "question_text": "Question?",
            "question_type": "MCQ",
            "is_image_needed": 1
        }
        result = _sanitize_question(question)
        assert result["answer_text"] == "Answer"
        assert result["explanation"] == "Explanation"
        assert result["question_text"] == "Question?"
        assert result["question_type"] == "MCQ"
        assert result["is_image_needed"] == 1

    def test_handles_empty_dict(self):
        """Should handle empty dict - no keys present."""
        question = {}
        result = _sanitize_question(question)
        # Keys not present should remain not present
        # (function only replaces None values, doesn't add missing keys)
        assert "answer_text" not in result or result["answer_text"] is not None

    def test_preserves_other_fields(self):
        """Should preserve fields not in sanitization list."""
        question = {
            "id": "test-uuid",
            "option1": "A",
            "option2": "B",
            "correct_mcq_option": 1,
            "explanation": None  # This will be sanitized
        }
        result = _sanitize_question(question)
        assert result["id"] == "test-uuid"
        assert result["option1"] == "A"
        assert result["option2"] == "B"
        assert result["correct_mcq_option"] == 1
        assert result["explanation"] == ""

    def test_mutates_original_dict(self):
        """Verify the function mutates and returns the same dict."""
        question = {"explanation": None}
        result = _sanitize_question(question)
        assert result is question
        assert question["explanation"] == ""

    def test_complete_question_untouched(self):
        """A complete question should pass through unchanged."""
        question = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "question_text": "What is 2+2?",
            "answer_text": "4",
            "explanation": "Addition of two and two",
            "question_type": "short_answer",
            "is_image_needed": 0,
            "option1": None,  # Options can be None, function doesn't touch them
            "option2": None
        }
        result = _sanitize_question(question.copy())
        # Core required fields are intact
        assert result["question_text"] == "What is 2+2?"
        assert result["answer_text"] == "4"
        assert result["explanation"] == "Addition of two and two"
        assert result["question_type"] == "short_answer"
