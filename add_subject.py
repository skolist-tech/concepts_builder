#!/usr/bin/env python
"""
Add Subject CLI

Creates a subject record in Supabase with a deterministic UUID.

Usage:
    python add_subject.py --school_class_id <uuid> --subject_name "Mathematics"
"""

import argparse
import asyncio
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

import supabase

from config import setup_logging, settings
from utils.uuid_generator import generate_subject_id, validate_uuid

setup_logging()
logger = logging.getLogger(__name__)


def create_supabase_client() -> supabase.Client:
    """Create and return a Supabase client."""
    url = settings.supabase_url
    key = settings.supabase_service_key
    
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_SERVICE_KEY not set in environment")
    
    return supabase.Client(url, key)


async def get_school_class(client: supabase.Client, school_class_id: str) -> dict | None:
    """Fetch school_class details from Supabase."""
    def _fetch():
        return client.table("school_classes").select("*, boards(name)").eq("id", school_class_id).execute()
    
    result = await asyncio.get_event_loop().run_in_executor(None, _fetch)
    
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


async def upsert_subject(
    client: supabase.Client,
    subject_id: str,
    subject_name: str,
    school_class_id: str
) -> dict:
    """Upsert subject record to Supabase."""
    subject_record = {
        "id": subject_id,
        "name": subject_name,
        "school_class_id": school_class_id,
    }
    
    def _upsert():
        return client.table("subjects").upsert(subject_record).execute()
    
    result = await asyncio.get_event_loop().run_in_executor(None, _upsert)
    return result.data[0] if result.data else subject_record


async def main_async(school_class_id: str, subject_name: str) -> None:
    """Main async function."""
    client = create_supabase_client()
    
    # Fetch school_class details
    school_class_data = await get_school_class(client, school_class_id)
    if not school_class_data:
        logger.error(f"Class not found: {school_class_id}")
        sys.exit(1)
    
    school_class_name = school_class_data.get("name", "Unknown")
    board_name = school_class_data.get("boards", {}).get("name", "Unknown") if school_class_data.get("boards") else "Unknown"
    board_id = school_class_data.get("board_id", "Unknown")
    
    # Generate subject ID
    subject_id = generate_subject_id(school_class_id, subject_name)
    
    # Upsert subject
    await upsert_subject(client, subject_id, subject_name, school_class_id)
    
    # Print results
    print()
    print("=" * 50)
    print("Subject Created Successfully")
    print("=" * 50)
    print(f"Board ID:      {board_id}")
    print(f"Board Name:    {board_name}")
    print(f"Class ID:      {school_class_id}")
    print(f"Class Name:    {school_class_name}")
    print(f"Subject Name:  {subject_name}")
    print(f"Subject ID:    {subject_id}")
    print("=" * 50)
    
    logger.info(f"Created subject: {subject_name} (id: {subject_id}) for school_class: {school_class_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Add a subject to Supabase with a deterministic UUID"
    )
    parser.add_argument(
        "--school_class_id",
        type=str,
        required=True,
        help="Class UUID"
    )
    parser.add_argument(
        "--subject_name",
        type=str,
        required=True,
        help="Subject name (e.g., 'Mathematics', 'Science')"
    )
    
    args = parser.parse_args()
    
    if not validate_uuid(args.school_class_id):
        print(f"Error: Invalid school_class_id UUID: {args.school_class_id}", file=sys.stderr)
        sys.exit(1)
    
    try:
        asyncio.run(main_async(args.school_class_id, args.subject_name))
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
