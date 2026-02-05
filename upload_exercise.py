"""
Upload exercise questions JSON to Supabase database.

Usage:
    uv run python upload_exercise.py
"""

import asyncio
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from config import setup_logging, get_subject_id
from schemas import load_exercise_bank_json
from pipelines.upload_pipeline import (
    create_supabase_client,
    upload_exercise_questions_to_supabase,
)
from utils.paths import get_exercise_questions_json_path

setup_logging()


async def upload_to_db(pdf_path: str | Path, subject_name: str = "maths_6_corodova"):
    """Upload exercise questions from JSON to Supabase."""
    pdf_path = Path(pdf_path)
    
    # Get subject ID from config
    subject_id = get_subject_id(subject_name)
    if not subject_id:
        raise ValueError(f"Subject ID not found for: {subject_name}")
    
    # Get JSON path
    json_path = get_exercise_questions_json_path(pdf_path)
    
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    
    print(f"📤 Uploading: {json_path.name}")
    print(f"   Subject: {subject_name} ({subject_id})")
    
    # Load the JSON
    print("  ⏳ Loading JSON...")
    exercise_bank = load_exercise_bank_json(str(json_path))
    print(f"  ✅ Loaded {len(exercise_bank.exercise_questions)} questions")
    
    # Create Supabase client and upload
    print("  ⏳ Uploading to Supabase...")
    client = create_supabase_client()
    
    stats = await upload_exercise_questions_to_supabase(
        client=client,
        exercise_bank=exercise_bank,
        subject_id=subject_id,
    )
    
    print(f"  ✅ Upload complete!")
    print(f"     Questions upserted: {stats['questions_upserted']}")
    print(f"     Concept maps upserted: {stats['maps_upserted']}")
    
    return stats


async def main():
    # === CONFIGURE YOUR PDF PATH AND SUBJECT HERE ===
    pdf_path = Path("data/rbse/maths_6_corodova/13_perimeter_and_area.pdf")
    subject_name = "maths_6_corodova"
    
    # Or process multiple chapters:
    # pdf_paths = [
    #     Path("data/rbse/maths_6_corodova/05_fractions.pdf"),
    #     Path("data/rbse/maths_6_corodova/06_decimals.pdf"),
    # ]
    # for pdf_path in pdf_paths:
    #     await upload_to_db(pdf_path, subject_name)
    
    await upload_to_db(pdf_path, subject_name)


if __name__ == "__main__":
    asyncio.run(main())
