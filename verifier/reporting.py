"""
Reporting and output formatting utilities for the verifier package.

This module provides functions for printing summary tables and creating
statistics dictionaries for verification results.
"""

import logging
from collections import defaultdict
from typing import Dict

logger = logging.getLogger(__name__)


def create_chapter_stats() -> Dict[str, int]:
    """
    Create a default statistics dictionary for tracking chapter-level verification results.
    
    Returns a dictionary with all statistical counters initialized to zero.
    This is used to track various types of issues and suggestions per chapter.
    
    Returns:
        Dictionary with the following keys, all initialized to 0:
            - 'mismatches': Total concept issues found
            - 'missing': Concepts not found in CSV
            - 'suggestions_valid': AI suggestions that exist in CSV
            - 'suggestions_invalid': AI suggestions that don't exist in CSV
            - 'suggestions_none': Cases where AI couldn't suggest a replacement
            - 'suggestions_failed': Cases where AI API call failed
            - 'concepts_resolved': Unique concepts that were fixed
            - 'questions_updated': Total questions updated with corrections
            - 'apply_failed': Cases where applying fix failed
            
    Example:
        >>> stats = create_chapter_stats()
        >>> stats['mismatches'] = 5
        >>> stats['missing'] = 3
    """
    return {
        "mismatches": 0,
        "missing": 0,
        "suggestions_valid": 0,
        "suggestions_invalid": 0,
        "suggestions_none": 0,
        "suggestions_failed": 0,
        "concepts_resolved": 0,
        "questions_updated": 0,
        "apply_failed": 0,
    }


def create_chapter_stats_dict() -> Dict[str, Dict[str, int]]:
    """
    Create a defaultdict that auto-creates chapter stats for new keys.
    
    Returns:
        A defaultdict that returns a new chapter stats dict for any new key.
        
    Example:
        >>> chapter_stats = create_chapter_stats_dict()
        >>> chapter_stats["chapter_01"]["mismatches"] += 1
    """
    return defaultdict(create_chapter_stats)


def print_summary_table(
    chapter_stats: Dict[str, Dict[str, int]], 
    suggest: bool, 
    apply_suggestions: bool
) -> None:
    """
    Print a formatted summary table of concept mapping statistics per chapter.
    
    Generates a table showing verification statistics for each chapter, with
    columns that vary based on which modes are enabled. The table includes
    totals and a legend explaining each column.
    
    Args:
        chapter_stats: Dictionary mapping chapter prefix to statistics dict.
                      Each stats dict should have keys as defined by create_chapter_stats().
        suggest: Whether AI suggestions mode was enabled.
        apply_suggestions: Whether apply suggestions mode was enabled.
        
    Note:
        Output is sent to the logger at INFO level for normal output
        and WARNING level for totals.
        
    Example:
        >>> stats = {"ch01": {"mismatches": 5, "missing": 2, ...}, ...}
        >>> print_summary_table(stats, suggest=True, apply_suggestions=False)
        ======================================================================
        CONCEPT MAPPING SUMMARY
        ======================================================================
        Chapter                                  Mismatches    Missing    Valid ...
        ...
    """
    logger.info("")
    logger.info("=" * 100)
    logger.info("CONCEPT MAPPING SUMMARY")
    logger.info("=" * 100)
    
    # Determine which columns to show based on modes
    if apply_suggestions:
        # Full table with all columns
        header = f"{'Chapter':<40} {'Mismatches':>10} {'Missing':>8} {'Valid':>7} {'Invalid':>8} {'None':>6} {'Resolved':>9} {'Questions':>10}"
        separator = "-" * 105
    elif suggest:
        # Table without apply columns
        header = f"{'Chapter':<45} {'Mismatches':>12} {'Missing':>10} {'Valid':>10} {'Invalid':>10} {'No Match':>10}"
        separator = "-" * 100
    else:
        # Simple table without suggestion columns
        header = f"{'Chapter':<60} {'Mismatches':>15} {'Missing':>15}"
        separator = "-" * 95
    
    logger.info(header)
    logger.info(separator)
    
    # Totals
    total_mismatches = 0
    total_missing = 0
    total_valid = 0
    total_invalid = 0
    total_none = 0
    total_failed = 0
    total_concepts_resolved = 0
    total_questions_updated = 0
    total_apply_failed = 0
    
    for prefix in sorted(chapter_stats.keys()):
        stats = chapter_stats[prefix]
        
        mismatches = stats["mismatches"]
        missing = stats["missing"]
        valid = stats["suggestions_valid"]
        invalid = stats["suggestions_invalid"]
        none_match = stats["suggestions_none"]
        failed = stats["suggestions_failed"]
        concepts_resolved = stats["concepts_resolved"]
        questions_updated = stats["questions_updated"]
        apply_failed = stats["apply_failed"]
        
        total_mismatches += mismatches
        total_missing += missing
        total_valid += valid
        total_invalid += invalid
        total_none += none_match
        total_failed += failed
        total_concepts_resolved += concepts_resolved
        total_questions_updated += questions_updated
        total_apply_failed += apply_failed
        
        # Truncate long chapter names
        display_prefix = prefix[:38] + ".." if len(prefix) > 40 else prefix
        
        if apply_suggestions:
            row = f"{display_prefix:<40} {mismatches:>10} {missing:>8} {valid:>7} {invalid:>8} {none_match:>6} {concepts_resolved:>9} {questions_updated:>10}"
        elif suggest:
            display_prefix = prefix[:43] + ".." if len(prefix) > 45 else prefix
            row = f"{display_prefix:<45} {mismatches:>12} {missing:>10} {valid:>10} {invalid:>10} {none_match:>10}"
        else:
            display_prefix = prefix[:58] + ".." if len(prefix) > 60 else prefix
            row = f"{display_prefix:<60} {mismatches:>15} {missing:>15}"
        
        logger.info(row)
    
    # Print totals row
    logger.info(separator)
    
    if apply_suggestions:
        totals_row = f"{'TOTAL':<40} {total_mismatches:>10} {total_missing:>8} {total_valid:>7} {total_invalid:>8} {total_none:>6} {total_concepts_resolved:>9} {total_questions_updated:>10}"
    elif suggest:
        totals_row = f"{'TOTAL':<45} {total_mismatches:>12} {total_missing:>10} {total_valid:>10} {total_invalid:>10} {total_none:>10}"
    else:
        totals_row = f"{'TOTAL':<60} {total_mismatches:>15} {total_missing:>15}"
    
    logger.info(totals_row)
    logger.info("=" * 100)
    
    # Print legend
    logger.info("")
    logger.info("Legend:")
    logger.info("  Mismatches  - Total concept issues (whitespace, case, unicode, missing)")
    logger.info("  Missing     - Concepts not found in CSV (candidates for AI suggestion)")
    if suggest:
        logger.info("  Valid       - AI suggestions that exist in CSV")
        logger.info("  Invalid     - AI suggestions that don't exist in CSV")
        logger.info("  None/No Match - AI could not suggest a replacement")
    if apply_suggestions:
        logger.info("  Resolved    - Unique missing concepts that were fixed")
        logger.info("  Questions   - Total questions updated with corrected concepts")
    logger.info("")
