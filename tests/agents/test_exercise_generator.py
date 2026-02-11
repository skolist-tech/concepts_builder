"""Tests for exercise_questions_generator agent with mocked Gemini."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from agents.exercise_questions_generator import generate_exercise_questions
from schemas.bank_questions.question_bank_schema import ExerciseQuestionsBank, ExerciseQuestion


@pytest.fixture
def sample_exercise_bank():
    """Create a sample ExerciseQuestionsBank for mock responses."""
    return ExerciseQuestionsBank(
        chapter_name="Numbers",
        exercise_questions=[
            ExerciseQuestion(
                question_text="What is 2+2?",
                explanation="Simple addition",
                answer_text="4",
                question_type="Short Answer",
                concepts=["Addition"]
            )
        ]
    )


@pytest.fixture
def mock_gemini_response(sample_exercise_bank):
    """Create a mock Gemini response."""
    mock_response = MagicMock()
    mock_response.parsed = sample_exercise_bank
    mock_response.text = '{"chapter_name": "Numbers"}'
    return mock_response


@pytest.fixture
def sample_pdf_file(tmp_path: Path) -> Path:
    """Create a sample PDF file for testing."""
    pdf_file = tmp_path / "chapter.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 test content")
    return pdf_file


@pytest.fixture
def sample_concepts():
    """Sample concepts list."""
    return ["Addition", "Subtraction", "Counting"]


class TestGenerateExerciseQuestions:
    """Tests for generate_exercise_questions function."""

    @pytest.mark.asyncio
    @patch("agents.exercise_questions_generator.read_pdf_as_part")
    @patch("agents.exercise_questions_generator.get_gemini_client")
    async def test_returns_exercise_bank(
        self,
        mock_get_client,
        mock_read_pdf,
        sample_pdf_file,
        sample_concepts,
        mock_gemini_response
    ):
        """Should return ExerciseQuestionsBank on success."""
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_gemini_response)
        mock_get_client.return_value = mock_client
        mock_read_pdf.return_value = MagicMock()
        
        result = await generate_exercise_questions(
            "Extract questions",
            str(sample_pdf_file),
            sample_concepts
        )
        
        assert isinstance(result, ExerciseQuestionsBank)
        assert result.chapter_name == "Numbers"
        assert len(result.exercise_questions) == 1

    @pytest.mark.asyncio
    @patch("agents.exercise_questions_generator.read_pdf_as_part")
    @patch("agents.exercise_questions_generator.get_gemini_client")
    async def test_appends_concepts_to_prompt(
        self,
        mock_get_client,
        mock_read_pdf,
        sample_pdf_file,
        sample_concepts,
        mock_gemini_response
    ):
        """Should append concepts list to the prompt."""
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_gemini_response)
        mock_get_client.return_value = mock_client
        mock_read_pdf.return_value = MagicMock()
        
        await generate_exercise_questions(
            "Extract questions",
            str(sample_pdf_file),
            sample_concepts
        )
        
        call_kwargs = mock_client.aio.models.generate_content.call_args[1]
        prompt = call_kwargs["contents"][0]
        assert "CONCEPTS LIST:" in prompt
        assert "- Addition" in prompt

    @pytest.mark.asyncio
    async def test_raises_error_empty_concepts(self, sample_pdf_file):
        """Should raise ValueError for empty concepts list."""
        with pytest.raises(ValueError, match="concepts_list cannot be empty"):
            await generate_exercise_questions("Prompt", str(sample_pdf_file), [])

    @pytest.mark.asyncio
    async def test_raises_error_empty_prompt(self, sample_pdf_file, sample_concepts):
        """Should raise ValueError for empty prompt."""
        with pytest.raises(ValueError, match="prompt cannot be empty"):
            await generate_exercise_questions("", str(sample_pdf_file), sample_concepts)

    @pytest.mark.asyncio
    async def test_raises_error_empty_pdf_path(self, sample_concepts):
        """Should raise ValueError for empty pdf_path."""
        with pytest.raises(ValueError, match="pdf_path cannot be empty"):
            await generate_exercise_questions("Prompt", "", sample_concepts)

    @pytest.mark.asyncio
    async def test_raises_file_not_found(self, sample_concepts):
        """Should raise FileNotFoundError for missing PDF."""
        with pytest.raises(FileNotFoundError):
            await generate_exercise_questions(
                "Prompt",
                "/nonexistent/file.pdf",
                sample_concepts
            )

    @pytest.mark.asyncio
    @patch("agents.exercise_questions_generator.read_pdf_as_part")
    @patch("agents.exercise_questions_generator.get_gemini_client")
    async def test_raises_on_parse_failure(
        self,
        mock_get_client,
        mock_read_pdf,
        sample_pdf_file,
        sample_concepts
    ):
        """Should raise ValueError if response cannot be parsed."""
        mock_response = MagicMock()
        mock_response.parsed = None
        mock_response.text = "Invalid"
        
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        mock_read_pdf.return_value = MagicMock()
        
        with pytest.raises(ValueError, match="Failed to parse response"):
            await generate_exercise_questions(
                "Prompt",
                str(sample_pdf_file),
                sample_concepts
            )
