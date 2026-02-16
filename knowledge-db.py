"""
Unified CLI to interact with Board / School Class / Subject in the knowledge database.

Usage:
    # Boards
    uv run python knowledge-db.py board get --all
    uv run python knowledge-db.py board get --id <uuid>
    uv run python knowledge-db.py board get --name "CBSE"
    uv run python knowledge-db.py board add --name "RBSE" --description "Rajasthan Board"

    # School Classes
    uv run python knowledge-db.py class get --all
    uv run python knowledge-db.py class get --id <uuid>
    uv run python knowledge-db.py class get --name "Class 6"
    uv run python knowledge-db.py class get --board-id <uuid>
    uv run python knowledge-db.py class get --board-name "CBSE"
    uv run python knowledge-db.py class add --board-id <uuid> --name "Class 6" --position 6

    # Subjects
    uv run python knowledge-db.py subject get --all
    uv run python knowledge-db.py subject get --id <uuid>
    uv run python knowledge-db.py subject get --name "Math"
    uv run python knowledge-db.py subject add --id <uuid> --name "Mathematics"
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

from knowledge_db_rest.boards import (
    get_board_by_id,
    get_all_boards,
    get_all_boards_by_name,
    upsert_board,
)
from knowledge_db_rest.school_classes import (
    get_school_class_by_id,
    get_all_school_classes,
    get_all_school_classes_by_name,
    get_all_school_classes_by_board_id,
    get_all_school_classes_by_board_name,
    upsert_school_class,
)
from knowledge_db_rest.subjects import (
    get_subject_by_id,
    get_all_subjects,
    get_all_subjects_by_name,
    upsert_subject,
)

setup_logging()
logger = logging.getLogger(__name__)


async def create_supabase_client() -> AsyncClient:
    """Create and return a Supabase client."""
    url = settings.supabase_url
    key = settings.supabase_service_key
    
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_SERVICE_KEY not set in environment")
    
    client: AsyncClient = await acreate_client(url, key)
    return client


# ============================================================================
# Board Commands
# ============================================================================

async def handle_board_get(args) -> None:
    """Handle board get subcommand."""
    client = await create_supabase_client()
    
    if args.id:
        if not validate_uuid(args.id):
            print(f"Error: Invalid UUID: {args.id}", file=sys.stderr)
            sys.exit(1)
        await get_board_by_id(client, args.id)
    elif args.name:
        await get_all_boards_by_name(client, args.name)
    elif args.all:
        await get_all_boards(client)
    else:
        print("Error: --id, --name, or --all is required", file=sys.stderr)
        sys.exit(1)


async def handle_board_add(args) -> None:
    """Handle board add subcommand."""
    client = await create_supabase_client()
    
    if not args.name:
        print("Error: --name is required", file=sys.stderr)
        sys.exit(1)
    board_id = str(uuid.uuid4())
    await upsert_board(client, board_id, args.name, args.description)


# ============================================================================
# School Class Commands
# ============================================================================

async def handle_class_get(args) -> None:
    """Handle class get subcommand."""
    client = await create_supabase_client()
    
    if args.id:
        if not validate_uuid(args.id):
            print(f"Error: Invalid UUID: {args.id}", file=sys.stderr)
            sys.exit(1)
        await get_school_class_by_id(client, args.id)
    elif args.board_id:
        if not validate_uuid(args.board_id):
            print(f"Error: Invalid board-id UUID: {args.board_id}", file=sys.stderr)
            sys.exit(1)
        await get_all_school_classes_by_board_id(client, args.board_id)
    elif args.board_name:
        await get_all_school_classes_by_board_name(client, args.board_name)
    elif args.name:
        await get_all_school_classes_by_name(client, args.name)
    elif args.all:
        await get_all_school_classes(client)
    else:
        print("Error: --id, --board-id, --board-name, --name, or --all is required", file=sys.stderr)
        sys.exit(1)


async def handle_class_add(args) -> None:
    """Handle class add subcommand."""
    client = await create_supabase_client()
    
    if not args.board_id:
        print("Error: --board-id is required", file=sys.stderr)
        sys.exit(1)
    if not args.name:
        print("Error: --name is required", file=sys.stderr)
        sys.exit(1)
    if not validate_uuid(args.board_id):
        print(f"Error: Invalid board-id UUID: {args.board_id}", file=sys.stderr)
        sys.exit(1)
    await upsert_school_class(client, args.name, args.board_id, args.position)


# ============================================================================
# Subject Commands
# ============================================================================

async def handle_subject_get(args) -> None:
    """Handle subject get subcommand."""
    client = await create_supabase_client()
    
    if args.id:
        if not validate_uuid(args.id):
            print(f"Error: Invalid UUID: {args.id}", file=sys.stderr)
            sys.exit(1)
        await get_subject_by_id(client, args.id)
    elif args.name:
        await get_all_subjects_by_name(client, args.name)
    elif args.all:
        await get_all_subjects(client)
    else:
        print("Error: --id, --name, or --all is required", file=sys.stderr)
        sys.exit(1)


async def handle_subject_add(args) -> None:
    """Handle subject add subcommand."""
    client = await create_supabase_client()
    
    if not args.id:
        print("Error: --id is required (subject ID)", file=sys.stderr)
        sys.exit(1)
    if not args.name:
        print("Error: --name is required", file=sys.stderr)
        sys.exit(1)
    if not validate_uuid(args.id):
        print(f"Error: Invalid UUID: {args.id}", file=sys.stderr)
        sys.exit(1)
    await upsert_subject(client, args.id, args.name, args.description)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Unified CLI for Knowledge Database (Boards, School Classes, Subjects)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="entity", help="Entity to manage")
    
    # -------------------------------------------------------------------------
    # Board subcommand
    # -------------------------------------------------------------------------
    board_parser = subparsers.add_parser("board", help="Manage boards")
    board_subparsers = board_parser.add_subparsers(dest="operation")
    
    # board get
    board_get = board_subparsers.add_parser("get", help="Get board(s)")
    board_get.add_argument("--id", type=str, help="Board UUID")
    board_get.add_argument("--name", type=str, help="Board name (search)")
    board_get.add_argument("--all", action="store_true", help="List all boards")
    
    # board add
    board_add = board_subparsers.add_parser("add", help="Add a new board")
    board_add.add_argument("--name", type=str, required=True, help="Board name")
    board_add.add_argument("--description", type=str, help="Board description")
    
    # -------------------------------------------------------------------------
    # Class subcommand
    # -------------------------------------------------------------------------
    class_parser = subparsers.add_parser("class", aliases=["school-class"], help="Manage school classes")
    class_subparsers = class_parser.add_subparsers(dest="operation")
    
    # class get
    class_get = class_subparsers.add_parser("get", help="Get school class(es)")
    class_get.add_argument("--id", type=str, help="School class UUID")
    class_get.add_argument("--name", type=str, help="School class name (search)")
    class_get.add_argument("--board-id", type=str, help="Board UUID")
    class_get.add_argument("--board-name", type=str, help="Board name (search)")
    class_get.add_argument("--all", action="store_true", help="List all school classes")
    
    # class add
    class_add = class_subparsers.add_parser("add", help="Add a new school class")
    class_add.add_argument("--board-id", type=str, required=True, help="Board UUID")
    class_add.add_argument("--name", type=str, required=True, help="School class name")
    class_add.add_argument("--position", type=int, help="Position/order of the class")
    
    # -------------------------------------------------------------------------
    # Subject subcommand
    # -------------------------------------------------------------------------
    subject_parser = subparsers.add_parser("subject", help="Manage subjects")
    subject_subparsers = subject_parser.add_subparsers(dest="operation")
    
    # subject get
    subject_get = subject_subparsers.add_parser("get", help="Get subject(s)")
    subject_get.add_argument("--id", type=str, help="Subject UUID")
    subject_get.add_argument("--name", type=str, help="Subject name (search)")
    subject_get.add_argument("--all", action="store_true", help="List all subjects")
    
    # subject add
    subject_add = subject_subparsers.add_parser("add", help="Add a new subject")
    subject_add.add_argument("--id", type=str, required=True, help="Subject UUID")
    subject_add.add_argument("--name", type=str, required=True, help="Subject name")
    subject_add.add_argument("--description", type=str, help="Subject description")
    
    args = parser.parse_args()
    
    if not args.entity:
        parser.print_help()
        sys.exit(1)
    
    if not getattr(args, "operation", None):
        if args.entity == "board":
            board_parser.print_help()
        elif args.entity in ("class", "school-class"):
            class_parser.print_help()
        elif args.entity == "subject":
            subject_parser.print_help()
        sys.exit(1)
    
    try:
        if args.entity == "board":
            if args.operation == "get":
                asyncio.run(handle_board_get(args))
            elif args.operation == "add":
                asyncio.run(handle_board_add(args))
        elif args.entity in ("class", "school-class"):
            if args.operation == "get":
                asyncio.run(handle_class_get(args))
            elif args.operation == "add":
                asyncio.run(handle_class_add(args))
        elif args.entity == "subject":
            if args.operation == "get":
                asyncio.run(handle_subject_get(args))
            elif args.operation == "add":
                asyncio.run(handle_subject_add(args))
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(130)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()







