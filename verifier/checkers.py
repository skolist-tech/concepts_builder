"""
Verification check functions for the verifier package.

This module provides the three main verification checks:
1. Chapter consistency check
2. Concept consistency check (with optional AI suggestions)
3. File naming conventions check
"""

import asyncio
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from config import settings
from verifier.loaders import (
    apply_concept_replacement,
    load_csv_chapter_info,
    load_json_info,
    load_json_questions_with_concepts,
)
from verifier.reporting import create_chapter_stats_dict, print_summary_table
from verifier.string_utils import find_similar_concepts, normalize_concept
from verifier.suggestions import get_gemini_concept_suggestion

logger = logging.getLogger(__name__)


def check_chapter_consistency(groups: List[Dict[str, Any]]) -> Tuple[int, int, List[Dict]]:
    """
    Check chapter_name and chapter_id consistency between CSV and JSONs.
    
    Verifies that the chapter metadata (name and ID) in concept CSVs matches
    the metadata in corresponding exercise and solved examples JSON files.
    Also checks for internal consistency within each CSV file.
    
    Args:
        groups: List of file groups from get_file_groups(). Each group dict
               should have keys: 'prefix', 'concepts_csv', 'exercise_json', 'solved_json'.
               
    Returns:
        Tuple of (passed_count, failed_count, failures_list) where:
            - passed_count: Number of chapters that passed all checks
            - failed_count: Number of chapters with issues
            - failures_list: List of dicts with 'prefix' and 'issues' for failed chapters
            
    Example:
        >>> groups = get_file_groups(Path("data/output"))
        >>> passed, failed, failures = check_chapter_consistency(groups)
        >>> print(f"{passed} passed, {failed} failed")
    """
    passed = 0
    failed = 0
    failures = []
    
    logger.info("=" * 70)
    logger.info("CHAPTER CONSISTENCY CHECK")
    logger.info("=" * 70)
    
    for idx, group in enumerate(groups, 1):
        prefix = group["prefix"]
        csv_path = group["concepts_csv"]
        exercise_path = group["exercise_json"]
        solved_path = group["solved_json"]
        
        csv_info = load_csv_chapter_info(csv_path)
        chapter_name_csv = csv_info["chapter_name"]
        chapter_id_csv = csv_info["chapter_id"]
        internal_issues = csv_info.get("internal_inconsistencies", [])
        
        group_passed = True
        group_issues = []
        
        # Check internal CSV consistency first
        if internal_issues:
            group_passed = False
            # Only show first 3 inconsistencies to avoid spam
            for issue in internal_issues[:3]:
                group_issues.append(f"CSV internal: {issue}")
            if len(internal_issues) > 3:
                group_issues.append(f"CSV internal: ... and {len(internal_issues) - 3} more inconsistencies")
        
        # Check exercise JSON
        if exercise_path:
            exercise_info = load_json_info(exercise_path, "exercise_questions")
            
            if chapter_name_csv != exercise_info["chapter_name"]:
                group_passed = False
                group_issues.append(
                    f"Exercise JSON chapter_name mismatch: "
                    f"CSV='{chapter_name_csv}' vs JSON='{exercise_info['chapter_name']}'"
                )
            
            if chapter_id_csv and exercise_info["chapter_id"]:
                if chapter_id_csv != exercise_info["chapter_id"]:
                    group_passed = False
                    group_issues.append(
                        f"Exercise JSON chapter_id mismatch: "
                        f"CSV='{chapter_id_csv}' vs JSON='{exercise_info['chapter_id']}'"
                    )
        
        # Check solved examples JSON
        if solved_path:
            solved_info = load_json_info(solved_path, "solved_examples_questions")
            
            if chapter_name_csv != solved_info["chapter_name"]:
                group_passed = False
                group_issues.append(
                    f"Solved JSON chapter_name mismatch: "
                    f"CSV='{chapter_name_csv}' vs JSON='{solved_info['chapter_name']}'"
                )
            
            if chapter_id_csv and solved_info["chapter_id"]:
                if chapter_id_csv != solved_info["chapter_id"]:
                    group_passed = False
                    group_issues.append(
                        f"Solved JSON chapter_id mismatch: "
                        f"CSV='{chapter_id_csv}' vs JSON='{solved_info['chapter_id']}'"
                    )
        
        if group_passed:
            passed += 1
            logger.info(f"  {idx:2}. {prefix:<45} [PASS]")
        else:
            failed += 1
            logger.error(f"  {idx:2}. {prefix:<45} [FAIL]")
            for issue in group_issues:
                logger.error(f"      -> {issue}")
            failures.append({
                "prefix": prefix,
                "issues": group_issues,
            })
    
    logger.info("=" * 70)
    if failed > 0:
        logger.error(f"Chapter check: {passed} passed, {failed} failed")
    else:
        logger.info(f"Chapter check: {passed} passed, {failed} failed")
    
    return passed, failed, failures


