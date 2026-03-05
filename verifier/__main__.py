"""
Allow running the verifier package as a module.

Usage:
    python -m verifier --input_dir <directory_path> --check-chapters
    python -m verifier --input_dir <directory_path> --check-concepts
    python -m verifier --input_dir <directory_path> --check-conventions
"""

from verifier.cli import main

if __name__ == "__main__":
    main()
