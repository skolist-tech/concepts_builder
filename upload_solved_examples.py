"""
Upload solved examples JSON to Supabase database.

Usage:
    uv run python upload_solved_examples.py
"""

import asyncio
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from config import setup_logging, get_subject_id
from schemas import load_solved_bank_json
from pipelines.upload_pipeline import (
    create_supabase_client,
    upload_solved_examples_to_supabase,
)
from utils.paths import get_solved_examples_json_path

setup_logging()


async def upload_to_db(pdf_path: str | Path, subject_name: str = "maths_6_corodova"):
    """Upload solved examples from JSON to Supabase."""
    pdf_path = Path(pdf_path)
    
    # Get subject ID from config
    subject_id = get_subject_id(subject_name)
    if not subject_id:
        raise ValueError(f"Subject ID not found for: {subject_name}")
    
    # Get JSON path
    json_path = get_solved_examples_json_path(pdf_path)
    
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    
    print(f"📤 Uploading: {json_path.name}")
    print(f"   Subject: {subject_name} ({subject_id})")
    
    # Load the JSON
    print("  ⏳ Loading JSON...")
    solved_bank = load_solved_bank_json(str(json_path))
    print(f"  ✅ Loaded {len(solved_bank.solved_examples_questions)} solved examples")
    
    # Create Supabase client and upload
    print("  ⏳ Uploading to Supabase...")
    client = create_supabase_client()
    
    stats = await upload_solved_examples_to_supabase(
        client=client,
        solved_bank=solved_bank,
        subject_id=subject_id,
    )
    
    print(f"  ✅ Upload complete!")
    print(f"     Questions upserted: {stats['questions_upserted']}")
    print(f"     Concept maps upserted: {stats['maps_upserted']}")
    
    return stats


async def main():
    # === CONFIGURE YOUR SUBJECT HERE ===
    subject_name = "maths_6_corodova"
    
    # All chapters from RBSE 6th Maths
    pdf_paths = [
        Path("data/rbse/maths_6_corodova/01_knowing_our_numbers.pdf"),
        Path("data/rbse/maths_6_corodova/02_whole_numbers.pdf"),
        Path("data/rbse/maths_6_corodova/03_playing_with_numbers.pdf"),
        Path("data/rbse/maths_6_corodova/04_integers.pdf"),
        Path("data/rbse/maths_6_corodova/05_fractions.pdf"),
        Path("data/rbse/maths_6_corodova/06_decimals.pdf"),
        Path("data/rbse/maths_6_corodova/07_algebra.pdf"),
        Path("data/rbse/maths_6_corodova/08_ratio_and_proportion.pdf"),
        Path("data/rbse/maths_6_corodova/09_basic_geometrical_ideas.pdf"),
        Path("data/rbse/maths_6_corodova/10_understanding_elementary_shapes.pdf"),
        Path("data/rbse/maths_6_corodova/11_symmetry.pdf"),
        Path("data/rbse/maths_6_corodova/12_practical_geometry.pdf"),
        Path("data/rbse/maths_6_corodova/13_perimeter_and_area.pdf"),
        Path("data/rbse/maths_6_corodova/14_data_handling.pdf"),
    ]
    
    print(f"🚀 Starting upload of {len(pdf_paths)} chapters (solved examples)...")
    print("=" * 50)
    
    total_questions = 0
    total_maps = 0
    failed_chapters = []
    
    for i, pdf_path in enumerate(pdf_paths, 1):
        print(f"\n[{i}/{len(pdf_paths)}] Processing: {pdf_path.name}")
        try:
            stats = await upload_to_db(pdf_path, subject_name)
            total_questions += stats['questions_upserted']
            total_maps += stats['maps_upserted']
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            failed_chapters.append(pdf_path.name)
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    print(f"Total solved examples upserted: {total_questions}")
    print(f"Total concept maps upserted: {total_maps}")
    if failed_chapters:
        print(f"Failed chapters ({len(failed_chapters)}): {failed_chapters}")
    else:
        print("✅ All chapters uploaded successfully!")


if __name__ == "__main__":
    asyncio.run(main())