def _check_concept_against_available(
    concept: str,
    source: str,
    available_concepts: Set[str],
    available_concepts_stripped: Dict[str, str],
    available_concepts_lower: Dict[str, str],
    available_concepts_normalized: Dict[str, str],
    concept_issues: Dict[str, Dict],
) -> None:
    """
    Check a single concept against available concepts and track any issues.
    
    Internal helper function that checks for various types of mismatches
    (exact, whitespace, case, unicode) and records issues in the concept_issues dict.
    
    Args:
        concept: The concept name to check.
        source: Source identifier (e.g., "[Exercise]", "[Solved]").
        available_concepts: Set of exact concept names from CSV.
        available_concepts_stripped: Dict mapping stripped names to originals.
        available_concepts_lower: Dict mapping lowercase names to originals.
        available_concepts_normalized: Dict mapping normalized names to originals.
        concept_issues: Dict to record issues (modified in place).
    """
    if concept in available_concepts:
        return  # Exact match, no issue
    
    concept_stripped = concept.strip()
    concept_lower = concept_stripped.lower()
    concept_normalized = normalize_concept(concept)
    concept_normalized_lower = concept_normalized.lower()
    
    # Check for whitespace mismatch (stripping makes it match)
    if concept_stripped in available_concepts_stripped:
        correct_form = available_concepts_stripped[concept_stripped]
        if concept in concept_issues:
            concept_issues[concept]["source"] = "[Both]"
        else:
            concept_issues[concept] = {
                "source": source,
                "type": "whitespace_mismatch",
                "correct_form": correct_form
            }
    # Check for case mismatch
    elif concept_lower in available_concepts_lower:
        correct_form = available_concepts_lower[concept_lower]
        if concept in concept_issues:
            concept_issues[concept]["source"] = "[Both]"
        else:
            concept_issues[concept] = {
                "source": source,
                "type": "case_mismatch",
                "correct_form": correct_form
            }
    # Check for invisible/unicode character issues (normalized match)
    elif concept_normalized in available_concepts_normalized:
        correct_form = available_concepts_normalized[concept_normalized]
        if concept in concept_issues:
            concept_issues[concept]["source"] = "[Both]"
        else:
            concept_issues[concept] = {
                "source": source,
                "type": "invisible_chars",
                "correct_form": correct_form
            }
    # Check for normalized + case insensitive match
    elif concept_normalized_lower in {normalize_concept(c).lower(): c for c in available_concepts}:
        correct_form = {normalize_concept(c).lower(): c for c in available_concepts}[concept_normalized_lower]
        if concept in concept_issues:
            concept_issues[concept]["source"] = "[Both]"
        else:
            concept_issues[concept] = {
                "source": source,
                "type": "invisible_chars",
                "correct_form": correct_form
            }
    else:
        # Truly missing concept
        if concept in concept_issues:
            concept_issues[concept]["source"] = "[Both]"
        else:
            concept_issues[concept] = {
                "source": source,
                "type": "missing",
                "correct_form": None
            }


