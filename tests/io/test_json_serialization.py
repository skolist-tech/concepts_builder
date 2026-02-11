"""I/O tests for JSON serialization with tmp_path fixture."""

import pytest
import json
from pathlib import Path

from schemas.bank_questions.exercise_bank_to_json import (
    save_exercise_bank_json,
    load_exercise_bank_json
)
from schemas.bank_questions.solved_bank_to_json import (
    save_solved_bank_json,
    load_solved_bank_json
)
from schemas.bank_questions.question_bank_schema import (
    ExerciseQuestionsBank,
    ExerciseQuestion,
    SolvedExamplesBank,
    SolvedExample
)
from utils.uuid_generator import validate_uuid


TEST_SUBJECT_ID = "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_exercise_bank() -> ExerciseQuestionsBank:
    """Create a sample ExerciseQuestionsBank for testing."""
    return ExerciseQuestionsBank(
        chapter_name="Chapter 1: Numbers",
        exercise_questions=[
            ExerciseQuestion(
                question_text="What is 2+2?",
                explanation="Simple addition: 2+2=4",
                answer_text="4",
                question_type="Short Answer",
                concepts=["Addition"]
            ),
            ExerciseQuestion(
                question_text="Which is the largest number?",
                explanation="Comparison of numbers",
                question_type="MCQ4",
                option1="5",
                option2="10",
                option3="3",
                option4="7",
                correct_mcq_option=2,
                concepts=["Number Comparison"]
            ),
        ]
    )


@pytest.fixture
def sample_solved_bank() -> SolvedExamplesBank:
    """Create a sample SolvedExamplesBank for testing."""
    return SolvedExamplesBank(
        chapter_name="Chapter 1: Numbers",
        solved_examples_questions=[
            SolvedExample(
                question_text="Example 1: Find 5+3",
                explanation="Step by step: 5+3=8",
                answer_text="8",
                question_type="Short Answer",
                concepts=["Addition"]
            ),
        ]
    )


class TestSaveExerciseBankJson:
    """Tests for save_exercise_bank_json function."""

    def test_creates_json_file(self, tmp_path: Path, sample_exercise_bank: ExerciseQuestionsBank):
        """Should create a JSON file at the specified path."""
        json_path = tmp_path / "exercise.json"
        
        save_exercise_bank_json(sample_exercise_bank, str(json_path), TEST_SUBJECT_ID)
        
        assert json_path.exists()

    def test_creates_parent_directories(self, tmp_path: Path, sample_exercise_bank: ExerciseQuestionsBank):
        """Should create parent directories if they don't exist."""
        json_path = tmp_path / "a" / "b" / "exercise.json"
        
        save_exercise_bank_json(sample_exercise_bank, str(json_path), TEST_SUBJECT_ID)
        
        assert json_path.exists()

    def test_json_contains_subject_id(self, tmp_path: Path, sample_exercise_bank: ExerciseQuestionsBank):
        """JSON should contain subject_id."""
        json_path = tmp_path / "exercise.json"
        save_exercise_bank_json(sample_exercise_bank, str(json_path), TEST_SUBJECT_ID)
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["subject_id"] == TEST_SUBJECT_ID

    def test_json_contains_chapter_id(self, tmp_path: Path, sample_exercise_bank: ExerciseQuestionsBank):
        """JSON should contain generated chapter_id."""
        json_path = tmp_path / "exercise.json"
        save_exercise_bank_json(sample_exercise_bank, str(json_path), TEST_SUBJECT_ID)
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert "chapter_id" in data
        assert validate_uuid(data["chapter_id"])

    def test_questions_have_ids(self, tmp_path: Path, sample_exercise_bank: ExerciseQuestionsBank):
        """Each question should have a generated id."""
        json_path = tmp_path / "exercise.json"
        save_exercise_bank_json(sample_exercise_bank, str(json_path), TEST_SUBJECT_ID)
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for question in data["exercise_questions"]:
            assert "id" in question
            assert validate_uuid(question["id"])

    def test_ids_are_deterministic(self, tmp_path: Path, sample_exercise_bank: ExerciseQuestionsBank):
        """Same input should produce same IDs."""
        json_path1 = tmp_path / "exercise1.json"
        json_path2 = tmp_path / "exercise2.json"
        
        save_exercise_bank_json(sample_exercise_bank, str(json_path1), TEST_SUBJECT_ID)
        save_exercise_bank_json(sample_exercise_bank, str(json_path2), TEST_SUBJECT_ID)
        
        with open(json_path1, "r", encoding="utf-8") as f:
            data1 = json.load(f)
        with open(json_path2, "r", encoding="utf-8") as f:
            data2 = json.load(f)
        
        assert data1["chapter_id"] == data2["chapter_id"]
        for q1, q2 in zip(data1["exercise_questions"], data2["exercise_questions"]):
            assert q1["id"] == q2["id"]

    def test_preserves_question_data(self, tmp_path: Path, sample_exercise_bank: ExerciseQuestionsBank):
        """Question data should be preserved."""
        json_path = tmp_path / "exercise.json"
        save_exercise_bank_json(sample_exercise_bank, str(json_path), TEST_SUBJECT_ID)
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        first_q = data["exercise_questions"][0]
        assert first_q["question_text"] == "What is 2+2?"
        assert first_q["explanation"] == "Simple addition: 2+2=4"
        assert first_q["answer_text"] == "4"


