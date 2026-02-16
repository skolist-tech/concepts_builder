import sys
import logging

from supabase import AsyncClient

from utils.uuid_generator import generate_school_class_id

logger = logging.getLogger(__name__)

async def get_school_class_by_id(client: AsyncClient, school_class_id: str) -> None:
    """Fetch school class details from Supabase."""
    response = await client.table("school_classes").select("*, boards(name)").eq("id", school_class_id).execute()
    
    if response.data and len(response.data) > 0:
        school_class = response.data[0]
        if not school_class:
            logger.error(f"School class not found: {school_class_id}")
            sys.exit(1)
        
        board_name = school_class.get("boards", {}).get("name", "Unknown") if school_class.get("boards") else "Unknown"
        
        print()
        print("=" * 50)
        print("School Class Details")
        print("=" * 50)
        print(f"Class ID:       {school_class['id']}")
        print(f"Class Name:     {school_class['name']}")
        print(f"Board ID:       {school_class['board_id']}")
        print(f"Board Name:     {board_name}")
        print(f"Position:       {school_class.get('position', 'N/A')}")
        print(f"Created At:     {school_class.get('created_at', 'N/A')}")
        print(f"Updated At:     {school_class.get('updated_at', 'N/A')}")
        print("=" * 50)
    else:
        logger.error(f"School class not found: {school_class_id}")
        sys.exit(1)
    return None

async def get_all_school_classes(client: AsyncClient) -> None:
    """Fetch all school classes from Supabase."""
    response = await client.table("school_classes").select("*").order("name").execute()
    school_classes = response.data if response.data else []

    title = "All School Classes"
        
    if not school_classes:
        print(f"No school classes found.")
        return
        
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)
    print(f"{'ID':<40} {'Name':<20} {'Board ID':<20}")
    print("-" * 80)
    for school_class in school_classes:
        print(f"{school_class['id']:<40} {school_class['name']:<20} {school_class['board_id']:<20}")
    print("=" * 80)
    print(f"Total: {len(school_classes)} school class(es)")
    return None

async def get_all_school_classes_by_name(client: AsyncClient, name: str) -> None:
    """Fetch school classes by name (case-insensitive)."""
    response = await client.table("school_classes").select("*, boards(name)").ilike("name", f"%{name}%").order("name").execute()
    school_classes = response.data if response.data else []

    title = f"School Classes matching '{name}'"
        
    if not school_classes:
        print(f"No school classes found matching: {name}.")
        return
        
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)
    print(f"{'ID':<40} {'Name':<20} {'Board':<20} {'Position':<10}")
    print("-" * 100)
    for sc in school_classes:
        board_name = sc.get("boards", {}).get("name", "Unknown") if sc.get("boards") else "Unknown"
        print(f"{sc['id']:<40} {sc['name']:<20} {board_name:<20} {sc.get('position', 'N/A'):<10}")
    print("=" * 100)
    print(f"Total: {len(school_classes)} school class(es)")
    return None

async def get_all_school_classes_by_board_id(client: AsyncClient, board_id: str) -> None:
    """Fetch school classes by board ID."""
    response = await client.table("school_classes").select("*, boards(name)").eq("board_id", board_id).order("position").execute()
    school_classes = response.data if response.data else []

    board_name = "Unknown"
    if school_classes and school_classes[0].get("boards"):
        board_name = school_classes[0]["boards"].get("name", "Unknown")
    
    title = f"School Classes for Board: {board_name}"
        
    if not school_classes:
        print(f"No school classes found for board ID: {board_id}.")
        return
        
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)
    print(f"{'ID':<40} {'Name':<20} {'Board':<20} {'Position':<10}")
    print("-" * 100)
    for sc in school_classes:
        b_name = sc.get("boards", {}).get("name", "Unknown") if sc.get("boards") else "Unknown"
        print(f"{sc['id']:<40} {sc['name']:<20} {b_name:<20} {sc.get('position', 'N/A'):<10}")
    print("=" * 100)
    print(f"Total: {len(school_classes)} school class(es)")
    return None

async def get_all_school_classes_by_board_name(client: AsyncClient, board_name: str) -> None:
    """Fetch school classes by board name (case-insensitive)."""
    # First find matching boards, then get their school classes
    boards_response = await client.table("boards").select("id, name").ilike("name", f"%{board_name}%").execute()
    boards = boards_response.data if boards_response.data else []
    
    if not boards:
        print(f"No boards found matching: {board_name}.")
        return
    
    board_ids = [b["id"] for b in boards]
    response = await client.table("school_classes").select("*, boards(name)").in_("board_id", board_ids).order("position").execute()
    school_classes = response.data if response.data else []

    title = f"School Classes for Boards matching '{board_name}'"
        
    if not school_classes:
        print(f"No school classes found for boards matching: {board_name}.")
        return
        
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)
    print(f"{'ID':<40} {'Name':<20} {'Board':<20} {'Position':<10}")
    print("-" * 100)
    for sc in school_classes:
        b_name = sc.get("boards", {}).get("name", "Unknown") if sc.get("boards") else "Unknown"
        print(f"{sc['id']:<40} {sc['name']:<20} {b_name:<20} {sc.get('position', 'N/A'):<10}")
    print("=" * 100)
    print(f"Total: {len(school_classes)} school class(es)")
    return None

async def upsert_school_class(client: AsyncClient, name: str, board_id: str, position: int | None = None) -> None:
    """Upsert school class record to Supabase."""
    school_class_id = generate_school_class_id(board_id, name)
    
    school_class_record = {
        "id": school_class_id,
        "name": name,
        "board_id": board_id,
    }
    if position is not None:
        school_class_record["position"] = position
    
    response = await client.table("school_classes").upsert(school_class_record).execute()
    result = response.data[0] if response.data else school_class_record
    if not result:
        logger.error(f"Failed to upsert school class: {name} (id: {school_class_id})")
        sys.exit(1)
    
    # Get board name for display
    board_response = await client.table("boards").select("name").eq("id", board_id).execute()
    board_name = board_response.data[0]["name"] if board_response.data else "Unknown"
    
    # Print results
    print()
    print("=" * 50)
    print("School Class Created Successfully")
    print("=" * 50)
    print(f"Board ID:       {board_id}")
    print(f"Board Name:     {board_name}")
    print(f"Class Name:     {name}")
    print(f"Class ID:       {school_class_id}")
    if position is not None:
        print(f"Position:       {position}")
    print("=" * 50)
    
    logger.info(f"Created school class: {name} (id: {school_class_id}) for board: {board_name}")
    return None