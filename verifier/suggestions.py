"""
AI-powered concept suggestion utilities for the verifier package.

This module provides functions that use Gemini AI to suggest correct
concept mappings when a question references a concept not found in the CSV.
"""

import logging
from typing import Dict, List, Optional

from agents.base import get_gemini_client
from config import settings
from google.genai import types

logger = logging.getLogger(__name__)


async def get_gemini_concept_suggestion(
    question_text: str,
    current_concepts: List[str],
    available_concepts_with_desc: Dict[str, str],
    missing_concept: str,
) -> Optional[str]:
    """
    Use Gemini to suggest the correct concept mapping for a question.
    
    When a question references a concept that doesn't exist in the available
    concept list, this function uses AI to analyze the question and suggest
    the most appropriate replacement from the available concepts.
    
    Args:
        question_text: The full text of the question.
        current_concepts: List of concepts currently associated with the question
                         (may include the incorrect one).
        available_concepts_with_desc: Dictionary mapping concept names to their
                                     descriptions from the CSV file.
        missing_concept: The concept name that was not found in the CSV.
        
    Returns:
        The suggested replacement concept name if one is found, "NONE" if no
        suitable concept exists, or None if the API call fails.
        
    Note:
        The function uses a low temperature (0.1) to ensure consistent,
        deterministic suggestions.
        
    Example:
        >>> suggestion = await get_gemini_concept_suggestion(
        ...     question_text="What is 2/3 + 1/4?",
        ...     current_concepts=["Fractions Addition"],  # not in CSV
        ...     available_concepts_with_desc={
        ...         "Addition of Fractions": "Adding two or more fractions",
        ...         "Subtraction of Fractions": "Subtracting fractions"
        ...     },
        ...     missing_concept="Fractions Addition"
        ... )
        >>> suggestion
        'Addition of Fractions'
    """
    try:
        client = get_gemini_client()
        
        # Build the available concepts list for prompt
        concepts_list = "\n".join(
            f"- {name}: {desc}" if desc else f"- {name}"
            for name, desc in sorted(available_concepts_with_desc.items())
        )
        
        prompt = f"""You are helping to fix concept mappings for educational questions.

A question has been mapped to the concept "{missing_concept}", but this concept does not exist in the available concept list.

QUESTION:
{question_text}

CURRENT CONCEPT MAPPING (may be incorrect):
{', '.join(current_concepts) if current_concepts else 'None'}

AVAILABLE CONCEPTS FROM THIS CHAPTER (format: "concept_name: description"):
{concepts_list}

TASK: Suggest the best matching concept from the AVAILABLE CONCEPTS list that this question should be mapped to instead of "{missing_concept}".

CRITICAL RULES:
1. Output ONLY the concept NAME, NOT the description
2. If no concept fits, respond with exactly "NONE"
4. Do NOT include any explanation, colon, or description text
5. Match the concept name EXACTLY as it appears before the colon in the list above

Example good response: "Rational Numbers"
Example good response: "Square Roots"
Example bad response: "Rational Numbers: Definition as numbers expressible in p/q form..."

Your response (concept name only):"""

        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.1,
            ),
        )
        
        suggestion = response.text.strip() if response.text else None
        return suggestion
        
    except Exception as e:
        logger.warning(f"Gemini suggestion failed: {e}")
        return None
