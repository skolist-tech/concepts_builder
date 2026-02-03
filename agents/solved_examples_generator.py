"""
This agent takes a prompt and a pdf path as input.
It uses the prompt to generate Solved Examples from the pdf mapped to the concepts form the list provided.
It returns a SolvedExamplesBank object.
"""

import os
import logging

from google import genai
from google.genai import types

from schemas import SolvedExamplesBank

logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_solved_examples(prompt: str, pdf_path: str, concepts_list : list[str]) -> SolvedExamplesBank:
    if not concepts_list:
        raise ValueError("concepts_list cannot be empty.")
    if not prompt:
        raise ValueError("prompt cannot be empty.")
    if not pdf_path:
        raise ValueError("pdf_path cannot be empty.")
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")
    
    with open(pdf_path, "rb") as f:
        part = types.Part.from_bytes(data=f.read(), mime_type="application/pdf")
        logger.info(f"PDF read successfully from path : {pdf_path}")
    
    # Format concepts list to include in the prompt
    concepts_text = "\n\nCONCEPTS LIST:\n" + "\n".join(f"- {concept}" for concept in concepts_list)
    full_prompt = prompt + concepts_text
    
    responce = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=[full_prompt, part],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SolvedExamplesBank,
        ),
    )
    logger.info("Response generated successfully")
    solved_examples_bank: SolvedExamplesBank = responce.parsed
    logger.info("SolvedExamplesBank parsed successfully")
    logger.info(
        f"Generated SolvedExamplesBank with {len(solved_examples_bank.solved_examples_questions)} solved examples questions for chapter : {solved_examples_bank.chapter_name}.")
    return solved_examples_bank