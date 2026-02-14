"""
Path utilities for managing input/output file paths across the application.
"""

import os
from pathlib import Path
from typing import List, Optional

from config import settings


def get_chapter_paths(
    input_dir: Optional[Path] = None,
    chapters_filter: Optional[List[str]] = None
) -> List[Path]:
    """
    Get list of chapter PDF paths from the input directory.
    
    Args:
        input_dir: Directory containing chapter PDFs. Defaults to RBSE maths_6_corodova.
        chapters_filter: Optional list of specific chapter filenames to include.
                        If None, all chapters are included.
    
    Returns:
        List of Path objects for each chapter PDF.
    """
    if input_dir is None:
        raise ValueError("Input directory must be provided")
    
    input_dir = Path(input_dir)
    
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    chapter_paths = [
        input_dir / f
        for f in os.listdir(input_dir)
        if f.endswith(".pdf") and not f.startswith("index")
    ]
    
    if chapters_filter:
        chapter_paths = [p for p in chapter_paths if p.name in chapters_filter]
    
    return sorted(chapter_paths)


def get_chapter_name(chapter_pdf_path: Path) -> str:
    """
    Extract chapter name from PDF path (without extension).
    
    Args:
        chapter_pdf_path: Path to chapter PDF file.
    
    Returns:
        Chapter name string (e.g., "01_knowing_our_numbers")
    """
    return chapter_pdf_path.stem


def get_concepts_csv_path(
    chapter_pdf_path: Path,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Get the output path for concepts CSV file.
    
    Args:
        chapter_pdf_path: Path to the chapter PDF.
        output_dir: Output directory. Defaults to RBSE output directory.
    
    Returns:
        Path for the concepts CSV file.
    """
    if output_dir is None:
        raise ValueError("Output directory must be provided")
    
    chapter_name = get_chapter_name(chapter_pdf_path)
    return Path(output_dir) / f"{chapter_name}_concepts.csv"


def get_solved_examples_json_path(
    chapter_pdf_path: Path,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Get the output path for solved examples JSON file.
    
    Args:
        chapter_pdf_path: Path to the chapter PDF.
        output_dir: Output directory. Defaults to RBSE output directory.
    
    Returns:
        Path for the solved examples JSON file.
    """
    if output_dir is None:
        raise ValueError("Output directory must be provided")
    
    chapter_name = get_chapter_name(chapter_pdf_path)
    return Path(output_dir) / f"{chapter_name}_solved_examples.json"


def get_solved_examples_pdf_path(
    chapter_pdf_path: Path,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Get the output path for solved examples PDF file.
    
    Args:
        chapter_pdf_path: Path to the chapter PDF.
        output_dir: Output directory. Defaults to RBSE output directory.
    
    Returns:
        Path for the solved examples PDF file.
    """
    if output_dir is None:
        raise ValueError("Output directory must be provided")
    
    chapter_name = get_chapter_name(chapter_pdf_path)
    return Path(output_dir) / f"{chapter_name}_solved_examples.pdf"


def get_exercise_questions_json_path(
    chapter_pdf_path: Path,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Get the output path for exercise questions JSON file.
    
    Args:
        chapter_pdf_path: Path to the chapter PDF.
        output_dir: Output directory. Defaults to RBSE output directory.
    
    Returns:
        Path for the exercise questions JSON file.
    """
    if output_dir is None:
        raise ValueError("Output directory must be provided")
    
    chapter_name = get_chapter_name(chapter_pdf_path)
    return Path(output_dir) / f"{chapter_name}_exercise_questions.json"


def get_exercise_questions_pdf_path(
    chapter_pdf_path: Path,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Get the output path for exercise questions PDF file.
    
    Args:
        chapter_pdf_path: Path to the chapter PDF.
        output_dir: Output directory. Defaults to RBSE output directory.
    
    Returns:
        Path for the exercise questions PDF file.
    """
    if output_dir is None:
        raise ValueError("Output directory must be provided")
    
    chapter_name = get_chapter_name(chapter_pdf_path)
    return Path(output_dir) / f"{chapter_name}_exercise_questions.pdf"


def ensure_output_dir(output_dir: Optional[Path] = None) -> Path:
    """
    Ensure the output directory exists, creating it if necessary.
    
    Args:
        output_dir: Directory path to ensure. Defaults to RBSE output directory.
    
    Returns:
        The output directory path.
    """
    if output_dir is None:
        raise ValueError("Output directory must be provided")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
