"""Tests for questions_pipeline with mocked agents."""

import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
import csv

from pipelines.questions_pipeline import (
    load_concepts_from_csv,
    process_chapter_for_solved_examples,
    process_chapter_for_exercise_questions
)
from schemas.bank_questions.question_bank_schema import (
    SolvedExamplesBank,
    SolvedExample,
    ExerciseQuestionsBank,
    ExerciseQuestion
)


TEST_SUBJECT_ID = "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_concepts_csv(tmp_path: Path) -> Path:
    """Create a sample concepts CSV file."""
    csv_path = tmp_path / "concepts.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "concept_id", "concept_name", "concept_description", 
            "topic_id", "topic_name", "chapter_id", "chapter_name", "subject_id"
        ])
        writer.writerow([
            "uuid1", "Addition", "Learn addition",
            "uuid2", "Basic Math", "uuid3", "Numbers", TEST_SUBJECT_ID
        ])
        writer.writerow([
            "uuid4", "Subtraction", "Learn subtraction",
            "uuid2", "Basic Math", "uuid3", "Numbers", TEST_SUBJECT_ID
        ])
    return csv_path


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a sample PDF file."""
    pdf_file = tmp_path / "chapter.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 test content")
    return pdf_file


@pytest.fixture
def sample_solved_bank():
    """Create a sample SolvedExamplesBank."""
    return SolvedExamplesBank(
        chapter_name="Numbers",
        solved_examples_questions=[
            SolvedExample(
                question_text="Example: 2+2=?",
                explanation="Addition example",
                answer_text="4",
                question_type="Short Answer"
            )
        ]
    )


@pytest.fixture
def sample_exercise_bank():
    """Create a sample ExerciseQuestionsBank."""
    return ExerciseQuestionsBank(
        chapter_name="Numbers",
        exercise_questions=[
            ExerciseQuestion(
                question_text="What is 3+3?",
                explanation="Simple addition",
                answer_text="6",
                question_type="Short Answer"
            )
        ]
    )


class TestLoadConceptsFromCsv:
    """Tests for load_concepts_from_csv function."""

    def test_loads_concepts(self, sample_concepts_csv):
        """Should load concept names from CSV."""
        concepts = load_concepts_from_csv(sample_concepts_csv)
        
        assert len(concepts) == 2
        assert "Addition" in concepts
        assert "Subtraction" in concepts

    def test_file_not_found(self, tmp_path):
        """Should raise FileNotFoundError for missing CSV."""
        with pytest.raises(FileNotFoundError, match="Concepts CSV file not found"):
            load_concepts_from_csv(tmp_path / "nonexistent.csv")

    def test_empty_csv_raises_error(self, tmp_path):
        """Should raise ValueError for CSV with no concepts."""
        csv_path = tmp_path / "empty.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["concept_id", "concept_name"])
        
        with pytest.raises(ValueError, match="No concepts found"):
            load_concepts_from_csv(csv_path)


class TestProcessChapterForSolvedExamples:
    """Tests for process_chapter_for_solved_examples function."""

    @pytest.mark.asyncio
    @patch("pipelines.questions_pipeline.generate_solved_examples")
    async def test_generates_and_saves_json(
        self,
        mock_generate,
        sample_pdf,
        sample_concepts_csv,
        sample_solved_bank,
        tmp_path
    ):
        """Should generate solved examples and save to JSON."""
        mock_generate.return_value = sample_solved_bank
        output_json = tmp_path / "solved.json"
        
        result = await process_chapter_for_solved_examples(
            chapter_pdf_path=sample_pdf,
            prompt="Extract solved examples",
            subject_id=TEST_SUBJECT_ID,
            concepts_csv_path=sample_concepts_csv,
            output_json_path=output_json
        )
        
        assert result == sample_solved_bank
        assert output_json.exists()

    @pytest.mark.asyncio
    @patch("pipelines.questions_pipeline.generate_solved_examples")
    async def test_passes_concepts_to_agent(
        self,
        mock_generate,
        sample_pdf,
        sample_concepts_csv,
        sample_solved_bank,
        tmp_path
    ):
        """Should pass concepts list to the agent."""
        mock_generate.return_value = sample_solved_bank
        output_json = tmp_path / "solved.json"
        
        await process_chapter_for_solved_examples(
            chapter_pdf_path=sample_pdf,
            prompt="Extract solved examples",
            subject_id=TEST_SUBJECT_ID,
            concepts_csv_path=sample_concepts_csv,
            output_json_path=output_json
        )
        
        call_kwargs = mock_generate.call_args[1]
        assert "Addition" in call_kwargs["concepts_list"]
        assert "Subtraction" in call_kwargs["concepts_list"]

    @pytest.mark.asyncio
    async def test_pdf_not_found(self, sample_concepts_csv, tmp_path):
        """Should raise FileNotFoundError for missing PDF."""
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            await process_chapter_for_solved_examples(
                chapter_pdf_path=tmp_path / "nonexistent.pdf",
                prompt="Prompt",
                subject_id=TEST_SUBJECT_ID,
                concepts_csv_path=sample_concepts_csv,
                output_json_path=tmp_path / "output.json"
            )


class TestProcessChapterForExerciseQuestions:
    """Tests for process_chapter_for_exercise_questions function."""

    @pytest.mark.asyncio
    @patch("pipelines.questions_pipeline.generate_exercise_questions")
    async def test_generates_and_saves_json(
        self,
        mock_generate,
        sample_pdf,
        sample_concepts_csv,
        sample_exercise_bank,
        tmp_path
    ):
        """Should generate exercise questions and save to JSON."""
        mock_generate.return_value = sample_exercise_bank
        output_json = tmp_path / "exercise.json"
        
        result = await process_chapter_for_exercise_questions(
            chapter_pdf_path=sample_pdf,
            prompt="Extract exercise questions",
            subject_id=TEST_SUBJECT_ID,
            concepts_csv_path=sample_concepts_csv,
            output_json_path=output_json
        )
        
        assert result == sample_exercise_bank
        assert output_json.exists()

    @pytest.mark.asyncio
    @patch("pipelines.questions_pipeline.generate_exercise_questions")
    async def test_json_contains_uuids(
        self,
        mock_generate,
        sample_pdf,
        sample_concepts_csv,
        sample_exercise_bank,
        tmp_path
    ):
        """Generated JSON should contain UUIDs."""
        import json
        
        mock_generate.return_value = sample_exercise_bank
        output_json = tmp_path / "exercise.json"
        
        await process_chapter_for_exercise_questions(
            chapter_pdf_path=sample_pdf,
            prompt="Extract exercise questions",
            subject_id=TEST_SUBJECT_ID,
            concepts_csv_path=sample_concepts_csv,
            output_json_path=output_json
        )
        
        with open(output_json, encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["subject_id"] == TEST_SUBJECT_ID
        assert "chapter_id" in data
        for q in data["exercise_questions"]:
            assert "id" in q
