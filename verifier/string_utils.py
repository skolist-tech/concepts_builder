"""
String and concept matching utilities for the verifier package.

This module provides functions for normalizing concept names and finding
similar concepts using string matching algorithms.
"""

import unicodedata
from typing import List, Set


def normalize_concept(s: str) -> str:
    """
    Normalize a concept name by handling unicode and whitespace.
    
    Performs the following normalizations:
    1. Unicode NFKC normalization (converts various unicode chars to canonical form)
    2. Replaces all whitespace characters with regular spaces
    3. Strips leading/trailing whitespace
    4. Collapses multiple consecutive spaces into single spaces
    
    Args:
        s: The concept string to normalize.
        
    Returns:
        The normalized concept string.
        
    Example:
        >>> normalize_concept("  Rational  Numbers  ")
        'Rational Numbers'
        >>> normalize_concept("Numbers\\u00a0and\\u2003Operations")  # non-breaking space, em space
        'Numbers and Operations'
    """
    # Normalize unicode (NFKC converts various unicode chars to their canonical form)
    s = unicodedata.normalize('NFKC', s)
    # Replace various whitespace characters with regular space
    s = ''.join(' ' if c.isspace() else c for c in s)
    # Strip and collapse multiple spaces
    return ' '.join(s.split())


def is_subsequence(shorter: str, longer: str) -> bool:
    """
    Check if 'shorter' is a subsequence of 'longer' (case-insensitive).
    
    A subsequence means characters appear in order but don't need to be contiguous.
    This is useful for fuzzy matching where one string might be an abbreviated
    or partial version of another.
    
    Args:
        shorter: The potential subsequence string.
        longer: The string to check against.
        
    Returns:
        True if shorter is a subsequence of longer, False otherwise.
        
    Example:
        >>> is_subsequence("ace", "abcde")
        True
        >>> is_subsequence("aec", "abcde")
        False
        >>> is_subsequence("NUM", "Numbers")
        True
    """
    shorter = shorter.lower()
    longer = longer.lower()
    
    it = iter(longer)
    return all(char in it for char in shorter)


def find_similar_concepts(
    missing_concept: str, 
    available_concepts: Set[str], 
    max_suggestions: int = 3
) -> List[str]:
    """
    Find available concepts where one is a subsequence of the other.
    
    Uses the subsequence algorithm to find concepts that might be similar
    to the missing concept. This helps suggest corrections for typos or
    minor variations in concept names.
    
    Args:
        missing_concept: The concept that was not found in the available set.
        available_concepts: Set of valid concept names from the CSV.
        max_suggestions: Maximum number of suggestions to return (default: 3).
        
    Returns:
        List of similar concept names, sorted alphabetically and limited
        to max_suggestions items.
        
    Example:
        >>> available = {"Rational Numbers", "Irrational Numbers", "Real Numbers"}
        >>> find_similar_concepts("Ratinal Numbers", available)
        ['Rational Numbers']
        >>> find_similar_concepts("Numbers", available)
        ['Irrational Numbers', 'Rational Numbers', 'Real Numbers']
    """
    suggestions = []
    
    for available in available_concepts:
        # Check if missing concept is subsequence of available, or vice versa
        if is_subsequence(missing_concept, available) or is_subsequence(available, missing_concept):
            suggestions.append(available)
    
    return sorted(suggestions)[:max_suggestions]
