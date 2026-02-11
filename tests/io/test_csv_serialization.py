"""I/O tests for CSV serialization with tmp_path fixture."""

import pytest
import csv
from pathlib import Path

from schemas.chapter_to_csv import save_csv, load_csv_with_uuids, create_csv_with_uuids, get_concept_names_from_csv
from schemas.concept_schema import Chapter, Topic, Concept
from utils.uuid_generator import validate_uuid


TEST_SUBJECT_ID = "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_chapter() -> Chapter:
    """Create a sample Chapter for testing."""
    return Chapter(
        name="Numbers and Operations",
        description="Introduction to numbers and basic operations",
        topics=[
            Topic(
                name="Natural Numbers",
                description="Numbers used for counting",
                position=1,
                concepts=[
                    Concept(
                        name="Counting from 1 to 100",
                        description="Learn to count natural numbers",
                        page_number=5
                    ),
                    Concept(
                        name="Number Comparison",
                        description="Compare two natural numbers",
                        page_number=7
                    ),
                ]
            ),
            Topic(
                name="Addition",
                description="Adding numbers together",
                position=2,
                concepts=[
                    Concept(
                        name="Single Digit Addition",
                        description="Add numbers 0-9",
                        page_number=10
                    ),
                ]
            ),
        ]
    )


class TestSaveCsv:
    """Tests for save_csv function."""

    def test_creates_csv_file(self, tmp_path: Path, sample_chapter: Chapter):
        """Should create a CSV file at the specified path."""
        csv_path = tmp_path / "output" / "chapter.csv"
        
        save_csv(sample_chapter, str(csv_path), position=1, subject_id=TEST_SUBJECT_ID)
        
        assert csv_path.exists()

    def test_creates_parent_directories(self, tmp_path: Path, sample_chapter: Chapter):
        """Should create parent directories if they don't exist."""
        csv_path = tmp_path / "a" / "b" / "c" / "chapter.csv"
        
        save_csv(sample_chapter, str(csv_path), position=1, subject_id=TEST_SUBJECT_ID)
        
        assert csv_path.exists()
        assert (tmp_path / "a" / "b" / "c").is_dir()

    def test_csv_has_correct_headers(self, tmp_path: Path, sample_chapter: Chapter):
        """Should include all required headers in CSV."""
        csv_path = tmp_path / "chapter.csv"
        save_csv(sample_chapter, str(csv_path), position=1, subject_id=TEST_SUBJECT_ID)
        
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
        
        expected_headers = [
            "concept_id", "concept_name", "concept_description", "concept_page_number",
            "topic_id", "topic_name", "topic_description", "topic_position",
            "chapter_id", "chapter_name", "chapter_description", "chapter_position",
            "subject_id"
        ]
        assert headers == expected_headers

    def test_csv_has_correct_row_count(self, tmp_path: Path, sample_chapter: Chapter):
        """Should have one row per concept plus header."""
        csv_path = tmp_path / "chapter.csv"
        save_csv(sample_chapter, str(csv_path), position=1, subject_id=TEST_SUBJECT_ID)
        
        with open(csv_path, newline="", encoding="utf-8") as f:
            lines = list(csv.reader(f))
        
        # 3 concepts + 1 header = 4 lines
        assert len(lines) == 4

    def test_csv_contains_valid_uuids(self, tmp_path: Path, sample_chapter: Chapter):
        """All UUID columns should contain valid UUIDs."""
        csv_path = tmp_path / "chapter.csv"
        save_csv(sample_chapter, str(csv_path), position=1, subject_id=TEST_SUBJECT_ID)
        
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert validate_uuid(row["concept_id"]), f"Invalid concept_id: {row['concept_id']}"
                assert validate_uuid(row["topic_id"]), f"Invalid topic_id: {row['topic_id']}"
                assert validate_uuid(row["chapter_id"]), f"Invalid chapter_id: {row['chapter_id']}"
                assert validate_uuid(row["subject_id"]), f"Invalid subject_id: {row['subject_id']}"

    def test_uuids_are_deterministic(self, tmp_path: Path, sample_chapter: Chapter):
        """Same input should produce same UUIDs on multiple saves."""
        csv_path1 = tmp_path / "chapter1.csv"
        csv_path2 = tmp_path / "chapter2.csv"
        
        save_csv(sample_chapter, str(csv_path1), position=1, subject_id=TEST_SUBJECT_ID)
        save_csv(sample_chapter, str(csv_path2), position=1, subject_id=TEST_SUBJECT_ID)
        
        # Compare file contents
        content1 = csv_path1.read_text(encoding="utf-8")
        content2 = csv_path2.read_text(encoding="utf-8")
        assert content1 == content2