def _log_concept_issues(
    concept_issues: Dict[str, Dict],
    available_concepts: Set[str],
    csv_info: Dict[str, Any],
    prefix: str,
    exercise_path: Path,
    solved_path: Path,
    suggest: bool,
    suggestion_tasks: List[Dict],
) -> None:
    """
    Log concept issues and optionally queue AI suggestion tasks.
    
    Internal helper that logs detailed information about each concept issue
    and queues Gemini suggestion tasks for missing concepts when suggest mode is enabled.
    
    Args:
        concept_issues: Dict of concept name to issue details.
        available_concepts: Set of available concept names.
        csv_info: CSV info dict from load_csv_chapter_info().
        prefix: Chapter prefix string.
        exercise_path: Path to exercise JSON (or None).
        solved_path: Path to solved examples JSON (or None).
        suggest: Whether to queue AI suggestion tasks.
        suggestion_tasks: List to append suggestion tasks to (modified in place).
    """
    for concept_name in sorted(concept_issues.keys()):
        issue = concept_issues[concept_name]
        source = issue["source"]
        
        if issue["type"] == "whitespace_mismatch":
            correct_form = issue["correct_form"]
            logger.error(f"      -> {source} WHITESPACE: '{concept_name}' (has extra spaces) should be '{correct_form}'")
        elif issue["type"] == "case_mismatch":
            correct_form = issue["correct_form"]
            logger.error(f"      -> {source} CASE MISMATCH: '{concept_name}' should be '{correct_form}'")
        elif issue["type"] == "invisible_chars":
            correct_form = issue["correct_form"]
            logger.error(f"      -> {source} UNICODE/INVISIBLE CHARS: '{concept_name}' should be '{correct_form}'")
            logger.error(f"         DEBUG: JSON repr={repr(concept_name)}, CSV repr={repr(correct_form)}")
        else:
            logger.error(f"      -> {source} MISSING: '{concept_name}'")
            # Find and show substring-based suggestions
            suggestions = find_similar_concepts(concept_name, available_concepts)
            if suggestions:
                logger.info(f"         Substring suggestions: {', '.join(suggestions)}")
                # Debug: if any suggestion looks visually identical, show repr
                for sug in suggestions:
                    if sug == concept_name or sug.strip() == concept_name.strip():
                        logger.error(f"         DEBUG: Visually similar! JSON repr={repr(concept_name)}, CSV repr={repr(sug)}")
            
            # If suggest mode enabled, collect tasks for AI-based suggestions
            if suggest:
                concepts_with_desc = csv_info.get("concepts_with_desc", {})
                # Find ALL questions referencing this missing concept
                all_questions_with_missing = []  # (source, json_path, questions_key, q)
                
                if exercise_path and source in ("[Exercise]", "[Both]"):
                    exercise_questions = load_json_questions_with_concepts(exercise_path, "exercise_questions")
                    for q in exercise_questions:
                        if concept_name in q["concepts"]:
                            all_questions_with_missing.append(("Exercise", exercise_path, "exercise_questions", q))
                
                if solved_path and source in ("[Solved]", "[Both]"):
                    solved_questions = load_json_questions_with_concepts(solved_path, "solved_examples_questions")
                    for q in solved_questions:
                        if concept_name in q["concepts"]:
                            all_questions_with_missing.append(("Solved", solved_path, "solved_examples_questions", q))
                
                if all_questions_with_missing:
                    # Only get ONE suggestion per concept (using first question as context)
                    # but store ALL questions so we can apply to all of them
                    sample_q = all_questions_with_missing[0]
                    logger.info(f"         Found {len(all_questions_with_missing)} question(s) with this concept, queuing 1 AI suggestion...")
                    
                    task_coro = get_gemini_concept_suggestion(
                        question_text=sample_q[3]["question_text"],
                        current_concepts=sample_q[3]["concepts"],
                        available_concepts_with_desc=concepts_with_desc,
                        missing_concept=concept_name,
                    )
                    
                    suggestion_tasks.append({
                        "coro": task_coro,
                        "prefix": prefix,
                        "concept_name": concept_name,
                        "q_source": sample_q[0],
                        "q_index": sample_q[3]["question_index"],
                        "q_text": sample_q[3]["question_text"],
                        "available_concepts": available_concepts,
                        # Store ALL questions for bulk apply
                        "all_questions": all_questions_with_missing,
                    })


