"""Tests for solved_examples_generator agent with mocked Gemini."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from agents.solved_examples_generator import generate_solved_examples
from schemas.bank_questions.question_bank_schema import SolvedExamplesBank, SolvedExample


@pytest.fixture
def sample_solved_bank():
    """Create a sample SolvedExamplesBank for mock responses."""
    return SolvedExamplesBank(
        chapter_name="Numbers",
        solved_examples_questions=[
            SolvedExample(
                question_text="Example: Find 5+3",
                explanation="Step by step solution",
                answer_text="8",
                question_type="Short Answer",
                concepts=["Addition"]
            )
        ]
    )


@pytest.fixture
def mock_gemini_response(sample_solved_bank):
    """Create a mock Gemini response."""
    mock_response = MagicMock()
    mock_response.parsed = sample_solved_bank
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
    return ["Addition", "Subtraction"]


class TestGenerateSolvedExamples:
    """Tests for generate_solved_examples function."""

    @pytest.mark.asyncio
    @patch("agents.solved_examples_generator.read_pdf_as_part")
    @patch("agents.solved_examples_generator.get_gemini_client")
    async def test_returns_solved_bank(
        self,
        mock_get_client,
        mock_read_pdf,
        sample_pdf_file,
        sample_concepts,
        mock_gemini_response
    ):
        """Should return SolvedExamplesBank on success."""
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_gemini_response)
        mock_get_client.return_value = mock_client
        mock_read_pdf.return_value = MagicMock()
        
        result = await generate_solved_examples(
            "Extract solved examples",
            str(sample_pdf_file),
            sample_concepts
        )
        
        assert isinstance(result, SolvedExamplesBank)
        assert result.chapter_name == "Numbers"
        assert len(result.solved_examples_questions) == 1

    @pytest.mark.asyncio
    @patch("agents.solved_examples_generator.read_pdf_as_part")
    @patch("agents.solved_examples_generator.get_gemini_client")
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
        
        await generate_solved_examples(
            "Extract examples",
            str(sample_pdf_file),
            sample_concepts
        )
        
        call_kwargs = mock_client.aio.models.generate_content.call_args[1]
        prompt = call_kwargs["contents"][0]
        assert "CONCEPTS LIST:" in prompt
        assert "- Addition" in prompt
        assert "- Subtraction" in prompt

    @pytest.mark.asyncio
    async def test_raises_error_empty_concepts(self, sample_pdf_file):
        """Should raise ValueError for empty concepts list."""
        with pytest.raises(ValueError, match="concepts_list cannot be empty"):
            await generate_solved_examples("Prompt", str(sample_pdf_file), [])

    @pytest.mark.asyncio
    async def test_raises_error_empty_prompt(self, sample_pdf_file, sample_concepts):
        """Should raise ValueError for empty prompt."""
        with pytest.raises(ValueError, match="prompt cannot be empty"):
            await generate_solved_examples("", str(sample_pdf_file), sample_concepts)

    @pytest.mark.asyncio
    async def test_raises_error_empty_pdf_path(self, sample_concepts):
        """Should raise ValueError for empty pdf_path."""
        with pytest.raises(ValueError, match="pdf_path cannot be empty"):
            await generate_solved_examples("Prompt", "", sample_concepts)

    @pytest.mark.asyncio
    async def test_raises_file_not_found(self, sample_concepts):
        """Should raise FileNotFoundError for missing PDF."""
        with pytest.raises(FileNotFoundError):
            await generate_solved_examples(
                "Prompt",
                "/nonexistent/file.pdf",
                sample_concepts
            )

    @pytest.mark.asyncio
    @patch("agents.solved_examples_generator.read_pdf_as_part")
    @patch("agents.solved_examples_generator.get_gemini_client")
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
        mock_response.text = "Invalid response"
        
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        mock_read_pdf.return_value = MagicMock()
        
        with pytest.raises(ValueError, match="Failed to parse response"):
            await generate_solved_examples(
                "Prompt",
                str(sample_pdf_file),
                sample_concepts
            )
