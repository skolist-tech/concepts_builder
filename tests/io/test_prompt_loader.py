"""I/O tests for prompt loading using tmp_path fixture."""

import pytest
from pathlib import Path

from utils.prompt_loader import load_prompt


class TestLoadPrompt:
    """Tests for load_prompt function."""

    def test_load_valid_prompt(self, tmp_path: Path):
        """Should load prompt content from a valid file."""
        prompt_file = tmp_path / "test_prompt.txt"
        prompt_file.write_text("Extract concepts from the PDF.", encoding="utf-8")
        
        result = load_prompt(str(prompt_file))
        
        assert result == "Extract concepts from the PDF."

    def test_load_prompt_strips_whitespace(self, tmp_path: Path):
        """Should strip leading/trailing whitespace from prompt."""
        prompt_file = tmp_path / "test_prompt.txt"
        prompt_file.write_text("  \n  Extract concepts.  \n  ", encoding="utf-8")
        
        result = load_prompt(str(prompt_file))
        
        assert result == "Extract concepts."

    def test_load_multiline_prompt(self, tmp_path: Path):
        """Should preserve internal newlines in prompt."""
        prompt_file = tmp_path / "test_prompt.txt"
        content = "Line 1\nLine 2\nLine 3"
        prompt_file.write_text(content, encoding="utf-8")
        
        result = load_prompt(str(prompt_file))
        
        assert result == content

    def test_file_not_found_raises_error(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="Prompt file not found"):
            load_prompt("/nonexistent/path/prompt.txt")

    def test_empty_file_raises_error(self, tmp_path: Path):
        """Should raise ValueError for empty file."""
        prompt_file = tmp_path / "empty.txt"
        prompt_file.write_text("", encoding="utf-8")
        
        with pytest.raises(ValueError, match="Empty prompt file"):
            load_prompt(str(prompt_file))

    def test_whitespace_only_file_raises_error(self, tmp_path: Path):
        """Should raise ValueError for whitespace-only file."""
        prompt_file = tmp_path / "whitespace.txt"
        prompt_file.write_text("   \n\t\n   ", encoding="utf-8")
        
        with pytest.raises(ValueError, match="Empty prompt file"):
            load_prompt(str(prompt_file))

    def test_unicode_content(self, tmp_path: Path):
        """Should handle unicode content correctly."""
        prompt_file = tmp_path / "unicode.txt"
        content = "Extraire les concepts mathématiques 数学 🔢"
        prompt_file.write_text(content, encoding="utf-8")
        
        result = load_prompt(str(prompt_file))
        
        assert result == content

    def test_load_from_subdirectory(self, tmp_path: Path):
        """Should handle loading from nested directories."""
        subdir = tmp_path / "prompts" / "math"
        subdir.mkdir(parents=True)
        prompt_file = subdir / "concepts.txt"
        prompt_file.write_text("Math concepts prompt", encoding="utf-8")
        
        result = load_prompt(str(prompt_file))
        
        assert result == "Math concepts prompt"
