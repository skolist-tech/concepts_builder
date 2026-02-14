#!/usr/bin/env python
"""
Verify Concepts, Exercise Questions, and Solved Examples CLI

Validates consistency between concept CSVs and their corresponding JSON files.

Three independent verification checks:
1. --check-chapters: Verify chapter_name and chapter_id match between CSVs and JSONs
2. --check-concepts: Verify concepts in questions exist in concept CSVs
3. --check-conventions: Verify file naming conventions and position consistency

Optional:
--suggest: Use Gemini AI to suggest correct concept mappings for missing concepts

Usage:
    python verify_concept_exercise_solved_example.py --input_dir <directory_path> --check-chapters
    python verify_concept_exercise_solved_example.py --input_dir <directory_path> --check-concepts
    python verify_concept_exercise_solved_example.py --input_dir <directory_path> --check-concepts --suggest
    python verify_concept_exercise_solved_example.py --input_dir <directory_path> --check-conventions
    python verify_concept_exercise_solved_example.py --input_dir <directory_path> --check-chapters --check-concepts --check-conventions
"""

import argparse
import asyncio
import csv
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional
from collections import defaultdict

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from config import setup_logging, settings
from agents.base import get_gemini_client
from google.genai import types

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)


def get_file_groups(input_dir: Path) -> List[Dict[str, Path]]:
    """
    Group related files by chapter prefix.
    
    Returns list of dicts with keys: 'concepts_csv', 'exercise_json', 'solved_json'
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    csv_files = sorted(input_dir.glob("*_concepts.csv"))
    if not csv_files:
        raise ValueError(f"No concept CSV files found in: {input_dir}")
    
    groups = []
    for csv_file in csv_files:
        # Extract prefix (e.g., "01_knowing_our_numbers" from "01_knowing_our_numbers_concepts.csv")
        prefix = csv_file.stem.replace("_concepts", "")
        
        exercise_json = input_dir / f"{prefix}_exercise_questions.json"
        solved_json = input_dir / f"{prefix}_solved_examples.json"
        
        groups.append({
            "prefix": prefix,
            "concepts_csv": csv_file,
            "exercise_json": exercise_json if exercise_json.exists() else None,
            "solved_json": solved_json if solved_json.exists() else None,
        })
    
    return groups


def load_csv_chapter_info(csv_path: Path) -> Dict[str, Any]:
    """Load chapter info and concept names from a concepts CSV."""
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        return {
            "chapter_name": None,
            "chapter_id": None,
            "chapter_position": None,
            "concepts": set(),
            "concepts_with_desc": {},
            "internal_inconsistencies": [],
        }
    
    first_row = rows[0]
    chapter_name = first_row.get("chapter_name", "").strip()
    chapter_id = first_row.get("chapter_id", "").strip()
    chapter_position = first_row.get("chapter_position", "").strip()
    
    # Check all rows have consistent chapter_name and chapter_id
    internal_inconsistencies = []
    concepts = set()
    concepts_with_desc = {}
    
    for i, row in enumerate(rows, 1):
        row_chapter_name = row.get("chapter_name", "").strip()
        row_chapter_id = row.get("chapter_id", "").strip()
        concept_name = row.get("concept_name", "").strip()
        concept_desc = row.get("concept_description", "").strip()
        
        if concept_name:
            concepts.add(concept_name)
            concepts_with_desc[concept_name] = concept_desc


        if row_chapter_name != chapter_name:
            internal_inconsistencies.append(
                f"Row {i}: chapter_name '{row_chapter_name}' != first row '{chapter_name}'"
            )
        
        if row_chapter_id != chapter_id:
            internal_inconsistencies.append(
                f"Row {i}: chapter_id '{row_chapter_id}' != first row '{chapter_id}'"
            )
    
    return {
        "chapter_name": chapter_name,
        "chapter_id": chapter_id,
        "chapter_position": chapter_position,
        "concepts": concepts,
        "concepts_with_desc": concepts_with_desc,
        "internal_inconsistencies": internal_inconsistencies,
    }


def load_json_info(json_path: Path, questions_key: str) -> Dict[str, Any]:
    """Load chapter info and concept references from a JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    concepts_referenced = set()
    questions = data.get(questions_key, [])
    for question in questions:
        for concept in question.get("concepts", []):
            if concept:
                concepts_referenced.add(concept.strip())
    
    return {
        "chapter_name": data.get("chapter_name", "").strip(),
        "chapter_id": data.get("chapter_id", "").strip(),
        "concepts_referenced": concepts_referenced,
        "question_count": len(questions),
    }


