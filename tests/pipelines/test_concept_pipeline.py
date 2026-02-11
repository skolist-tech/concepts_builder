"""Tests for concept_pipeline with mocked agents."""

import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock

from pipelines.concept_pipeline import process_chapter_for_concepts
from schemas.concept_schema import Chapter, Topic, Concept


@pytest.fixture
def sample_chapter():
    """Create a sample Chapter for testing."""
    return Chapter(
        name="Numbers",
        description="Introduction to numbers",
        topics=[
            Topic(
                name="Counting",
                description="Learn counting",
                position=1,
                concepts=[
                    Concept(
                        name="Basic Counting",
                        description="Count 1-10",
                        page_number=5
                    )
                ]
            )
        ]
    )


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a sample PDF file."""
    pdf_file = tmp_path / "chapter.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 test content")
    return pdf_file


TEST_SUBJECT_ID = "550e8400-e29b-41d4-a716-446655440000"


class TestProcessChapterForConcepts:
    """Tests for process_chapter_for_concepts function."""

    @pytest.mark.asyncio
    @patch("pipelines.concept_pipeline.generate_concepts")
    async def test_generates_and_saves_csv(
        self,
        mock_generate,
        sample_pdf,
        sample_chapter,
        tmp_path
    ):
        """Should generate concepts and save to CSV."""
        mock_generate.return_value = sample_chapter
        output_csv = tmp_path / "output" / "chapter_concepts.csv"
        
        result = await process_chapter_for_concepts(
            chapter_pdf_path=sample_pdf,
            prompt="Extract concepts",
            subject_id=TEST_SUBJECT_ID,
            output_csv_path=output_csv,
            chapter_position=1
        )
        
        assert result == sample_chapter
        assert output_csv.exists()

    @pytest.mark.asyncio
    @patch("pipelines.concept_pipeline.generate_concepts")
    async def test_calls_agent_with_prompt_and_pdf(
        self,
        mock_generate,
        sample_pdf,
        sample_chapter,
        tmp_path
    ):
        """Should call generate_concepts with correct args."""
        mock_generate.return_value = sample_chapter
        output_csv = tmp_path / "chapter_concepts.csv"
        
        await process_chapter_for_concepts(
            chapter_pdf_path=sample_pdf,
            prompt="My custom prompt",
            subject_id=TEST_SUBJECT_ID,
            output_csv_path=output_csv
        )
        
        mock_generate.assert_called_once_with(
            prompt="My custom prompt",
            pdf_path=str(sample_pdf)
        )

    @pytest.mark.asyncio
    async def test_raises_file_not_found(self, tmp_path):
        """Should raise FileNotFoundError for missing PDF."""
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            await process_chapter_for_concepts(
                chapter_pdf_path=tmp_path / "nonexistent.pdf",
                prompt="Prompt",
                subject_id=TEST_SUBJECT_ID,
                output_csv_path=tmp_path / "output.csv"
            )

    @pytest.mark.asyncio
    @patch("pipelines.concept_pipeline.generate_concepts")
    async def test_csv_contains_uuids(
        self,
        mock_generate,
        sample_pdf,
        sample_chapter,
        tmp_path
    ):
        """Generated CSV should contain UUID columns."""
        import csv
        
        mock_generate.return_value = sample_chapter
        output_csv = tmp_path / "chapter_concepts.csv"
        
        await process_chapter_for_concepts(
            chapter_pdf_path=sample_pdf,
            prompt="Extract concepts",
            subject_id=TEST_SUBJECT_ID,
            output_csv_path=output_csv
        )
        
        with open(output_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        
        assert "concept_id" in row
        assert "topic_id" in row
        assert "chapter_id" in row
        assert "subject_id" in row
        assert row["subject_id"] == TEST_SUBJECT_ID

    @pytest.mark.asyncio
    @patch("pipelines.concept_pipeline.generate_concepts")
    async def test_creates_output_directory(
        self,
        mock_generate,
        sample_pdf,
        sample_chapter,
        tmp_path
    ):
        """Should create parent directories for output file."""
        mock_generate.return_value = sample_chapter
        output_csv = tmp_path / "a" / "b" / "c" / "chapter.csv"
        
        await process_chapter_for_concepts(
            chapter_pdf_path=sample_pdf,
            prompt="Extract concepts",
            subject_id=TEST_SUBJECT_ID,
            output_csv_path=output_csv
        )
        
        assert output_csv.exists()
        assert output_csv.parent.exists()
