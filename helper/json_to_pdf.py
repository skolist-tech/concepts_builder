"""
Script to convert all solved examples JSON files to PDFs.
Reads from data/rbse_output directory and generates PDFs in the same location.
"""

import os
import asyncio
import logging

from schemas import load_solved_bank_json, save_solved_bank_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
RBSE_OUTPUT_DIR = "/home/purushottam/Desktop/startup_work/forks/platform_v1/concepts_builder/data/rbse_output/maths_6_corodova/"


async def convert_json_to_pdf(json_path: str, pdf_path: str) -> None:
    """Convert a single JSON file to PDF."""
    try:
        logger.info(f"Loading: {json_path}")
        bank = load_solved_bank_json(json_path)
        
        logger.info(f"Generating PDF: {pdf_path}")
        await save_solved_bank_pdf(bank, pdf_path)
        
        logger.info(f"✅ Successfully created: {pdf_path}")
    except Exception as e:
        import traceback
        logger.error(f"❌ Failed to convert {json_path}: {e}")
        logger.error(traceback.format_exc())


async def convert_all_json_to_pdf(input_dir: str = RBSE_OUTPUT_DIR) -> None:
    """
    Convert all solved examples JSON files in the directory to PDFs.
    
    Args:
        input_dir: Directory containing the JSON files
    """
    if not os.path.exists(input_dir):
        logger.error(f"Directory not found: {input_dir}")
        return
    
    # Find all solved_examples JSON files
    json_files = [
        f for f in os.listdir(input_dir) 
        if f.endswith("_solved_examples.json")
    ]
    
    if not json_files:
        logger.warning(f"No solved_examples JSON files found in {input_dir}")
        return
    
    logger.info(f"Found {len(json_files)} JSON files to convert")
    
    # Create conversion tasks
    tasks = []
    for json_file in json_files:
        json_path = os.path.join(input_dir, json_file)
        pdf_path = json_path.replace(".json", ".pdf")
        tasks.append(convert_json_to_pdf(json_path, pdf_path))
    
    # Run all conversions concurrently
    await asyncio.gather(*tasks)
    
    logger.info(f"🎉 Completed! Converted {len(json_files)} files.")