def load_json_questions_with_concepts(json_path: Path, questions_key: str) -> List[Dict[str, Any]]:
    """
    Load questions with their text and concepts for suggestion purposes.
    
    Returns list of dicts with keys: question_text, concepts, question_index
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    result = []
    questions = data.get(questions_key, [])
    for idx, question in enumerate(questions, 1):
        question_text = question.get("question_text", "").strip()
        concepts = [c.strip() for c in question.get("concepts", []) if c]
        result.append({
            "question_index": idx,
            "question_text": question_text,
            "concepts": concepts,
        })
    return result


async def get_gemini_concept_suggestion(
    question_text: str,
    current_concepts: List[str],
    available_concepts_with_desc: Dict[str, str],
    missing_concept: str,
) -> Optional[str]:
    """
    Use Gemini to suggest the correct concept mapping for a question.
    
    Args:
        question_text: The question text
        current_concepts: List of concepts currently associated with the question
        available_concepts_with_desc: Dict of {concept_name: concept_description} from CSV
        missing_concept: The concept name that was not found in CSV
    
    Returns:
        Suggested replacement concept name, or None if no suggestion
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


def check_chapter_consistency(groups: List[Dict[str, Path]]) -> Tuple[int, int, List[Dict]]:
    """
    Check chapter_name and chapter_id consistency between CSV and JSONs.
    
    Returns:
        Tuple of (passed_count, failed_count, failures_list)
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


def is_subsequence(shorter: str, longer: str) -> bool:
    """
    Check if 'shorter' is a subsequence of 'longer' (case-insensitive).
    
    A subsequence means characters appear in order but don't need to be contiguous.
    e.g., "ace" is a subsequence of "abcde"
    """
    shorter = shorter.lower()
    longer = longer.lower()
    
    it = iter(longer)
    return all(char in it for char in shorter)


def find_similar_concepts(missing_concept: str, available_concepts: Set[str], max_suggestions: int = 3) -> List[str]:
    """
    Find available concepts where one is a subsequence of the other (case-insensitive).
    
    Args:
        missing_concept: The concept that was not found
        available_concepts: Set of available concept names from CSV
        max_suggestions: Maximum number of suggestions to return
    
    Returns:
        List of similar concept names
    """
    suggestions = []
    
    for available in available_concepts:
        # Check if missing concept is subsequence of available, or vice versa
        if is_subsequence(missing_concept, available) or is_subsequence(available, missing_concept):
            suggestions.append(available)
    
    return sorted(suggestions)[:max_suggestions]


async def check_concept_consistency(
    groups: List[Dict[str, Path]], 
    suggest: bool = False
) -> Tuple[int, int, List[Dict]]:
    """
    Check that concepts referenced in questions exist in concept CSVs.
    
    Args:
        groups: List of file groups to check
        suggest: If True, use Gemini to suggest replacements for missing concepts
    
    Returns:
        Tuple of (passed_count, failed_count, failures_list)
    """
    passed = 0
    failed = 0
    failures = []
    
    # Collect all suggestion tasks for parallel execution
    suggestion_tasks = []  # List of (task_coro, metadata_dict)
    
    logger.info("=" * 70)
    logger.info("CONCEPT MAPPING CHECK")
    if suggest:
        logger.info("(Gemini suggestions enabled for missing concepts)")
    logger.info("=" * 70)
    
    for idx, group in enumerate(groups, 1):
        prefix = group["prefix"]
        csv_path = group["concepts_csv"]
        exercise_path = group["exercise_json"]
        solved_path = group["solved_json"]
        
        csv_info = load_csv_chapter_info(csv_path)
        available_concepts = csv_info["concepts"]
        
        # Create multiple lookups for different mismatch types
        # Stripped lookup: {stripped: original}
        available_concepts_stripped = {c.strip(): c for c in available_concepts}
        # Case-insensitive lookup: {lowercase_stripped: original}
        available_concepts_lower = {c.strip().lower(): c for c in available_concepts}
        
        # Track issues: {concept_name: {"source": str, "type": str, "correct_form": Optional[str]}}
        # type can be "whitespace_mismatch", "case_mismatch", "invisible_chars", or "missing"
        concept_issues: Dict[str, Dict] = {}
        
        def normalize_concept(s: str) -> str:
            """Normalize a concept name by stripping and replacing various whitespace chars."""
            import unicodedata
            # Normalize unicode (NFKC converts various unicode chars to their canonical form)
            s = unicodedata.normalize('NFKC', s)
            # Replace various whitespace characters with regular space
            s = ''.join(' ' if c.isspace() else c for c in s)
            # Strip and collapse multiple spaces
            return ' '.join(s.split())
        
        # Create normalized lookup: {normalized: original}
        available_concepts_normalized = {normalize_concept(c): c for c in available_concepts}
        
        def check_concept(concept: str, source: str):
            """Check a concept and track the issue type."""
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
        
        # Check exercise JSON concepts
        if exercise_path:
            exercise_info = load_json_info(exercise_path, "exercise_questions")
            for concept in exercise_info["concepts_referenced"]:
                check_concept(concept, "[Exercise]")
        
        # Check solved examples JSON concepts
        if solved_path:
            solved_info = load_json_info(solved_path, "solved_examples_questions")
            for concept in solved_info["concepts_referenced"]:
                check_concept(concept, "[Solved]")
        
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
                        # Find questions referencing this missing concept
                        questions_with_missing = []
                        
                        if exercise_path and source in ("[Exercise]", "[Both]"):
                            exercise_questions = load_json_questions_with_concepts(exercise_path, "exercise_questions")
                            for q in exercise_questions:
                                if concept_name in q["concepts"]:
                                    questions_with_missing.append(("Exercise", q))
                        
                        if solved_path and source in ("[Solved]", "[Both]"):
                            solved_questions = load_json_questions_with_concepts(solved_path, "solved_examples_questions")
                            for q in solved_questions:
                                if concept_name in q["concepts"]:
                                    questions_with_missing.append(("Solved", q))
                        
                        if questions_with_missing:
                            logger.info(f"         Queuing AI suggestions for {len(questions_with_missing)} question(s)...")
                            for q_source, q in questions_with_missing[:3]:  # Limit to 3 questions per concept
                                task_coro = get_gemini_concept_suggestion(
                                    question_text=q["question_text"],
                                    current_concepts=q["concepts"],
                                    available_concepts_with_desc=concepts_with_desc,
                                    missing_concept=concept_name,
                                )
                                suggestion_tasks.append({
                                    "coro": task_coro,
                                    "prefix": prefix,
                                    "concept_name": concept_name,
                                    "q_source": q_source,
                                    "q_index": q["question_index"],
                                    "q_text": q["question_text"],
                                })
            
            failures.append({
                "prefix": prefix,
                "issues": sorted(
                    f"{v['source']} {v['type'].upper().replace('_', ' ')}: {k}" 
                    + (f" -> {v['correct_form']}" if v['correct_form'] else "")
                    for k, v in concept_issues.items()
                ),
            })
    
    logger.info("=" * 70)
    if failed > 0:
        logger.error(f"Concept check: {passed} passed, {failed} failed")
    else:
        logger.info(f"Concept check: {passed} passed, {failed} failed")
    
    # Run all AI suggestion tasks in parallel with concurrency limit
    if suggestion_tasks:
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
                concept_name = task_meta["concept_name"]
                q_source = task_meta["q_source"]
                q_index = task_meta["q_index"]
                q_text = task_meta["q_text"]
                result = task_meta["result"]
                
                q_snippet = q_text[:100] + "..." if len(q_text) > 100 else q_text
                
                if isinstance(result, Exception):
                    logger.warning(f"    [{q_source} Q#{q_index}] AI suggestion failed: {result}")
                elif result and result != "NONE":
                    logger.info(f"    [{q_source} Q#{q_index}]")
                    logger.info(f"       Question: {q_snippet}")
                    logger.info(f"       Missing Concept: {concept_name}")
                    logger.info(f"       Suggested Concept: {result}")
                elif result == "NONE":
                    logger.warning(f"    [{q_source} Q#{q_index}]")
                    logger.warning(f"       Question: {q_snippet}")
                    logger.warning(f"       Missing Concept: {concept_name}")
                    logger.warning(f"       Suggested Concept: (no match found)")
        
        logger.info("")
        logger.info("=" * 70)
    
    return passed, failed, failures


def check_conventions(input_dir: Path) -> Tuple[int, int, List[Dict]]:
    """
    Check file naming conventions and position consistency.
    
    Verifies:
    - All files follow naming pattern: {number}_{name}_{type}.{ext}
    - For CSVs: filename number prefix matches chapter_position column
    - All 3 file types exist for each chapter (csv, exercise json, solved json)
    
    Returns:
        Tuple of (passed_count, failed_count, failures_list)
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