async def _run_suggestion_tasks(
    suggestion_tasks: List[Dict],
    chapter_stats: Dict[str, Dict[str, int]],
    apply_suggestions: bool,
) -> None:
    """
    Run AI suggestion tasks in parallel and process results.
    
    Internal helper that executes all queued Gemini suggestion tasks with
    concurrency limiting, then processes and logs the results.
    
    Args:
        suggestion_tasks: List of task dicts with 'coro' and metadata.
        chapter_stats: Dict to update with statistics (modified in place).
        apply_suggestions: Whether to apply valid suggestions to JSON files.
    """
    from collections import defaultdict
    
    logger.info("")
    logger.info("=" * 70)
    max_concurrent = getattr(settings, "max_concurrent_generations", 3)
    logger.info(f"RUNNING {len(suggestion_tasks)} AI SUGGESTION TASKS (max {max_concurrent} concurrent)...")
    logger.info("=" * 70)
    
    # Create semaphore for concurrency control
    sem = asyncio.Semaphore(max_concurrent)
    
    async def run_with_semaphore(task_meta):
        async with sem:
            return await task_meta["coro"]
    
    # Run all tasks with semaphore
    results = await asyncio.gather(
        *[run_with_semaphore(t) for t in suggestion_tasks],
        return_exceptions=True
    )
    
    # Attach results to task metadata
    for task_meta, result in zip(suggestion_tasks, results):
        task_meta["result"] = result
    
    # Group results by chapter prefix
    results_by_chapter = defaultdict(list)
    for task_meta in suggestion_tasks:
        results_by_chapter[task_meta["prefix"]].append(task_meta)
    
    # Output results sequentially per chapter
    for prefix in sorted(results_by_chapter.keys()):
        chapter_tasks = results_by_chapter[prefix]
        logger.info(f"")
        logger.info(f"  Chapter: {prefix}")
        logger.info(f"  {'-' * 60}")
        
        for task_meta in chapter_tasks:
            _process_suggestion_result(task_meta, chapter_stats, apply_suggestions)
    
    logger.info("")
    logger.info("=" * 70)


def _process_suggestion_result(
    task_meta: Dict,
    chapter_stats: Dict[str, Dict[str, int]],
    apply_suggestions: bool,
) -> None:
    """
    Process a single AI suggestion result.
    
    Internal helper that logs the result and optionally applies the suggestion
    to the JSON files.
    
    Args:
        task_meta: Task metadata dict with 'result' and other info.
        chapter_stats: Dict to update with statistics.
        apply_suggestions: Whether to apply valid suggestions.
    """
    prefix = task_meta["prefix"]
    concept_name = task_meta["concept_name"]
    q_source = task_meta["q_source"]
    q_index = task_meta["q_index"]
    q_text = task_meta["q_text"]
    result = task_meta["result"]
    
    q_snippet = q_text[:100] + "..." if len(q_text) > 100 else q_text
    
    if isinstance(result, Exception):
        logger.warning(f"    [{q_source} Q#{q_index}] AI suggestion failed: {result}")
        chapter_stats[prefix]["suggestions_failed"] += 1
    elif result and result != "NONE":
        # Validate that the suggested concept exists in available concepts
        available_concepts = task_meta.get("available_concepts", set())
        suggestion_valid = result in available_concepts
        
        logger.info(f"    [{q_source} Q#{q_index}]")
        logger.info(f"       Question: {q_snippet}")
        logger.info(f"       Missing Concept: {concept_name}")
        logger.info(f"       Suggested Concept: {result}")
        
        if suggestion_valid:
            logger.info(f"       Validation: VALID (concept exists in CSV)")
            chapter_stats[prefix]["suggestions_valid"] += 1
            
            if apply_suggestions:
                # Apply to ALL questions with this missing concept
                all_questions = task_meta.get("all_questions", [])
                
                if all_questions:
                    applied_count = 0
                    failed_count = 0
                    
                    for aq_source, aq_json_path, aq_questions_key, aq in all_questions:
                        success = apply_concept_replacement(
                            json_path=aq_json_path,
                            questions_key=aq_questions_key,
                            question_index=aq["question_index"],
                            old_concept=concept_name,
                            new_concept=result,
                        )
                        if success:
                            applied_count += 1
                        else:
                            failed_count += 1
                    
                    if applied_count > 0:
                        logger.info(f"       Applied: Replaced '{concept_name}' with '{result}' in {applied_count} question(s)")
                        chapter_stats[prefix]["concepts_resolved"] += 1  # 1 concept resolved
                        chapter_stats[prefix]["questions_updated"] += applied_count
                    if failed_count > 0:
                        logger.error(f"       Apply FAILED: Could not replace concept in {failed_count} question(s)")
                        chapter_stats[prefix]["apply_failed"] += failed_count
                else:
                    logger.warning(f"       Apply SKIPPED: No questions to apply to")
                    chapter_stats[prefix]["apply_failed"] += 1
        else:
            logger.warning(f"       Validation: INVALID (suggested concept '{result}' not found in CSV)")
            chapter_stats[prefix]["suggestions_invalid"] += 1
            if apply_suggestions:
                logger.warning(f"       Apply SKIPPED: Cannot apply invalid suggestion")
    elif result == "NONE":
        logger.warning(f"    [{q_source} Q#{q_index}]")
        logger.warning(f"       Question: {q_snippet}")
        logger.warning(f"       Missing Concept: {concept_name}")
        logger.warning(f"       Suggested Concept: (no match found)")
        chapter_stats[prefix]["suggestions_none"] += 1