class TestLoadExerciseBankJson:
    """Tests for load_exercise_bank_json function."""

    def test_load_saved_json(self, tmp_path: Path, sample_exercise_bank: ExerciseQuestionsBank):
        """Should load a previously saved JSON."""
        json_path = tmp_path / "exercise.json"
        save_exercise_bank_json(sample_exercise_bank, str(json_path), TEST_SUBJECT_ID)
        
        data = load_exercise_bank_json(str(json_path))
        
        assert data["subject_id"] == TEST_SUBJECT_ID
        assert data["chapter_name"] == "Chapter 1: Numbers"
        assert len(data["exercise_questions"]) == 2

    def test_loaded_questions_have_ids(self, tmp_path: Path, sample_exercise_bank: ExerciseQuestionsBank):
        """Loaded questions should retain their IDs."""
        json_path = tmp_path / "exercise.json"
        save_exercise_bank_json(sample_exercise_bank, str(json_path), TEST_SUBJECT_ID)
        
        data = load_exercise_bank_json(str(json_path))
        
        for question in data["exercise_questions"]:
            assert "id" in question
            assert validate_uuid(question["id"])

    def test_file_not_found(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_exercise_bank_json("/nonexistent/path.json")

    def test_sanitizes_null_values(self, tmp_path: Path):
        """Should sanitize null values on load."""
        json_path = tmp_path / "exercise.json"
        # Create JSON with null values
        data = {
            "chapter_name": "Test",
            "chapter_id": TEST_SUBJECT_ID,
            "subject_id": TEST_SUBJECT_ID,
            "exercise_questions": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "question_text": None,
                    "explanation": None,
                    "answer_text": None,
                    "question_type": None
                }
            ]
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        
        loaded = load_exercise_bank_json(str(json_path))
        
        q = loaded["exercise_questions"][0]
        assert q["question_text"] == ""
        assert q["explanation"] == ""
        assert q["question_type"] == "Short Answer"


class TestSaveSolvedBankJson:
    """Tests for save_solved_bank_json function."""

    def test_creates_json_file(self, tmp_path: Path, sample_solved_bank: SolvedExamplesBank):
        """Should create a JSON file at the specified path."""
        json_path = tmp_path / "solved.json"
        
        save_solved_bank_json(sample_solved_bank, str(json_path), TEST_SUBJECT_ID)
        
        assert json_path.exists()

    def test_json_contains_ids(self, tmp_path: Path, sample_solved_bank: SolvedExamplesBank):
        """JSON should contain subject_id, chapter_id, and question ids."""
        json_path = tmp_path / "solved.json"
        save_solved_bank_json(sample_solved_bank, str(json_path), TEST_SUBJECT_ID)
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["subject_id"] == TEST_SUBJECT_ID
        assert validate_uuid(data["chapter_id"])
        for q in data["solved_examples_questions"]:
            assert validate_uuid(q["id"])


class TestLoadSolvedBankJson:
    """Tests for load_solved_bank_json function."""

    def test_load_saved_json(self, tmp_path: Path, sample_solved_bank: SolvedExamplesBank):
        """Should load a previously saved JSON."""
        json_path = tmp_path / "solved.json"
        save_solved_bank_json(sample_solved_bank, str(json_path), TEST_SUBJECT_ID)
        
        data = load_solved_bank_json(str(json_path))
        
        assert data["subject_id"] == TEST_SUBJECT_ID
        assert data["chapter_name"] == "Chapter 1: Numbers"
        assert len(data["solved_examples_questions"]) == 1
