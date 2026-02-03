import os
import logging

import pandas as pd
from prompts import NCERT_GEN

from agents import generate_concepts, generate_solved_examples
from schemas import Chapter, save_csv, SolvedExamplesBank, save_solved_bank_json

logger = logging.getLogger(__name__)

async def test(chapter_pdf_path: str = None, prompt: str = None, output_csv_path: str = None, chapter_number: int = None):

    # CHANGE THESE VALUES TO SWITCH CLASS/CHAPTER:
    #
    # For Class 10 Math Chapter 1: "Class_10", "jemh101.pdf"
    # For Class 10 Math Chapter 2: "Class_10", "jemh102.pdf"
    # For Class 11 Math Chapter 1: "Class_11", "kemh101.pdf"
    # For Class 9 Math Chapter 1:  "Class_09", "iemh101.pdf"
    
    
    if chapter_pdf_path:
        pdf_path = chapter_pdf_path
        logger.info(f"Using provided chapter PDF path: {pdf_path}")
    else:
        class_folder = "test_client"  # ← CHANGE THIS
        pdf_filename = "ch01.pdf"  # ← CHANGE THIS
        pdf_path = os.path.join("helper", class_folder, pdf_filename)
    logger.info(f"Using default chapter PDF path: {pdf_path}")

    # Check if file exists
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found at {pdf_path}")
        return

    if prompt:
        logger.info(f"Using provided prompt: {prompt}")
    else:
        prompt = NCERT_GEN
        logger.info("Using default NCERT_GEN prompt.")

    
    if output_csv_path:
        logger.info(f"Using provided output CSV path: {output_csv_path}")
    else:
        output_csv_path = "helper/data.csv"
        logger.info("Using default output CSV path: helper/data.csv")

    if chapter_number:
        logger.info(f"Using provided chapter number: {chapter_number}")
    else:
        chapter_number = 1
        logger.info("Using default chapter number: 1")

    print(f"Processing PDF: {pdf_path}")
    output: Chapter = await generate_concepts(prompt=prompt, pdf_path=pdf_path)
    print("Generation complete. Saving to CSV...")
    save_csv(output, output_csv_path, chapter_number)
    print("Done!")

async def process_chapter_for_solved_examples(
    chapter_pdf_path: str,
    prompt: str,
    concepts_csv_path: str,
    output_json_path : str) -> SolvedExamplesBank:

    if not os.path.exists(chapter_pdf_path):
        raise FileNotFoundError(f"PDF file not found at {chapter_pdf_path}")
    if not os.path.exists(concepts_csv_path):
        raise FileNotFoundError(f"Concepts CSV file not found at {concepts_csv_path}")
    df = pd.read_csv(concepts_csv_path)
    concepts_list = df['concept_name'].dropna().tolist()
    if not concepts_list:
        raise ValueError("Concepts list extracted from CSV is empty.")
    logger.info(f"Processing chapter for solved examples from PDF: {chapter_pdf_path}")
    output: SolvedExamplesBank = await generate_solved_examples(prompt=prompt, pdf_path=chapter_pdf_path, concepts_list=concepts_list)
    save_solved_bank_json(output, output_json_path)
    logger.info(f"Solved examples saved to JSON at: {output_json_path}")
    return output