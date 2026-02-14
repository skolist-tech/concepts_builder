#!/usr/bin/env python
"""
School Class CLI

Manage school_class records in Supabase.

Usage:
    # Add a new school class (by board ID)
    python school_class.py --add --board-id <uuid> --name "Class 6" --position 6

    # Add a new school class (by board name)
    python school_class.py --add --board-name "CBSE" --name "Class 6" --position 6

    # Get a specific school class
    python school_class.py --get --school-class-id <uuid>

    # List all school classes for a board
    python school_class.py --get --board-id <uuid>
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


async def get_boards_by_exact_name(client: supabase.Client, name: str) -> list[dict]:
    """Fetch boards by exact name (case-insensitive)."""
    def _fetch():
        return client.table("boards").select("*").ilike("name", name).execute()
    
    result = await asyncio.get_event_loop().run_in_executor(None, _fetch)
    return result.data if result.data else []


async def resolve_board_by_name(client: supabase.Client, board_name: str) -> dict:
    """Resolve a board by name. Errors if no match or duplicates found."""
    boards = await get_boards_by_exact_name(client, board_name)
    
    if not boards:
        logger.error(f"No board found with name: {board_name}")
        sys.exit(1)
    
    if len(boards) > 1:
        logger.error(f"Multiple boards found with name '{board_name}':")
        for b in boards:
            logger.error(f"  - {b['id']}  {b['name']}")
        logger.error("Use --board-id to specify the exact board.")
        sys.exit(1)
    
    return boards[0]


async def get_school_class(client: supabase.Client, school_class_id: str) -> dict | None:
    """Fetch a single school_class by ID with board info."""
    def _fetch():
        return client.table("school_classes").select("*, boards(name)").eq("id", school_class_id).execute()
    
    result = await asyncio.get_event_loop().run_in_executor(None, _fetch)
    
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


async def get_school_classes_by_board(client: supabase.Client, board_id: str) -> list[dict]:
    """Fetch all school_classes for a board."""
    def _fetch():
        return client.table("school_classes").select("*, boards(name)").eq("board_id", board_id).order("position").execute()
    
    result = await asyncio.get_event_loop().run_in_executor(None, _fetch)
    return result.data if result.data else []


async def get_school_classes_by_name(client: supabase.Client, name: str) -> list[dict]:
    """Fetch school_classes by name (case-insensitive)."""
    def _fetch():
        return client.table("school_classes").select("*, boards(name)").ilike("name", f"%{name}%").order("name").execute()
    
    result = await asyncio.get_event_loop().run_in_executor(None, _fetch)
    return result.data if result.data else []


async def get_all_school_classes(client: supabase.Client) -> list[dict]:
    """Fetch all school_classes from Supabase."""
    def _fetch():
        return client.table("school_classes").select("*, boards(name)").order("name").execute()
    
    result = await asyncio.get_event_loop().run_in_executor(None, _fetch)
    return result.data if result.data else []


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


async def add_school_class_async(board_id: str | None, board_name_arg: str | None, school_class_name: str, position: int) -> None:
    """Add a new school class."""
    client = create_supabase_client()
    
    # Resolve board
    if board_id:
        board = await get_board(client, board_id)
        if not board:
            logger.error(f"Board not found: {board_id}")
            sys.exit(1)
    else:
        board = await resolve_board_by_name(client, board_name_arg)
        board_id = board["id"]
    
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


async def get_school_class_async(school_class_id: str | None, board_id: str | None, name: str | None, all_classes: bool) -> None:
    """Get school class(es) from database."""
    client = create_supabase_client()
    
    if all_classes or board_id or name:
        if all_classes:
            school_classes = await get_all_school_classes(client)
            title = "All School Classes"
        elif name:
            school_classes = await get_school_classes_by_name(client, name)
            title = f"School Classes matching '{name}'"
        else:
            # Verify board exists
            board = await get_board(client, board_id)
            if not board:
                logger.error(f"Board not found: {board_id}")
                sys.exit(1)
            board_name = board.get("name", "Unknown")
            school_classes = await get_school_classes_by_board(client, board_id)
            title = f"School Classes for Board: {board_name}"
        
        if not school_classes:
            print(f"No school classes found{' matching: ' + name if name else ''}.")
            return
        
        print()
        print("=" * 100)
        print(title)
        print("=" * 100)
        print(f"{'ID':<40} {'Name':<20} {'Board':<20} {'Position':<10}")
        print("-" * 100)
        for sc in school_classes:
            board_name = sc.get("boards", {}).get("name", "Unknown") if sc.get("boards") else "Unknown"
            print(f"{sc['id']:<40} {sc['name']:<20} {board_name:<20} {sc['position']:<10}")
        print("=" * 100)
        print(f"Total: {len(school_classes)} school class(es)")
    
    else:
        school_class = await get_school_class(client, school_class_id)
        
        if not school_class:
            logger.error(f"School class not found: {school_class_id}")
            sys.exit(1)
        
        board_name = school_class.get("boards", {}).get("name", "Unknown") if school_class.get("boards") else "Unknown"
        
        print()
        print("=" * 50)
        print("School Class Details")
        print("=" * 50)
        print(f"School Class ID:    {school_class['id']}")
        print(f"School Class Name:  {school_class['name']}")
        print(f"Board ID:           {school_class['board_id']}")
        print(f"Board Name:         {board_name}")
        print(f"Position:           {school_class['position']}")
        print(f"Created At:         {school_class.get('created_at', 'N/A')}")
        print(f"Updated At:         {school_class.get('updated_at', 'N/A')}")
        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Manage school_class records in Supabase"
    )
    
    # Operation flags (mutually exclusive)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument(
        "--add",
        action="store_true",
        help="Add a new school class"
    )
    operation.add_argument(
        "--get",
        action="store_true",
        help="Get school class(es) from database"
    )
    
    # Common arguments
    parser.add_argument(
        "--board-id",
        type=str,
        help="Board UUID (for --add or --get)"
    )
    parser.add_argument(
        "--board-name",
        type=str,
        help="Board name to look up (alternative to --board-id for --add; errors if duplicates exist)"
    )
    
    # Add arguments / Get by name
    parser.add_argument(
        "--name",
        type=str,
        help="School class name (required for --add, optional for --get to search by name)"
    )
    parser.add_argument(
        "--position",
        type=int,
        help="Position/order of the class (required for --add)"
    )
    
    # Get arguments
    parser.add_argument(
        "--school-class-id",
        type=str,
        help="School class UUID to fetch (for --get)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="List all school classes (for --get)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.add:
            if not args.board_id and not args.board_name:
                parser.error("--board-id or --board-name is required when using --add")
            if not args.name:
                parser.error("--name is required when using --add")
            if args.position is None:
                parser.error("--position is required when using --add")
            
            if args.board_id and not validate_uuid(args.board_id):
                print(f"Error: Invalid board-id UUID: {args.board_id}", file=sys.stderr)
                sys.exit(1)
            
            asyncio.run(add_school_class_async(args.board_id, args.board_name, args.name, args.position))
        
        elif args.get:
            if not args.school_class_id and not args.board_id and not args.name and not args.all:
                parser.error("--school-class-id, --board-id, --name, or --all is required when using --get")
            
            if args.school_class_id and not validate_uuid(args.school_class_id):
                print(f"Error: Invalid school-class-id UUID: {args.school_class_id}", file=sys.stderr)
                sys.exit(1)
            
            if args.board_id and not validate_uuid(args.board_id):
                print(f"Error: Invalid board-id UUID: {args.board_id}", file=sys.stderr)
                sys.exit(1)
            
            asyncio.run(get_school_class_async(args.school_class_id, args.board_id, args.name, args.all))
    
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
