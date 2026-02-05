"""
Prompts package for concepts_builder.

Contains prompt templates for different textbook formats.
Each book format may require specific prompts for:
- Concept extraction
- Solved examples extraction
- Exercise questions extraction
"""

from prompts.class10_maths import NCERT_GEN

__all__ = [
    "NCERT_GEN",
]
