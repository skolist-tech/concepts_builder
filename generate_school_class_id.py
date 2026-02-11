#!/usr/bin/env python
"""
Generate Class ID CLI

Generates a deterministic school_class UUID from board_id and school_class_name.

Usage:
    python generate_school_class_id.py --board_id <uuid> --school_class_name "Class 6"
"""

import argparse
import sys

from utils.uuid_generator import generate_school_class_id, validate_uuid


def main():
    parser = argparse.ArgumentParser(
        description="Generate a deterministic school_class UUID from board_id and school_class_name"
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
    
    args = parser.parse_args()
    
    if not validate_uuid(args.board_id):
        print(f"Error: Invalid board_id UUID: {args.board_id}", file=sys.stderr)
        sys.exit(1)
    
    school_class_id = generate_school_class_id(args.board_id, args.school_class_name)
    print(school_class_id)


if __name__ == "__main__":
    main()
