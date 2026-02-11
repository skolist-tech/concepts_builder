#!/usr/bin/env python
"""
Add Class CLI

Creates a school_class record in Supabase with a deterministic UUID.

Usage:
    python add_school_class.py --board_id <uuid> --school_class_name "Class 6"
"""

import argparse
import asyncio
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

import supabase

from config import setup_logging, settings
from utils.uuid_generator import generate_school_class_id, validate_uuid

setup_logging()
logger = logging.getLogger(__name__)


def create_supabase_client() -> supabase.Client:
    """Create and return a Supabase client."""
    url = settings.supabase_url
    key = settings.supabase_service_key
    
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_SERVICE_KEY not set in environment")
    
    return supabase.Client(url, key)


async def get_board(client: supabase.Client, board_id: str) -> dict | None:
    """Fetch board details from Supabase."""
    def _fetch():
        return client.table("boards").select("*").eq("id", board_id).execute()
    
    result = await asyncio.get_event_loop().run_in_executor(None, _fetch)
    
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


async def upsert_school_class(
    client: supabase.Client,
    school_class_id: str,
    school_class_name: str,
    board_id: str,
    position: int
) -> dict:
    """Upsert school_class record to Supabase."""
    school_class_record = {
        "id": school_class_id,
        "name": school_class_name,
        "board_id": board_id,
        "position": position,
    }
    
    def _upsert():
        return client.table("school_classes").upsert(school_class_record).execute()
    
    result = await asyncio.get_event_loop().run_in_executor(None, _upsert)
    return result.data[0] if result.data else school_class_record


async def main_async(board_id: str, school_class_name: str, position: int) -> None:
    """Main async function."""
    client = create_supabase_client()
    
    # Fetch board details
    board = await get_board(client, board_id)
    if not board:
        logger.error(f"Board not found: {board_id}")
        sys.exit(1)
    
    board_name = board.get("name", "Unknown")
    
    # Generate school_class ID
    school_class_id = generate_school_class_id(board_id, school_class_name)
    
    # Upsert school_class
    await upsert_school_class(client, school_class_id, school_class_name, board_id, position)
    
    # Print results
    print()
    print("=" * 50)
    print("School Class Created Successfully")
    print("=" * 50)
    print(f"Board ID:    {board_id}")
    print(f"Board Name:  {board_name}")
    print(f"School Class Name:  {school_class_name}")
    print(f"School Class ID:    {school_class_id}")
    print(f"Position:    {position}")
    print("=" * 50)
    
    logger.info(f"Created school_class: {school_class_name} (id: {school_class_id}) for board: {board_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Add a school_class to Supabase with a deterministic UUID"
    )
    parser.add_argument(
        "--board_id",
        type=str,
        required=True,
        help="Board UUID"
    )
    parser.add_argument(
        "--school_class_name",
        type=str,
        required=True,
        help="Class name (e.g., 'Class 6', 'Class 10')"
    )
    parser.add_argument(
        "--position",
        type=int,
        required=True,
        help="Position/order of the class (e.g., 6 for Class 6, 10 for Class 10)"
    )
    
    args = parser.parse_args()
    
    if not validate_uuid(args.board_id):
        print(f"Error: Invalid board_id UUID: {args.board_id}", file=sys.stderr)
        sys.exit(1)
    
    try:
        asyncio.run(main_async(args.board_id, args.school_class_name, args.position))
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
