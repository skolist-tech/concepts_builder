"""Tests for add_uuids_to_existing utility."""

import pytest
import csv
import json
from pathlib import Path

from utils.add_uuids_to_existing import (
    add_uuids_to_concepts_csv,
    add_uuids_to_exercise_json,
    add_uuids_to_solved_json,
    add_uuids_to_directory
)
from utils.uuid_generator import validate_uuid


TEST_SUBJECT_ID = "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_concepts_csv(tmp_path: Path) -> Path:
    """Create a sample concepts CSV without UUIDs."""
    csv_path = tmp_path / "concepts.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "concept_name", "concept_description", "concept_page_number",
            "topic_name", "topic_description", "topic_position",
            "chapter_name", "chapter_description", "chapter_position"
        ])
        writer.writerow([
            "Counting", "Learn to count", "5",
            "Natural Numbers", "Numbers for counting", "1",
            "Numbers", "Introduction to numbers", "1"
        ])
        writer.writerow([
            "Comparison", "Compare numbers", "7",
            "Natural Numbers", "Numbers for counting", "1",
            "Numbers", "Introduction to numbers", "1"
        ])
        writer.writerow([
            "Addition", "Add numbers", "10",
            "Operations", "Basic math operations", "2",
            "Numbers", "Introduction to numbers", "1"
        ])
    return csv_path


@pytest.fixture
def sample_exercise_json(tmp_path: Path) -> Path:
    """Create a sample exercise questions JSON without UUIDs."""
    json_path = tmp_path / "chapter_exercise_questions.json"
    data = {
        "chapter_name": "Numbers",
        "exercise_questions": [
            {
                "question_text": "What is 2+2?",
                "explanation": "Simple addition",
                "answer_text": "4",
                "question_type": "Short Answer"
            },
            {
                "question_text": "Which is larger: 5 or 3?",
                "explanation": "Number comparison",
                "option1": "5",
                "option2": "3",
                "correct_mcq_option": 1,
                "question_type": "MCQ4"
            }
        ]
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return json_path


@pytest.fixture
def sample_solved_json(tmp_path: Path) -> Path:
    """Create a sample solved examples JSON without UUIDs."""
    json_path = tmp_path / "chapter_solved_examples.json"
    data = {
        "chapter_name": "Numbers",
        "solved_examples_questions": [
            {
                "question_text": "Example: Find 5+3",
                "explanation": "Step by step: 5+3=8",
                "answer_text": "8",
                "question_type": "Short Answer"
            }
        ]
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return json_path


class TestAddUuidsToCsv:
    """Tests for add_uuids_to_concepts_csv function."""

    def test_adds_uuid_columns(self, sample_concepts_csv, tmp_path):
        """Should add all UUID columns to output CSV."""
        output_path = tmp_path / "output.csv"
        
        add_uuids_to_concepts_csv(str(sample_concepts_csv), str(output_path), TEST_SUBJECT_ID)
        
        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
        
        assert "concept_id" in headers
        assert "topic_id" in headers
        assert "chapter_id" in headers
        assert "subject_id" in headers

    def test_generates_valid_uuids(self, sample_concepts_csv, tmp_path):
        """All generated UUIDs should be valid."""
        output_path = tmp_path / "output.csv"
        
        add_uuids_to_concepts_csv(str(sample_concepts_csv), str(output_path), TEST_SUBJECT_ID)
        
        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert validate_uuid(row["concept_id"])
                assert validate_uuid(row["topic_id"])
                assert validate_uuid(row["chapter_id"])
                assert row["subject_id"] == TEST_SUBJECT_ID

    def test_preserves_original_data(self, sample_concepts_csv, tmp_path):
        """Original data should be preserved."""
        output_path = tmp_path / "output.csv"
        
        add_uuids_to_concepts_csv(str(sample_concepts_csv), str(output_path), TEST_SUBJECT_ID)
        
        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 3
        assert rows[0]["concept_name"] == "Counting"
        assert rows[0]["chapter_name"] == "Numbers"

    def test_same_topic_gets_same_uuid(self, sample_concepts_csv, tmp_path):
        """Concepts in the same topic should have the same topic_id."""
        output_path = tmp_path / "output.csv"
        
        add_uuids_to_concepts_csv(str(sample_concepts_csv), str(output_path), TEST_SUBJECT_ID)
        
        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # First two rows are in "Natural Numbers" topic
        assert rows[0]["topic_id"] == rows[1]["topic_id"]
        # Third row is in "Operations" topic
        assert rows[0]["topic_id"] != rows[2]["topic_id"]

    def test_returns_statistics(self, sample_concepts_csv, tmp_path):
        """Should return correct statistics."""
        output_path = tmp_path / "output.csv"
        
        stats = add_uuids_to_concepts_csv(str(sample_concepts_csv), str(output_path), TEST_SUBJECT_ID)
        
        assert stats["concepts"] == 3
        assert stats["topics"] == 2
        assert stats["chapters"] == 1

    def test_file_not_found(self, tmp_path):
        """Should raise FileNotFoundError for missing input."""
        with pytest.raises(FileNotFoundError):
            add_uuids_to_concepts_csv(
                str(tmp_path / "nonexistent.csv"),
                str(tmp_path / "output.csv"),
                TEST_SUBJECT_ID
            )

    def test_creates_output_directory(self, sample_concepts_csv, tmp_path):
        """Should create output directory if it doesn't exist."""
        output_path = tmp_path / "a" / "b" / "output.csv"
        
        add_uuids_to_concepts_csv(str(sample_concepts_csv), str(output_path), TEST_SUBJECT_ID)
        
        assert output_path.exists()


class TestAddUuidsToExerciseJson:
    """Tests for add_uuids_to_exercise_json function."""

    def test_adds_top_level_ids(self, sample_exercise_json, tmp_path):
        """Should add chapter_id and subject_id at top level."""
        output_path = tmp_path / "output.json"
        
        add_uuids_to_exercise_json(str(sample_exercise_json), str(output_path), TEST_SUBJECT_ID)
        
        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)
        
        assert "chapter_id" in data
        assert validate_uuid(data["chapter_id"])
        assert data["subject_id"] == TEST_SUBJECT_ID

    def test_adds_question_ids(self, sample_exercise_json, tmp_path):
        """Should add id to each question."""
        output_path = tmp_path / "output.json"
        
        add_uuids_to_exercise_json(str(sample_exercise_json), str(output_path), TEST_SUBJECT_ID)
        
        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)
        
        for question in data["exercise_questions"]:
            assert "id" in question
            assert validate_uuid(question["id"])

    def test_preserves_original_data(self, sample_exercise_json, tmp_path):
        """Original question data should be preserved."""
        output_path = tmp_path / "output.json"
        
        add_uuids_to_exercise_json(str(sample_exercise_json), str(output_path), TEST_SUBJECT_ID)
        
        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["chapter_name"] == "Numbers"
        assert len(data["exercise_questions"]) == 2
        assert data["exercise_questions"][0]["question_text"] == "What is 2+2?"

    def test_ids_are_deterministic(self, sample_exercise_json, tmp_path):
        """Same input should produce same UUIDs."""
        output1 = tmp_path / "output1.json"
        output2 = tmp_path / "output2.json"
        
        add_uuids_to_exercise_json(str(sample_exercise_json), str(output1), TEST_SUBJECT_ID)
        add_uuids_to_exercise_json(str(sample_exercise_json), str(output2), TEST_SUBJECT_ID)
        
        with open(output1, encoding="utf-8") as f:
            data1 = json.load(f)
        with open(output2, encoding="utf-8") as f:
            data2 = json.load(f)
        
        assert data1["chapter_id"] == data2["chapter_id"]
        for q1, q2 in zip(data1["exercise_questions"], data2["exercise_questions"]):
            assert q1["id"] == q2["id"]


