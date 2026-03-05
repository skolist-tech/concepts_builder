"""
Verifier package for concepts_builder.

Validates consistency between concept CSVs and their corresponding JSON files
for exercise questions and solved examples.

Three independent verification checks:
1. Chapter consistency: Verify chapter_name and chapter_id match between CSVs and JSONs
2. Concept consistency: Verify concepts in questions exist in concept CSVs
3. File conventions: Verify file naming conventions and position consistency

Example usage:
    from verifier import check_chapter_consistency, check_concept_consistency, check_conventions
    from verifier import get_file_groups
    
    groups = get_file_groups(input_dir)
    passed, failed, failures = check_chapter_consistency(groups)
"""

from verifier.loaders import (
    get_file_groups,
    load_csv_chapter_info,
    load_json_info,
    load_json_questions_with_concepts,
    apply_concept_replacement,
)
from verifier.string_utils import (
    normalize_concept,
    is_subsequence,
    find_similar_concepts,
)
from verifier.suggestions import get_gemini_concept_suggestion
from verifier.reporting import print_summary_table, create_chapter_stats
from verifier.checkers import (
    check_chapter_consistency,
    check_concept_consistency,
    check_conventions,
)
from verifier.cli import main

__all__ = [
    # Loaders
    "get_file_groups",
    "load_csv_chapter_info",
    "load_json_info",
    "load_json_questions_with_concepts",
    "apply_concept_replacement",
    # String utilities
    "normalize_concept",
    "is_subsequence",
    "find_similar_concepts",
    # AI suggestions
    "get_gemini_concept_suggestion",
    # Reporting
    "print_summary_table",
    "create_chapter_stats",
    # Checkers
    "check_chapter_consistency",
    "check_concept_consistency",
    "check_conventions",
    # CLI
    "main",
]
