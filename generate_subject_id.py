#!/usr/bin/env python
"""
Generate Subject ID CLI

Generates a deterministic subject UUID from school_class_id and subject_name.

Usage:
    python generate_subject_id.py --school_class_id <uuid> --subject_name "Mathematics"
"""

import argparse
import sys

from utils.uuid_generator import generate_subject_id, validate_uuid


def main():
    parser = argparse.ArgumentParser(
        description="Generate a deterministic subject UUID from school_class_id and subject_name"
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
    
    subject_id = generate_subject_id(args.school_class_id, args.subject_name)
    print(subject_id)


if __name__ == "__main__":
    main()
