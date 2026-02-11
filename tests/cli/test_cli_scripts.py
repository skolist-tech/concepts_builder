"""Tests for CLI scripts - argument parsing and main functions."""

import pytest
import subprocess
import sys
from pathlib import Path


class TestConceptsBuilderCli:
    """Tests for concepts_builder.py CLI."""

    def test_help_flag(self):
        """Should display help without error."""
        result = subprocess.run(
            [sys.executable, "concepts_builder.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Extract concepts from chapter PDFs" in result.stdout
        assert "--input_dir" in result.stdout
        assert "--output_dir" in result.stdout
        assert "--subject_id" in result.stdout
        assert "--prompt_file_path" in result.stdout

    def test_missing_required_args(self):
        """Should fail with missing required arguments."""
        result = subprocess.run(
            [sys.executable, "concepts_builder.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        assert "required" in result.stderr.lower()

    def test_invalid_uuid_rejected(self, tmp_path):
        """Should reject invalid subject_id UUID."""
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text("Extract concepts")
        
        result = subprocess.run(
            [
                sys.executable, "concepts_builder.py",
                "--input_dir", str(tmp_path),
                "--output_dir", str(tmp_path / "output"),
                "--subject_id", "not-a-valid-uuid",
                "--prompt_file_path", str(prompt_file)
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        assert "Invalid" in result.stderr or "uuid" in result.stderr.lower()


class TestExerciseQuestionsBuilderCli:
    """Tests for exercise_questions_builder.py CLI."""

    def test_help_flag(self):
        """Should display help without error."""
        result = subprocess.run(
            [sys.executable, "exercise_questions_builder.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--input_dir" in result.stdout
        assert "--output_dir" in result.stdout
        assert "--subject_id" in result.stdout

    def test_missing_required_args(self):
        """Should fail with missing required arguments."""
        result = subprocess.run(
            [sys.executable, "exercise_questions_builder.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0


class TestSolvedExamplesBuilderCli:
    """Tests for solved_examples_builder.py CLI."""

    def test_help_flag(self):
        """Should display help without error."""
        result = subprocess.run(
            [sys.executable, "solved_examples_builder.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--input_dir" in result.stdout
        assert "--output_dir" in result.stdout
        assert "--subject_id" in result.stdout

    def test_missing_required_args(self):
        """Should fail with missing required arguments."""
        result = subprocess.run(
            [sys.executable, "solved_examples_builder.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0


class TestConceptsUploaderCli:
    """Tests for concepts_uploader.py CLI."""

    def test_help_flag(self):
        """Should display help without error."""
        result = subprocess.run(
            [sys.executable, "concepts_uploader.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--input_dir" in result.stdout

    def test_missing_required_args(self):
        """Should fail with missing required arguments."""
        result = subprocess.run(
            [sys.executable, "concepts_uploader.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0


class TestExerciseQuestionsUploaderCli:
    """Tests for exercise_questions_uploader.py CLI."""

    def test_help_flag(self):
        """Should display help without error."""
        result = subprocess.run(
            [sys.executable, "exercise_questions_uploader.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--input_dir" in result.stdout

    def test_missing_required_args(self):
        """Should fail with missing required arguments."""
        result = subprocess.run(
            [sys.executable, "exercise_questions_uploader.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0


class TestSolvedExamplesUploaderCli:
    """Tests for solved_examples_uploader.py CLI."""

    def test_help_flag(self):
        """Should display help without error."""
        result = subprocess.run(
            [sys.executable, "solved_examples_uploader.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--input_dir" in result.stdout

    def test_missing_required_args(self):
        """Should fail with missing required arguments."""
        result = subprocess.run(
            [sys.executable, "solved_examples_uploader.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
