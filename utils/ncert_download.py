"""
NCERT textbook downloader utility.
Downloads NCERT PDF textbooks from the official website.
"""

import os
import logging
import asyncio
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

# NCERT PDF base URLs
NCERT_BASE_URL = "https://ncert.nic.in/textbook"


async def download_ncert_pdf(
    class_num: int,
    subject: str,
    chapter_code: str,
    output_dir: Path
) -> Path:
    """
    Download an NCERT PDF chapter.
    
    Args:
        class_num: Class number (1-12)
        subject: Subject code (e.g., "Math", "Science")
        chapter_code: Chapter code (e.g., "jemh101" for class 10 math chapter 1)
        output_dir: Directory to save the downloaded PDF
    
    Returns:
        Path to the downloaded PDF file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    url = f"{NCERT_BASE_URL}/pdf/{chapter_code}.pdf"
    output_path = output_dir / f"{chapter_code}.pdf"
    
    if output_path.exists():
        logger.info(f"PDF already exists: {output_path}")
        return output_path
    
    async with httpx.AsyncClient() as client:
        logger.info(f"Downloading: {url}")
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        logger.info(f"Downloaded: {output_path}")
    
    return output_path


def download_ncert_pdf_sync(
    class_num: int,
    subject: str,
    chapter_code: str,
    output_dir: Path
) -> Path:
    """Synchronous wrapper for download_ncert_pdf."""
    return asyncio.run(download_ncert_pdf(class_num, subject, chapter_code, output_dir))
