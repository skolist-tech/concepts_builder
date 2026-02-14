#!/usr/bin/env python
"""
Subject CLI

Manage subject records in Supabase.

Usage:
    # Add a new subject
    python subject.py --add --school-class-id <uuid> --name "Mathematics"

    # Get a specific subject
    python subject.py --get --subject-id <uuid>

    # List all subjects for a school class
    python subject.py --get --school-class-id <uuid>
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


async def get_subject(client: supabase.Client, subject_id: str) -> dict | None:
    """Fetch a single subject by ID with school_class and board info."""
    def _fetch():
        return client.table("subjects").select("*, school_classes(name, board_id, boards(name))").eq("id", subject_id).execute()
    
    result = await asyncio.get_event_loop().run_in_executor(None, _fetch)
    
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


async def get_subjects_by_school_class(client: supabase.Client, school_class_id: str) -> list[dict]:
    """Fetch all subjects for a school_class."""
    def _fetch():
        return client.table("subjects").select("*").eq("school_class_id", school_class_id).order("name").execute()
    
    result = await asyncio.get_event_loop().run_in_executor(None, _fetch)
    return result.data if result.data else []


async def get_subjects_by_name(client: supabase.Client, name: str) -> list[dict]:
    """Fetch subjects by name (case-insensitive)."""
    def _fetch():
        return client.table("subjects").select("*, school_classes(name, board_id, boards(name))").ilike("name", f"%{name}%").order("name").execute()
    
    result = await asyncio.get_event_loop().run_in_executor(None, _fetch)
    return result.data if result.data else []


async def get_all_subjects(client: supabase.Client) -> list[dict]:
    """Fetch all subjects from Supabase."""
    def _fetch():
        return client.table("subjects").select("*, school_classes(name, board_id, boards(name))").order("name").execute()
    
    result = await asyncio.get_event_loop().run_in_executor(None, _fetch)
    return result.data if result.data else []


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


async def add_subject_async(school_class_id: str, subject_name: str) -> None:
    """Add a new subject."""
    client = create_supabase_client()
    
    school_class_data = await get_school_class(client, school_class_id)
    if not school_class_data:
        logger.error(f"School class not found: {school_class_id}")
        sys.exit(1)
    
    school_class_name = school_class_data.get("name", "Unknown")
    board_name = school_class_data.get("boards", {}).get("name", "Unknown") if school_class_data.get("boards") else "Unknown"
    board_id = school_class_data.get("board_id", "Unknown")
    
    subject_id = generate_subject_id(school_class_id, subject_name)
    await upsert_subject(client, subject_id, subject_name, school_class_id)
    
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


async def get_subject_async(subject_id: str | None, school_class_id: str | None, name: str | None, all_subjects: bool) -> None:
    """Get subject(s) from database."""
    client = create_supabase_client()
    
    if all_subjects or school_class_id or name:
        if all_subjects:
            subjects = await get_all_subjects(client)
            title = "All Subjects"
        elif name:
            subjects = await get_subjects_by_name(client, name)
            title = f"Subjects matching '{name}'"
        else:
            # Verify school_class exists
            school_class = await get_school_class(client, school_class_id)
            if not school_class:
                logger.error(f"School class not found: {school_class_id}")
                sys.exit(1)
            school_class_name = school_class.get("name", "Unknown")
            board_name = school_class.get("boards", {}).get("name", "Unknown") if school_class.get("boards") else "Unknown"
            subjects = await get_subjects_by_school_class(client, school_class_id)
            title = f"Subjects for {school_class_name} ({board_name})"
        
        if not subjects:
            print(f"No subjects found{' matching: ' + name if name else ''}.")
            return
        
        print()
        print("=" * 110)
        print(title)
        print("=" * 110)
        print(f"{'ID':<40} {'Name':<25} {'Class':<20} {'Board':<20}")
        print("-" * 110)
        for subj in subjects:
            sc_data = subj.get("school_classes", {}) or {}
            sc_name = sc_data.get("name", "Unknown") if sc_data else "Unknown"
            b_name = sc_data.get("boards", {}).get("name", "Unknown") if sc_data and sc_data.get("boards") else "Unknown"
            print(f"{subj['id']:<40} {subj['name']:<25} {sc_name:<20} {b_name:<20}")
        print("=" * 110)
        print(f"Total: {len(subjects)} subject(s)")
    
    else:
        subject = await get_subject(client, subject_id)
        
        if not subject:
            logger.error(f"Subject not found: {subject_id}")
            sys.exit(1)
        
        school_class_data = subject.get("school_classes", {}) or {}
        school_class_name = school_class_data.get("name", "Unknown")
        board_id = school_class_data.get("board_id", "Unknown")
        board_name = school_class_data.get("boards", {}).get("name", "Unknown") if school_class_data.get("boards") else "Unknown"
        
        print()
        print("=" * 50)
        print("Subject Details")
        print("=" * 50)
        print(f"Subject ID:         {subject['id']}")
        print(f"Subject Name:       {subject['name']}")
        print(f"School Class ID:    {subject['school_class_id']}")
        print(f"School Class Name:  {school_class_name}")
        print(f"Board ID:           {board_id}")
        print(f"Board Name:         {board_name}")
        print(f"Created At:         {subject.get('created_at', 'N/A')}")
        print(f"Updated At:         {subject.get('updated_at', 'N/A')}")
        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Manage subject records in Supabase"
    )
    
    # Operation flags (mutually exclusive)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument(
        "--add",
        action="store_true",
        help="Add a new subject"
    )
    operation.add_argument(
        "--get",
        action="store_true",
        help="Get subject(s) from database"
    )
    
    # Common arguments
    parser.add_argument(
        "--school-class-id",
        type=str,
        help="School class UUID (required for --add, optional for --get to list all subjects)"
    )
    
    # Add arguments / Get by name
    parser.add_argument(
        "--name",
        type=str,
        help="Subject name (required for --add, optional for --get to search by name)"
    )
    
    # Get arguments
    parser.add_argument(
        "--subject-id",
        type=str,
        help="Subject UUID to fetch (for --get)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="List all subjects (for --get)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.add:
            if not args.school_class_id:
                parser.error("--school-class-id is required when using --add")
            if not args.name:
                parser.error("--name is required when using --add")
            
            if not validate_uuid(args.school_class_id):
                print(f"Error: Invalid school-class-id UUID: {args.school_class_id}", file=sys.stderr)
                sys.exit(1)
            
            asyncio.run(add_subject_async(args.school_class_id, args.name))
        
        elif args.get:
            if not args.subject_id and not args.school_class_id and not args.name and not args.all:
                parser.error("--subject-id, --school-class-id, --name, or --all is required when using --get")
            
            if args.subject_id and not validate_uuid(args.subject_id):
                print(f"Error: Invalid subject-id UUID: {args.subject_id}", file=sys.stderr)
                sys.exit(1)
            
            if args.school_class_id and not validate_uuid(args.school_class_id):
                print(f"Error: Invalid school-class-id UUID: {args.school_class_id}", file=sys.stderr)
                sys.exit(1)
            
            asyncio.run(get_subject_async(args.subject_id, args.school_class_id, args.name, args.all))
    
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