async def check_concept_consistency(
    groups: List[Dict[str, Any]], 
    suggest: bool = False,
    apply_suggestions: bool = False,
) -> Tuple[int, int, List[Dict]]:
    """
    Check that concepts referenced in questions exist in concept CSVs.
    
    Validates that all concept names referenced by exercise questions and
    solved examples actually exist in the corresponding concept CSV. Detects
    various types of mismatches including whitespace, case, and unicode issues.
    
    Optionally uses Gemini AI to suggest corrections for missing concepts.
    
    Args:
        groups: List of file groups from get_file_groups().
        suggest: If True, use Gemini to suggest replacements for missing concepts.
        apply_suggestions: If True, validate and apply Gemini suggestions to JSON files.
                          Requires suggest=True.
                          
    Returns:
        Tuple of (passed_count, failed_count, failures_list) where:
            - passed_count: Number of chapters with no concept issues
            - failed_count: Number of chapters with concept issues
            - failures_list: List of dicts with 'prefix' and 'issues' for failed chapters
            
    Example:
        >>> groups = get_file_groups(Path("data/output"))
        >>> passed, failed, failures = await check_concept_consistency(groups, suggest=True)
        >>> print(f"{passed} passed, {failed} failed")
    """
    passed = 0
    failed = 0
    failures = []
    
    # Collect all suggestion tasks for parallel execution
    suggestion_tasks = []  # List of (task_coro, metadata_dict)
    
    # Track statistics per chapter for summary table
    chapter_stats = create_chapter_stats_dict()
    
    logger.info("=" * 70)
    logger.info("CONCEPT MAPPING CHECK")
    if suggest:
        logger.info("(Gemini suggestions enabled for missing concepts)")
    if apply_suggestions:
        logger.info("(Apply suggestions mode: validated suggestions will be applied to JSON files)")
    logger.info("=" * 70)
    
    for idx, group in enumerate(groups, 1):
        prefix = group["prefix"]
        csv_path = group["concepts_csv"]
        exercise_path = group["exercise_json"]
        solved_path = group["solved_json"]
        
        csv_info = load_csv_chapter_info(csv_path)
        available_concepts = csv_info["concepts"]
        
        # Create multiple lookups for different mismatch types
        available_concepts_stripped = {c.strip(): c for c in available_concepts}
        available_concepts_lower = {c.strip().lower(): c for c in available_concepts}
        available_concepts_normalized = {normalize_concept(c): c for c in available_concepts}
        
        # Track issues: {concept_name: {"source": str, "type": str, "correct_form": Optional[str]}}
        concept_issues: Dict[str, Dict] = {}
        
        # Check exercise JSON concepts
        if exercise_path:
            exercise_info = load_json_info(exercise_path, "exercise_questions")
            for concept in exercise_info["concepts_referenced"]:
                _check_concept_against_available(
                    concept, "[Exercise]",
                    available_concepts,
                    available_concepts_stripped,
                    available_concepts_lower,
                    available_concepts_normalized,
                    concept_issues,
                )
        
        # Check solved examples JSON concepts
        if solved_path:
            solved_info = load_json_info(solved_path, "solved_examples_questions")
            for concept in solved_info["concepts_referenced"]:
                _check_concept_against_available(
                    concept, "[Solved]",
                    available_concepts,
                    available_concepts_stripped,
                    available_concepts_lower,
                    available_concepts_normalized,
                    concept_issues,
                )
        
        if not concept_issues:
            passed += 1
            logger.info(f"  {idx:2}. {prefix:<45} [PASS]")
        else:
            failed += 1
            
            # Count issues by type
            whitespace_mismatches = sum(1 for v in concept_issues.values() if v["type"] == "whitespace_mismatch")
            case_mismatches = sum(1 for v in concept_issues.values() if v["type"] == "case_mismatch")
            invisible_chars = sum(1 for v in concept_issues.values() if v["type"] == "invisible_chars")
            truly_missing = sum(1 for v in concept_issues.values() if v["type"] == "missing")
            
            issue_summary = []
            if whitespace_mismatches > 0:
                issue_summary.append(f"{whitespace_mismatches} whitespace issue(s)")
            if case_mismatches > 0:
                issue_summary.append(f"{case_mismatches} case mismatch(es)")
            if invisible_chars > 0:
                issue_summary.append(f"{invisible_chars} unicode/invisible char(s)")
            if truly_missing > 0:
                issue_summary.append(f"{truly_missing} missing")
            
            logger.error(f"  {idx:2}. {prefix:<45} [FAIL] - {', '.join(issue_summary)}")
            
            _log_concept_issues(
                concept_issues,
                available_concepts,
                csv_info,
                prefix,
                exercise_path,
                solved_path,
                suggest,
                suggestion_tasks,
            )
            
            failures.append({
                "prefix": prefix,
                "issues": sorted(
                    f"{v['source']} {v['type'].upper().replace('_', ' ')}: {k}" 
                    + (f" -> {v['correct_form']}" if v['correct_form'] else "")
                    for k, v in concept_issues.items()
                ),
            })
            
            # Update chapter statistics
            chapter_stats[prefix]["mismatches"] = len(concept_issues)
            chapter_stats[prefix]["missing"] = sum(1 for v in concept_issues.values() if v["type"] == "missing")
    
    logger.info("=" * 70)
    if failed > 0:
        logger.error(f"Concept check: {passed} passed, {failed} failed")
    else:
        logger.info(f"Concept check: {passed} passed, {failed} failed")
    
    # Run all AI suggestion tasks in parallel with concurrency limit
    if suggestion_tasks:
        await _run_suggestion_tasks(suggestion_tasks, chapter_stats, apply_suggestions)
    
    # Print summary table if there are any statistics to show
    if chapter_stats:
        print_summary_table(chapter_stats, suggest, apply_suggestions)
    
    return passed, failed, failures


