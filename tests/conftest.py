"""Shared pytest fixtures for all tests."""

import pytest
from pathlib import Path


@pytest.fixture
def sample_subject_id() -> str:
    """A consistent subject ID for testing."""
    return "test-subject-uuid-123"


@pytest.fixture
def sample_chapter_name() -> str:
    """A sample chapter name for testing."""
    return "Chapter 1: Introduction to Numbers"


@pytest.fixture
def sample_topic_name() -> str:
    """A sample topic name for testing."""
    return "Natural Numbers"


@pytest.fixture
def sample_concept_name() -> str:
    """A sample concept name for testing."""
    return "Counting Numbers from 1 to 100"


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"
