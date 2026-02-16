import sys
import logging

from supabase import AsyncClient

logger = logging.getLogger(__name__)

async def get_subject_by_id(client: AsyncClient, subject_id: str) -> None:
    """Fetch subject details from Supabase."""
    response = await client.table("subjects").select("*").eq("id", subject_id).execute()
    
    if response.data and len(response.data) > 0:
        subject = response.data[0]
        if not subject:
            logger.error(f"Subject not found: {subject_id}")
            sys.exit(1)
        
        print()
        print("=" * 50)
        print("Subject Details")
        print("=" * 50)
        print(f"Subject ID:     {subject['id']}")
        print(f"Subject Name:   {subject['name']}")
        if subject.get("description"):
            print(f"Description:    {subject['description']}")
        print(f"Created At:    {subject.get('created_at', 'N/A')}")
        print(f"Updated At:    {subject.get('updated_at', 'N/A')}")
        print("=" * 50)
    return None

async def get_all_subjects(client: AsyncClient) -> None:
    """Fetch all subjects from Supabase."""
    response = await client.table("subjects").select("*").order("name").execute()
    subjects = response.data if response.data else []

    title = "All Subjects"
        
    if not subjects:
        print(f"No subjects found.")
        return
        
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)
    print(f"{'ID':<40} {'Name':<20} {'Description':<20}")
    print("-" * 80)
    for subject in subjects:
        desc = subject.get("description", "") or ""
        desc = desc[:17] + "..." if len(desc) > 20 else desc
        print(f"{subject['id']:<40} {subject['name']:<20} {desc:<20}")
    print("=" * 80)
    print(f"Total: {len(subjects)} subject(s)")
    return None

async def get_all_subjects_by_name(client: AsyncClient, name: str) -> None:
    """Fetch subjects by name (case-insensitive)."""
    response = await client.table("subjects").select("*").ilike("name", f"%{name}%").order("name").execute()
    subjects = response.data if response.data else []

    title = f"Subjects matching '{name}'"
        
    if not subjects:
        print(f"No subjects found matching: {name}.")
        return
        
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)
    print(f"{'ID':<40} {'Name':<20} {'Description':<20}")
    print("-" * 80)
    for subject in subjects:
        desc = subject.get("description", "") or ""
        desc = desc[:17] + "..." if len(desc) > 20 else desc
        print(f"{subject['id']:<40} {subject['name']:<20} {desc:<20}")
    print("=" * 80)
    print(f"Total: {len(subjects)} subject(s)")
    return None

async def upsert_subject(client: AsyncClient, subject_id: str, name: str, description: str | None = None) -> None:
    """Upsert subject record to Supabase."""
    subject_record = {
        "id": subject_id,
        "name": name,
        "description": description,
    }
    
    response = await client.table("subjects").upsert(subject_record).execute()
    result = response.data[0] if response.data else subject_record
    if not result:
        logger.error(f"Failed to upsert subject: {name} (id: {subject_id})")
        sys.exit(1)
    
    # Print results
    print()
    print("=" * 50)
    print("Subject Upserted Successfully")
    print("=" * 50)
    print(f"Subject ID:     {subject_id}")
    print(f"Subject Name:   {name}")
    if description:
        print(f"Description:    {description}")
    print("=" * 50)

    logger.info(f"Upserted subject: {name} (id: {subject_id})")
    return None

