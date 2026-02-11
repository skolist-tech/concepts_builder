"""Tests for agent base utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from agents.base import (
    GeminiClient,
    read_pdf_as_part,
    format_concepts_list,
    get_gemini_client
)


class TestGeminiClient:
    """Tests for GeminiClient singleton."""

    def setup_method(self):
        """Reset client before each test."""
        GeminiClient.reset_client()

    def teardown_method(self):
        """Clean up after each test."""
        GeminiClient.reset_client()

    def test_reset_client(self):
        """reset_client should clear the singleton instance."""
        GeminiClient._instance = MagicMock()
        GeminiClient.reset_client()
        assert GeminiClient._instance is None

    @patch("agents.base.settings")
    @patch("agents.base.genai.Client")
    def test_get_client_creates_instance(self, mock_client_cls, mock_settings):
        """get_client should create a new client if none exists."""
        mock_settings.gemini_api_key = "test-api-key"
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        client = GeminiClient.get_client()
        
        mock_client_cls.assert_called_once_with(api_key="test-api-key")
        assert client == mock_client

    @patch("agents.base.settings")
    @patch("agents.base.genai.Client")
    def test_get_client_returns_same_instance(self, mock_client_cls, mock_settings):
        """get_client should return the same instance on subsequent calls."""
        mock_settings.gemini_api_key = "test-api-key"
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        client1 = GeminiClient.get_client()
        client2 = GeminiClient.get_client()
        
        # Should only create once
        assert mock_client_cls.call_count == 1
        assert client1 is client2

    @patch("agents.base.settings")
    @patch.dict("os.environ", {}, clear=True)
    def test_get_client_raises_without_api_key(self, mock_settings):
        """get_client should raise ValueError without API key."""
        mock_settings.gemini_api_key = None
        
        with pytest.raises(ValueError, match="GEMINI_API_KEY not set"):
            GeminiClient.get_client()


class TestReadPdfAsPart:
    """Tests for read_pdf_as_part function."""

    def test_file_not_found(self):
        """Should raise FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            read_pdf_as_part("/nonexistent/file.pdf")

    @patch("agents.base.types.Part.from_bytes")
    def test_reads_pdf_and_creates_part(self, mock_from_bytes, tmp_path: Path):
        """Should read PDF and create Part with correct mime type."""
        # Create a dummy PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 dummy content")
        
        mock_part = MagicMock()
        mock_from_bytes.return_value = mock_part
        
        result = read_pdf_as_part(str(pdf_file))
        
        mock_from_bytes.assert_called_once()
        call_kwargs = mock_from_bytes.call_args[1]
        assert call_kwargs["mime_type"] == "application/pdf"
        assert b"%PDF-1.4 dummy content" in call_kwargs["data"]
        assert result == mock_part


class TestFormatConceptsList:
    """Tests for format_concepts_list function."""

    def test_empty_list_returns_empty_string(self):
        """Empty list should return empty string."""
        assert format_concepts_list([]) == ""

    def test_single_concept(self):
        """Single concept should be formatted correctly."""
        result = format_concepts_list(["Addition"])
        assert "CONCEPTS LIST:" in result
        assert "- Addition" in result

    def test_multiple_concepts(self):
        """Multiple concepts should all be included."""
        concepts = ["Addition", "Subtraction", "Multiplication"]
        result = format_concepts_list(concepts)
        
        assert "CONCEPTS LIST:" in result
        assert "- Addition" in result
        assert "- Subtraction" in result
        assert "- Multiplication" in result

    def test_preserves_concept_text(self):
        """Concept names should be preserved exactly."""
        concepts = ["Complex Concept: With Special (Characters)"]
        result = format_concepts_list(concepts)
        assert "- Complex Concept: With Special (Characters)" in result


class TestGetGeminiClient:
    """Tests for get_gemini_client convenience function."""

    def setup_method(self):
        """Reset client before each test."""
        GeminiClient.reset_client()

    def teardown_method(self):
        """Clean up after each test."""
        GeminiClient.reset_client()

    @patch("agents.base.settings")
    @patch("agents.base.genai.Client")
    def test_returns_client(self, mock_client_cls, mock_settings):
        """Should return a Gemini client."""
        mock_settings.gemini_api_key = "test-key"
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        result = get_gemini_client()
        
        assert result == mock_client
