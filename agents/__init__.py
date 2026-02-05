"""
Agents package for concepts_builder.

Contains AI-powered generators that use Gemini to extract structured data from PDFs.
"""

from agents.base import GeminiClient, get_gemini_client, read_pdf_as_part, format_concepts_list
from agents.concept_generator import generate_concepts
from agents.solved_examples_generator import generate_solved_examples
from agents.exercise_questions_generator import generate_exercise_questions

__all__ = [
    # Base utilities
    "GeminiClient",
    "get_gemini_client",
    "read_pdf_as_part",
    "format_concepts_list",
    # Generators
    "generate_concepts",
    "generate_solved_examples",
    "generate_exercise_questions",
]