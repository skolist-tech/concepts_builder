"""Tests for concept_generator agent with mocked Gemini."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from agents.concept_generator import generate_concepts
from schemas.concept_schema import Chapter, Topic, Concept


@pytest.fixture
def sample_chapter():
    """Create a sample Chapter object for mock responses."""
    return Chapter(
        name="Numbers",
        description="Introduction to numbers",
        topics=[
            Topic(
                name="Natural Numbers",
                description="Counting numbers",
                position=1,
                concepts=[
                    Concept(
                        name="Counting",
                        description="Learn to count",
                        page_number=1
                    )
                ]
            )
        ]
    )


@pytest.fixture
def mock_gemini_response(sample_chapter):
    """Create a mock Gemini response with parsed Chapter."""
    mock_response = MagicMock()
    mock_response.parsed = sample_chapter
    mock_response.text = '{"name": "Numbers"}'
    return mock_response


@pytest.fixture
def sample_pdf_file(tmp_path: Path) -> Path:
    """Create a sample PDF file for testing."""
    pdf_file = tmp_path / "chapter.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 test content")
    return pdf_file


class TestGenerateConcepts:
    """Tests for generate_concepts function."""

    @pytest.mark.asyncio
    @patch("agents.concept_generator.read_pdf_as_part")
    @patch("agents.concept_generator.get_gemini_client")
    async def test_returns_chapter(
        self, 
        mock_get_client, 
        mock_read_pdf, 
        sample_pdf_file,
        mock_gemini_response
    ):
        """Should return a Chapter object on success."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_gemini_response)
        mock_get_client.return_value = mock_client
        mock_read_pdf.return_value = MagicMock()
        
        result = await generate_concepts("Extract concepts", str(sample_pdf_file))
        
        assert isinstance(result, Chapter)
        assert result.name == "Numbers"
        assert len(result.topics) == 1

    @pytest.mark.asyncio
    @patch("agents.concept_generator.read_pdf_as_part")
    @patch("agents.concept_generator.get_gemini_client")
    async def test_calls_gemini_with_prompt_and_pdf(
        self, 
        mock_get_client, 
        mock_read_pdf,
        sample_pdf_file,
        mock_gemini_response
    ):
        """Should call Gemini with prompt and PDF part."""
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_gemini_response)
        mock_get_client.return_value = mock_client
        
        mock_part = MagicMock()
        mock_read_pdf.return_value = mock_part
        
        await generate_concepts("Extract concepts", str(sample_pdf_file))
        
        # Verify Gemini was called
        mock_client.aio.models.generate_content.assert_called_once()
        call_kwargs = mock_client.aio.models.generate_content.call_args[1]
        assert call_kwargs["contents"] == ["Extract concepts", mock_part]

    @pytest.mark.asyncio
    @patch("agents.concept_generator.read_pdf_as_part")
    @patch("agents.concept_generator.get_gemini_client")
    async def test_raises_value_error_on_parse_failure(
        self,
        mock_get_client,
        mock_read_pdf,
        sample_pdf_file
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
            await generate_concepts("Extract concepts", str(sample_pdf_file))

    @pytest.mark.asyncio
    async def test_raises_file_not_found(self):
        """Should raise FileNotFoundError for missing PDF."""
        with pytest.raises(FileNotFoundError):
            await generate_concepts("Extract concepts", "/nonexistent/file.pdf")

    @pytest.mark.asyncio
    @patch("agents.concept_generator.read_pdf_as_part")
    @patch("agents.concept_generator.get_gemini_client")
    @patch("agents.concept_generator.settings")
    async def test_uses_configured_model(
        self,
        mock_settings,
        mock_get_client,
        mock_read_pdf,
        sample_pdf_file,
        mock_gemini_response
    ):
        """Should use the model from settings."""
        mock_settings.gemini_model = "gemini-2.0-flash"
        
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_gemini_response)
        mock_get_client.return_value = mock_client
        mock_read_pdf.return_value = MagicMock()
        
        await generate_concepts("Extract concepts", str(sample_pdf_file))
        
        call_kwargs = mock_client.aio.models.generate_content.call_args[1]
        assert call_kwargs["model"] == "gemini-2.0-flash"
