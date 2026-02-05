"""
Pipelines package for concepts_builder.

Contains orchestration logic for processing chapters through various stages:
- Concept generation from PDFs
- Question extraction (solved examples & exercises)
- PDF generation from questions
- Upload to Supabase
"""

from pipelines.concept_pipeline import process_chapter_for_concepts
from pipelines.questions_pipeline import (
    process_chapter_for_solved_examples,
    process_chapter_for_exercise_questions,
)
from pipelines.pdf_pipeline import (
    generate_solved_examples_pdf,
    generate_exercise_questions_pdf,
    generate_all_pdfs,
)
from pipelines.upload_pipeline import (
    upload_solved_examples_to_supabase,
    upload_exercise_questions_to_supabase,
    upload_all_chapters,
)

__all__ = [
    # Concept generation
    "process_chapter_for_concepts",
    # Question extraction
    "process_chapter_for_solved_examples",
    "process_chapter_for_exercise_questions",
    # PDF generation
    "generate_solved_examples_pdf",
    "generate_exercise_questions_pdf",
    "generate_all_pdfs",
    # Supabase upload
    "upload_solved_examples_to_supabase",
    "upload_exercise_questions_to_supabase",
    "upload_all_chapters",
]