def check_conventions(input_dir: Path) -> Tuple[int, int, List[Dict]]:
    """
    Check file naming conventions and position consistency.
    
    Verifies that:
    - All files follow the naming pattern: {number}_{name}_{type}.{ext}
    - For CSVs: filename number prefix matches chapter_position column
    - All 3 file types exist for each chapter (csv, exercise json, solved json)
    - No orphan JSON files exist without corresponding CSVs
    
    Args:
        input_dir: Directory containing the files to check.
        
    Returns:
        Tuple of (passed_count, failed_count, failures_list) where:
            - passed_count: Number of chapters with correct conventions
            - failed_count: Number of chapters with convention violations
            - failures_list: List of dicts with 'prefix' and 'issues' for failed chapters
            
    Example:
        >>> passed, failed, failures = check_conventions(Path("data/output"))
        >>> print(f"{passed} passed, {failed} failed")
    """
    passed = 0
    failed = 0
    failures = []
    
    logger.info("=" * 70)
    logger.info("FILE CONVENTIONS CHECK")
    logger.info("=" * 70)
    
    # Get all relevant files
    csv_files = sorted(input_dir.glob("*_concepts.csv"))
    exercise_files = {f.stem.replace("_exercise_questions", ""): f for f in input_dir.glob("*_exercise_questions.json")}
    solved_files = {f.stem.replace("_solved_examples", ""): f for f in input_dir.glob("*_solved_examples.json")}
    
    # Pattern to extract number prefix from filename
    number_pattern = re.compile(r'^(\d+)_')
    
    for idx, csv_path in enumerate(csv_files, 1):
        prefix = csv_path.stem.replace("_concepts", "")
        group_passed = True
        group_issues = []
        
        # Extract number from filename
        match = number_pattern.match(prefix)
        filename_number = match.group(1) if match else None
        
        # Check if filename has number prefix
        if not filename_number:
            group_passed = False
            group_issues.append(f"Filename missing number prefix: {csv_path.name}")
        
        # Load CSV to get chapter_position
        csv_info = load_csv_chapter_info(csv_path)
        chapter_position = csv_info.get("chapter_position")
        
        # Check filename number matches chapter_position
        if filename_number and chapter_position:
            # Compare as integers to handle leading zeros (e.g., "01" == "1")
            try:
                if int(filename_number) != int(chapter_position):
                    group_passed = False
                    group_issues.append(
                        f"Filename number ({filename_number}) != chapter_position ({chapter_position})"
                    )
            except ValueError:
                group_passed = False
                group_issues.append(
                    f"Invalid number format: filename='{filename_number}', position='{chapter_position}'"
                )
        elif filename_number and not chapter_position:
            group_passed = False
            group_issues.append("CSV missing chapter_position column")
        
        # Check if corresponding exercise JSON exists
        if prefix not in exercise_files:
            group_passed = False
            group_issues.append(f"Missing exercise JSON: {prefix}_exercise_questions.json")
        
        # Check if corresponding solved examples JSON exists
        if prefix not in solved_files:
            group_passed = False
            group_issues.append(f"Missing solved JSON: {prefix}_solved_examples.json")
        
        if group_passed:
            passed += 1
            logger.info(f"  {idx:2}. {prefix:<45} [PASS]")
        else:
            failed += 1
            logger.error(f"  {idx:2}. {prefix:<45} [FAIL]")
            for issue in group_issues:
                logger.error(f"      -> {issue}")
            failures.append({
                "prefix": prefix,
                "issues": group_issues,
            })
    
    # Check for orphan JSON files (JSONs without corresponding CSV)
    csv_prefixes = {f.stem.replace("_concepts", "") for f in csv_files}
    
    orphan_exercise = set(exercise_files.keys()) - csv_prefixes
    orphan_solved = set(solved_files.keys()) - csv_prefixes
    
    if orphan_exercise or orphan_solved:
        logger.info("-" * 70)
        logger.info("ORPHAN FILES (JSONs without corresponding CSV):")
        for orphan in sorted(orphan_exercise):
            logger.error(f"      -> {orphan}_exercise_questions.json")
            failed += 1
        for orphan in sorted(orphan_solved):
            logger.error(f"      -> {orphan}_solved_examples.json")
            failed += 1
    
    logger.info("=" * 70)
    if failed > 0:
        logger.error(f"Conventions check: {passed} passed, {failed} failed")
    else:
        logger.info(f"Conventions check: {passed} passed, {failed} failed")
    
    return passed, failed, failures