def main():
    parser = argparse.ArgumentParser(
        description="Verify consistency between concept CSVs and question JSONs"
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Directory containing concept CSVs and question JSONs"
    )
    parser.add_argument(
        "--check-chapters",
        action="store_true",
        help="Check chapter_name and chapter_id consistency"
    )
    parser.add_argument(
        "--check-concepts",
        action="store_true",
        help="Check that concepts in questions exist in CSVs"
    )
    parser.add_argument(
        "--suggest",
        action="store_true",
        help="Use Gemini AI to suggest correct concept mappings for missing concepts (requires --check-concepts)"
    )
    parser.add_argument(
        "--check-conventions",
        action="store_true",
        help="Check file naming conventions and position consistency"
    )
    
    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    
    # Require at least one check
    if not args.check_chapters and not args.check_concepts and not args.check_conventions:
        logger.error("Please specify at least one check: --check-chapters, --check-concepts, or --check-conventions")
        sys.exit(1)
    
    # --suggest requires --check-concepts
    if args.suggest and not args.check_concepts:
        logger.error("--suggest requires --check-concepts to be enabled")
        sys.exit(1)
    
    logger.info(f"Input directory: {input_dir}")
    logger.info("")
    
    try:
        groups = get_file_groups(input_dir)
        logger.info(f"Found {len(groups)} chapter file groups")
        logger.info("")
        
        total_failed = 0
        
        if args.check_chapters:
            _, ch_failed, _ = check_chapter_consistency(groups)
            total_failed += ch_failed
            logger.info("")
        
        if args.check_concepts:
            _, co_failed, _ = asyncio.run(check_concept_consistency(groups, suggest=args.suggest))
            total_failed += co_failed
            logger.info("")
        
        if args.check_conventions:
            _, conv_failed, _ = check_conventions(input_dir)
            total_failed += conv_failed
        
        if total_failed > 0:
            sys.exit(1)
        
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
