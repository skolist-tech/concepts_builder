"""
Schemas package for concepts_builder.

Contains Pydantic models for:
- Concepts, Topics, and Chapters
- Question banks (solved examples and exercise questions)
- Converters for CSV, JSON, PDF, and SQL formats
"""

from schemas.concept_schema import Concept, Topic, Chapter
from schemas.chapter_to_csv import save_csv, csv_to_chapter

from schemas.bank_questions.question_bank_schema import (
    BaseQuestion,
    MatchColumn,
    SolvedExample,
    SolvedExamplesBank,
    ExerciseQuestion,
    ExerciseQuestionsBank,
)
from schemas.bank_questions.solved_bank_to_json import save_solved_bank_json, load_solved_bank_json
from schemas.bank_questions.solved_bank_to_pdf import save_solved_bank_pdf, save_solved_bank_pdf_sync
from schemas.bank_questions.exercise_bank_to_json import save_exercise_bank_json, load_exercise_bank_json
from schemas.bank_questions.exercise_bank_to_pdf import save_exercise_bank_pdf, save_exercise_bank_pdf_sync

__all__ = [
    # Concept models
    "Concept",
    "Topic",
    "Chapter",
    # Chapter converters
    "save_csv",
    "csv_to_chapter",
    # Question models
    "BaseQuestion",
    "MatchColumn",
    "SolvedExample",
    "SolvedExamplesBank",
    "ExerciseQuestion",
    "ExerciseQuestionsBank",
    # Solved examples converters
    "save_solved_bank_json",
    "load_solved_bank_json",
    "save_solved_bank_pdf",
    "save_solved_bank_pdf_sync",
    # Exercise questions converters
    "save_exercise_bank_json",
    "load_exercise_bank_json",
    "save_exercise_bank_pdf",
    "save_exercise_bank_pdf_sync",
]