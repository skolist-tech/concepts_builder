#!/usr/bin/env python
"""
Boards CLI

Manage board records in Supabase.

Usage:
    # Add a new board
    python boards.py --add-board --name "CBSE" --description "Central Board of Secondary Education"

    # Get a specific board
    python boards.py --get-board --board-id <uuid>

    # List all boards
    python boards.py --get-board --all
"""

import argparse
import asyncio
import logging
import sys
import uuid

from dotenv import load_dotenv
load_dotenv()

from supabase import acreate_client, AsyncClient
from config import setup_logging, settings
from utils.uuid_generator import validate_uuid

setup_logging()
logger = logging.getLogger(__name__)


async def create_supabase_client() -> AsyncClient:
    """Create and return a Supabase async client."""
    url = settings.supabase_url
    key = settings.supabase_service_key
    
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_SERVICE_KEY not set in environment")
    
    return await acreate_client(url, key)


async def get_board(client: AsyncClient, board_id: str) -> dict | None:
    """Fetch a single board by ID."""
    result = await client.table("boards").select("*").eq("id", board_id).execute()
    
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


async def get_all_boards(client: AsyncClient) -> list[dict]:
    """Fetch all boards from Supabase."""
    result = await client.table("boards").select("*").order("name").execute()
    return result.data if result.data else []


async def get_boards_by_name(client: AsyncClient, name: str) -> list[dict]:
    """Fetch boards by name (case-insensitive)."""
    result = await client.table("boards").select("*").ilike("name", f"%{name}%").order("name").execute()
    return result.data if result.data else []


async def upsert_board(
    client: AsyncClient,
    board_id: str,
    name: str,
    description: str | None = None
) -> dict:
    """Upsert board record to Supabase."""
    board_record = {
        "id": board_id,
        "name": name,
    }
    if description:
        board_record["description"] = description
    
    result = await client.table("boards").upsert(board_record).execute()
    return result.data[0] if result.data else board_record


async def add_board_async(name: str, description: str | None) -> None:
    """Add a new board."""
    client = await create_supabase_client()
    
    # Generate a random UUID for the board (root entity)
    board_id = str(uuid.uuid4())
    
    # Upsert board
    await upsert_board(client, board_id, name, description)
    
    # Print results
    print()
    print("=" * 50)
    print("Board Created Successfully")
    print("=" * 50)
    print(f"Board ID:      {board_id}")
    print(f"Board Name:    {name}")
    if description:
        print(f"Description:   {description}")
    print("=" * 50)
    
    logger.info(f"Created board: {name} (id: {board_id})")


async def get_board_async(board_id: str | None, all_boards: bool, name: str | None) -> None:
    """Get board(s) from database."""
    client = await create_supabase_client()
    
    if all_boards or name:
        if name:
            boards = await get_boards_by_name(client, name)
            title = f"Boards matching '{name}'"
        else:
            boards = await get_all_boards(client)
            title = "All Boards"
        
        if not boards:
            print(f"No boards found{' matching: ' + name if name else ''}.")
            return
        
        print()
        print("=" * 80)
        print(title)
        print("=" * 80)
        print(f"{'ID':<40} {'Name':<20} {'Description':<20}")
        print("-" * 80)
        for board in boards:
            desc = board.get("description", "") or ""
            desc = desc[:17] + "..." if len(desc) > 20 else desc
            print(f"{board['id']:<40} {board['name']:<20} {desc:<20}")
        print("=" * 80)
        print(f"Total: {len(boards)} board(s)")
    else:
        board = await get_board(client, board_id)
        
        if not board:
            logger.error(f"Board not found: {board_id}")
            sys.exit(1)
        
        print()
        print("=" * 50)
        print("Board Details")
        print("=" * 50)
        print(f"Board ID:      {board['id']}")
        print(f"Board Name:    {board['name']}")
        if board.get("description"):
            print(f"Description:   {board['description']}")
        print(f"Created At:    {board.get('created_at', 'N/A')}")
        print(f"Updated At:    {board.get('updated_at', 'N/A')}")
        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Manage board records in Supabase"
    )
    
    # Operation flags (mutually exclusive)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument(
        "--add-board",
        action="store_true",
        help="Add a new board"
    )
    operation.add_argument(
        "--get-board",
        action="store_true",
        help="Get board(s) from database"
    )
    
    # Add board arguments / Get by name
    parser.add_argument(
        "--name",
        type=str,
        help="Board name (required for --add-board, optional for --get-board to search by name)"
    )
    parser.add_argument(
        "--description",
        type=str,
        help="Board description (optional for --add-board)"
    )
    
    # Get board arguments
    parser.add_argument(
        "--board-id",
        type=str,
        help="Board UUID to fetch (for --get-board)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="List all boards (for --get-board)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.add_board:
            if not args.name:
                parser.error("--name is required when using --add-board")
            asyncio.run(add_board_async(args.name, args.description))
        
        elif args.get_board:
            if not args.board_id and not args.all and not args.name:
                parser.error("--board-id, --name, or --all is required when using --get-board")
            
            if args.board_id and not validate_uuid(args.board_id):
                print(f"Error: Invalid board-id UUID: {args.board_id}", file=sys.stderr)
                sys.exit(1)
            
            asyncio.run(get_board_async(args.board_id, args.all, args.name))
    
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