class TestCreateCsvWithUuids:
    """Tests for create_csv_with_uuids function."""

    def test_returns_headers_and_rows(self, sample_chapter: Chapter):
        """Should return tuple of headers and rows."""
        headers, rows = create_csv_with_uuids(sample_chapter, position=1, subject_id=TEST_SUBJECT_ID)
        
        assert isinstance(headers, list)
        assert isinstance(rows, list)
        assert len(headers) == 13  # All columns
        assert len(rows) == 3  # 3 concepts

    def test_row_data_matches_concepts(self, sample_chapter: Chapter):
        """Row data should match concept information."""
        headers, rows = create_csv_with_uuids(sample_chapter, position=1, subject_id=TEST_SUBJECT_ID)
        
        # Create dict for easier access
        header_index = {h: i for i, h in enumerate(headers)}
        
        # Check first row
        first_row = rows[0]
        assert first_row[header_index["concept_name"]] == "Counting from 1 to 100"
        assert first_row[header_index["topic_name"]] == "Natural Numbers"
        assert first_row[header_index["chapter_name"]] == "Numbers and Operations"
        assert first_row[header_index["subject_id"]] == TEST_SUBJECT_ID


class TestLoadCsvWithUuids:
    """Tests for load_csv_with_uuids function."""

    def test_load_saved_csv(self, tmp_path: Path, sample_chapter: Chapter):
        """Should load a previously saved CSV."""
        csv_path = tmp_path / "chapter.csv"
        save_csv(sample_chapter, str(csv_path), position=1, subject_id=TEST_SUBJECT_ID)
        
        data = load_csv_with_uuids(str(csv_path))
        
        assert data["subject_id"] == TEST_SUBJECT_ID
        assert "chapter" in data
        assert "topics" in data
        assert "concepts" in data

    def test_loaded_chapter_has_correct_info(self, tmp_path: Path, sample_chapter: Chapter):
        """Loaded chapter data should match original."""
        csv_path = tmp_path / "chapter.csv"
        save_csv(sample_chapter, str(csv_path), position=1, subject_id=TEST_SUBJECT_ID)
        
        data = load_csv_with_uuids(str(csv_path))
        
        assert data["chapter"]["name"] == "Numbers and Operations"
        assert data["chapter"]["position"] == 1
        assert validate_uuid(data["chapter"]["id"])

    def test_loaded_concepts_count(self, tmp_path: Path, sample_chapter: Chapter):
        """Should load all concepts."""
        csv_path = tmp_path / "chapter.csv"
        save_csv(sample_chapter, str(csv_path), position=1, subject_id=TEST_SUBJECT_ID)
        
        data = load_csv_with_uuids(str(csv_path))
        
        assert len(data["concepts"]) == 3

    def test_file_not_found(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_csv_with_uuids("/nonexistent/path.csv")


class TestGetConceptNamesFromCsv:
    """Tests for get_concept_names_from_csv function."""

    def test_returns_concept_names(self, tmp_path: Path, sample_chapter: Chapter):
        """Should return list of concept names from CSV."""
        csv_path = tmp_path / "chapter.csv"
        save_csv(sample_chapter, str(csv_path), position=1, subject_id=TEST_SUBJECT_ID)
        
        names = get_concept_names_from_csv(str(csv_path))
        
        assert len(names) == 3
        assert "Counting from 1 to 100" in names
        assert "Number Comparison" in names
        assert "Single Digit Addition" in names
