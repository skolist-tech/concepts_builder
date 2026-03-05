#!/usr/bin/env python
"""
Verify Concepts, Exercise Questions, and Solved Examples CLI

This is a thin wrapper around the verifier package.

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

from verifier.cli import main

if __name__ == "__main__":
    main()
    