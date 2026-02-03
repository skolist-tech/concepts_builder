"""
This agent takes a prompt and a pdf path as input.
It uses the prompt to generate concepts from the pdf.
It returns a Chapter object.
"""

import os
import logging

from google import genai
from google.genai import types

from schemas import Chapter

logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


async def generate_concepts(prompt: str, pdf_path: str) -> Chapter:
    """
    This function takes a prompt and a pdf path as input.
    It uses the prompt to generate concepts from the pdf.
    It returns a Chapter object.
    """
    with open(pdf_path, "rb") as f:
        part = types.Part.from_bytes(data=f.read(), mime_type="application/pdf")
        logger.info(f"PDF read successfully from path : {pdf_path}")

    responce = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, part],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Chapter,
        ),
    )

    logger.info("Response generated successfully")

    chapter: Chapter = responce.parsed
    logger.info("Chapter parsed successfully")
    logger.info(
        f"Generated Chapter: {chapter.name} with {len(chapter.topics)} topics, and {sum(len(topic.concepts) for topic in chapter.topics)} concepts."
    )
    return chapter
