"""
Question extraction pipeline.

Handles the workflow for extracting solved examples and exercise questions from chapter PDFs.
"""

import logging
from pathlib import Path
from typing import List

import pandas as pd

from agents import generate_solved_examples, generate_exercise_questions
from schemas import SolvedExamplesBank, ExerciseQuestionsBank
from schemas import save_solved_bank_json, save_exercise_bank_json

logger = logging.getLogger(__name__)


def load_concepts_from_csv(csv_path: Path) -> List[str]:
    """
    Load concept names from a concepts CSV file.
    
    Args:
        csv_path: Path to the concepts CSV file.
    
    Returns:
        List of concept names.
    
    Raises:
        FileNotFoundError: If the CSV file doesn't exist.
        ValueError: If no concepts are found in the CSV.
    """
    csv_path = Path(csv_path)
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Concepts CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    concepts_list = df['concept_name'].dropna().tolist()
    
    if not concepts_list:
        raise ValueError(f"No concepts found in CSV: {csv_path}")
    
    logger.info(f"Loaded {len(concepts_list)} concepts from {csv_path}")
    return concepts_list


async def process_chapter_for_solved_examples(
    chapter_pdf_path: Path,
    prompt: str,
    subject_id: str,
    concepts_csv_path: Path,
    output_json_path: Path
) -> SolvedExamplesBank:
    """
    Process a chapter PDF to extract solved examples and save to JSON with UUIDs.
    
    Args:
        chapter_pdf_path: Path to the chapter PDF file.
        prompt: The prompt for solved examples extraction.
        subject_id: Subject UUID for generating question UUIDs.
        concepts_csv_path: Path to the concepts CSV file.
        output_json_path: Path for the output JSON file.
    
    Returns:
        The generated SolvedExamplesBank object.
    
    Raises:
        FileNotFoundError: If the PDF or concepts CSV doesn't exist.
        ValueError: If extraction fails.
    """
    chapter_pdf_path = Path(chapter_pdf_path)
    concepts_csv_path = Path(concepts_csv_path)
    output_json_path = Path(output_json_path)
    
    if not chapter_pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {chapter_pdf_path}")
    
    # Load concepts from CSV
    concepts_list = load_concepts_from_csv(concepts_csv_path)
    
    logger.info(f"Processing chapter for solved examples: {chapter_pdf_path}")
    
    # Generate solved examples using the agent
    solved_bank: SolvedExamplesBank = await generate_solved_examples(
        prompt=prompt,
        pdf_path=str(chapter_pdf_path),
        concepts_list=concepts_list
    )
    
    # Save to JSON with UUIDs
    save_solved_bank_json(solved_bank, str(output_json_path), subject_id)
    logger.info(f"Solved examples saved to JSON: {output_json_path}")
    
    return solved_bank


async def process_chapter_for_exercise_questions(
    chapter_pdf_path: Path,
    prompt: str,
    subject_id: str,
    concepts_csv_path: Path,
    output_json_path: Path
) -> ExerciseQuestionsBank:
    """
    Process a chapter PDF to extract exercise questions and save to JSON with UUIDs.
    
    Args:
        chapter_pdf_path: Path to the chapter PDF file.
        prompt: The prompt for exercise questions extraction.
        subject_id: Subject UUID for generating question UUIDs.
        concepts_csv_path: Path to the concepts CSV file.
        output_json_path: Path for the output JSON file.
    
    Returns:
        The generated ExerciseQuestionsBank object.
    
    Raises:
        FileNotFoundError: If the PDF or concepts CSV doesn't exist.
        ValueError: If extraction fails.
    """
    chapter_pdf_path = Path(chapter_pdf_path)
    concepts_csv_path = Path(concepts_csv_path)
    output_json_path = Path(output_json_path)
    
    if not chapter_pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {chapter_pdf_path}")
    
    # Load concepts from CSV
    concepts_list = load_concepts_from_csv(concepts_csv_path)
    
    logger.info(f"Processing chapter for exercise questions: {chapter_pdf_path}")
    
    # Generate exercise questions using the agent
    exercise_bank: ExerciseQuestionsBank = await generate_exercise_questions(
        prompt=prompt,
        pdf_path=str(chapter_pdf_path),
        concepts_list=concepts_list
    )
    
    # Save to JSON with UUIDs
    save_exercise_bank_json(exercise_bank, str(output_json_path), subject_id)
    logger.info(f"Exercise questions saved to JSON: {output_json_path}")
    
    return exercise_bank
