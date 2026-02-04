"""
This agent takes a prompt and a pdf path as input.
It uses the prompt to generate Exercise Questions from the pdf mapped to the concepts form the list provided.
It returns a ExerciseQuestionsBank object.
"""

import os
import logging

from google import genai
from google.genai import types

from schemas import ExerciseQuestionsBank

logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_exercise_questions(prompt: str, pdf_path: str, concepts_list : list[str]) -> ExerciseQuestionsBank:
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
            response_schema=ExerciseQuestionsBank,
        ),
    )
    logger.info("Response generated successfully")
    exercise_questions_bank: ExerciseQuestionsBank = responce.parsed
    
    if exercise_questions_bank is None:
        logger.error(f"Failed to parse response for {pdf_path}. Raw response text: {responce.text}")
        raise ValueError(f"Failed to parse response from Gemini for {pdf_path}. The model might have been blocked or returned invalid JSON.")

    logger.info("ExerciseQuestionsBank parsed successfully")
    logger.info(
        f"Generated ExerciseQuestionsBank with {len(exercise_questions_bank.exercise_questions)} exercise questions for chapter : {exercise_questions_bank.chapter_name}.")
    return exercise_questions_bank