class TestAddUuidsToSolvedJson:
    """Tests for add_uuids_to_solved_json function."""

    def test_adds_top_level_ids(self, sample_solved_json, tmp_path):
        """Should add chapter_id and subject_id at top level."""
        output_path = tmp_path / "output.json"
        
        add_uuids_to_solved_json(str(sample_solved_json), str(output_path), TEST_SUBJECT_ID)
        
        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)
        
        assert validate_uuid(data["chapter_id"])
        assert data["subject_id"] == TEST_SUBJECT_ID

    def test_adds_question_ids(self, sample_solved_json, tmp_path):
        """Should add id to each solved example."""
        output_path = tmp_path / "output.json"
        
        add_uuids_to_solved_json(str(sample_solved_json), str(output_path), TEST_SUBJECT_ID)
        
        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)
        
        for question in data["solved_examples_questions"]:
            assert "id" in question
            assert validate_uuid(question["id"])


class TestAddUuidsToDirectory:
    """Tests for add_uuids_to_directory function."""

    def test_processes_all_file_types(self, tmp_path):
        """Should process CSVs and JSONs matching the patterns."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        
        # Create sample files
        csv_path = input_dir / "ch1_concepts.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "concept_name", "concept_description", "concept_page_number",
                "topic_name", "topic_description", "topic_position",
                "chapter_name", "chapter_description", "chapter_position"
            ])
            writer.writerow(["Test", "Desc", "1", "Topic", "Desc", "1", "Chapter", "Desc", "1"])
        
        exercise_path = input_dir / "ch1_exercise_questions.json"
        with open(exercise_path, "w", encoding="utf-8") as f:
            json.dump({"chapter_name": "Ch1", "exercise_questions": [{"question_text": "Q1", "explanation": "E1"}]}, f)
        
        solved_path = input_dir / "ch1_solved_examples.json"
        with open(solved_path, "w", encoding="utf-8") as f:
            json.dump({"chapter_name": "Ch1", "solved_examples_questions": [{"question_text": "S1", "explanation": "E1"}]}, f)
        
        stats = add_uuids_to_directory(str(input_dir), str(output_dir), TEST_SUBJECT_ID)
        
        assert stats["concepts_csvs"] == 1
        assert stats["exercise_jsons"] == 1
        assert stats["solved_jsons"] == 1
        assert (output_dir / "ch1_concepts.csv").exists()
        assert (output_dir / "ch1_exercise_questions.json").exists()
        assert (output_dir / "ch1_solved_examples.json").exists()
