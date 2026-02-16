import sys
import logging

from supabase import AsyncClient

logger = logging.getLogger(__name__)

async def get_board_by_id(client: AsyncClient, board_id: str) -> None:
    """Fetch board details from Supabase."""
    response = await client.table("boards").select("*").eq("id", board_id).execute()
    
    if response.data and len(response.data) > 0:
        board = response.data[0]
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
    return None

async def get_all_boards(client: AsyncClient) -> None:
    """Fetch all boards from Supabase."""
    response = await client.table("boards").select("*").order("name").execute()
    boards = response.data if response.data else []

    title = "All Boards"
        
    if not boards:
        print(f"No boards found.")
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
    return None

async def get_all_boards_by_name(client: AsyncClient, name: str) -> None:
    """Fetch boards by name (case-insensitive)."""
    response = await client.table("boards").select("*").ilike("name", f"%{name}%").order("name").execute()
    boards = response.data if response.data else []

    title = f"Boards matching '{name}'"
        
    if not boards:
        print(f"No boards found matching: {name}.")
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
    return None

async def upsert_board(client: AsyncClient, board_id: str, name: str, description: str | None = None) -> None:
    """Upsert board record to Supabase."""
    board_record = {
        "id": board_id,
        "name": name,
    }
    if description:
        board_record["description"] = description
    
    response = await client.table("boards").upsert(board_record).execute()
    result = response.data[0] if response.data else board_record
    if not result:
        logger.error(f"Failed to upsert board: {name} (id: {board_id})")
        sys.exit(1)
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
    return None