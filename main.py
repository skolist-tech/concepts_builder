import os
import logging
import asyncio

import supabase
from dotenv import load_dotenv

from config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

load_dotenv()

from helper.test_script import test, process_chapter_for_solved_examples, process_chapter_for_exercise_questions
from helper.json_to_pdf import convert_all_json_to_pdf
from schemas.concept_schema import Chapter
from schemas.bank_questions.solved_bank_to_sql import upload_solved_bank_to_supabase
from schemas.chapter_to_sql import chapter_to_sql
from schemas.chapter_to_csv import csv_to_chapter
from schemas import load_solved_bank_json, load_exercise_bank_json, save_exercise_bank_pdf
from prompts.rbse import (
    MATHS_6_CORODOVA_PROMPT, 
    MATHS_6_CORODOVA_SOLVED_EG_PROMPT, 
    MATHS_6_CORODOVA_EXERCISE_PROMPT
)


PDF_FOLDER_PATH = "/home/purushottam/Desktop/startup_work/forks/platform_v1/concepts_builder/data/rbse/maths_6_corodova/"
CSV_OUTPUT_FOLDER_PATH = "/home/purushottam/Desktop/startup_work/forks/platform_v1/concepts_builder/data/rbse_output/maths_6_corodova/"

# List of specific chapters to process. If empty, all chapters will be processed.
# Example: ["01_knowing_our_numbers.pdf", "02_whole_numbers.pdf"]
CHAPTERS_TO_PROCESS = [
    "05_fractions.pdf",
    "13_perimeter_and_area.pdf"
]

chapter_pdf_path_list = [
    os.path.join(PDF_FOLDER_PATH, chapter) 
    for chapter in os.listdir(PDF_FOLDER_PATH) 
    if not chapter.startswith("index") and chapter.endswith(".pdf")
]

# if CHAPTERS_TO_PROCESS:
#     chapter_pdf_path_list = [
#         path for path in chapter_pdf_path_list 
#         if os.path.basename(path) in CHAPTERS_TO_PROCESS
#     ]


# async def main():
#     tasks = []
#     for chapter_pdf_path in chapter_pdf_path_list:
#         output_csv_path = os.path.join(
#             CSV_OUTPUT_FOLDER_PATH,
#             os.path.basename(chapter_pdf_path.replace(".pdf", "")) + "_concepts.csv"
#         )
#         logger.info(f"Appending chapter PDF: {chapter_pdf_path} to async tasks")
#         tasks.append(
#             test(
#                 chapter_pdf_path=chapter_pdf_path,
#                 prompt=MATHS_6_CORODOVA_PROMPT,
#                 output_csv_path=output_csv_path,
#             )
#         )
    
#     # Process all chapters concurrently
#     await asyncio.gather(*tasks)

async def main2():
    tasks = []
    for chapter_pdf_path in chapter_pdf_path_list:
        output_json_path = os.path.join(
            CSV_OUTPUT_FOLDER_PATH,
            os.path.basename(chapter_pdf_path.replace(".pdf", "")) + "_solved_examples.json"
        )
        concepts_csv_path = os.path.join(
            CSV_OUTPUT_FOLDER_PATH,
            os.path.basename(chapter_pdf_path.replace(".pdf", "")) + "_concepts.csv"
        )
        logger.info(f"Appending chapter PDF: {chapter_pdf_path} to async tasks for solved examples")
        tasks.append(
            process_chapter_for_solved_examples(
                chapter_pdf_path=chapter_pdf_path,
                prompt=MATHS_6_CORODOVA_SOLVED_EG_PROMPT,
                concepts_csv_path=concepts_csv_path,
                output_json_path=output_json_path
            )
        )
    await asyncio.gather(*tasks)

# async def main3():
#     await convert_all_json_to_pdf(input_dir=CSV_OUTPUT_FOLDER_PATH)

# async def main4():
#     sql_statements = []
#     for chapter_pdf_path in chapter_pdf_path_list:
#         chapter_name = os.path.basename(chapter_pdf_path.replace(".pdf", ""))
#         output_sql_path = os.path.join(
#             CSV_OUTPUT_FOLDER_PATH,
#             chapter_name + "_concepts.sql"
#         )
#         concepts_csv_path = os.path.join(
#             CSV_OUTPUT_FOLDER_PATH,
#             chapter_name + "_concepts.csv"
#         )
#         if not os.path.exists(concepts_csv_path):
#             logger.warning(f"Concepts CSV not found for {chapter_name} at {concepts_csv_path}. Skipping SQL generation.")
#             continue
#         chapter : Chapter = csv_to_chapter(concepts_csv_path)
#         logger.info(f"Generating SQL for chapter: {chapter_name}")
#         sql_statement = chapter_to_sql(
#             subject_id="11ea3956-d46e-4476-bb2c-a50afa027f5c",
#             chapter=chapter,
#             output_sql_path=output_sql_path,
#             position=chapter_name[:2]  # Assuming chapter names start with position like "01_Introduction"
#         )
#         logger.info(f"SQL saved at: {output_sql_path}")
#         sql_statements.extend(sql_statement)
#     with open(os.path.join(CSV_OUTPUT_FOLDER_PATH, "all_chapters_concepts.sql"), "w", encoding="utf-8") as f:
#         f.write("DO $$\n")
#         f.write("\tBEGIN\n")
#         f.write("\n".join(sql_statements))
#         f.write("\nEXCEPTION WHEN OTHERS THEN\n")
#         f.write("RAISE NOTICE 'An error occurred, rolling back automatically.';\n")
#         f.write("END $$\n")
#         logger.info(f"All chapters SQL statements saved to all_chapters_concepts.sql")

async def main5():
    """
    Generate and upload bank questions and bank question concept maps 
    from the solved examples JSON files directly to Supabase using async processing.
    """
    # Create Supabase client once
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL or SUPABASE_SERVICE_KEY not set.")
        return

    client = supabase.Client(supabase_url, supabase_key)

    # Subject ID for RBSE Maths 6 Corodova
    subject_id = "11ea3956-d46e-4476-bb2c-a50afa027f5c"
    
  
    async def process_chapter(chapter_pdf_path: str) -> tuple[str, dict]:
        """Process a single chapter asynchronously and upload to DB"""
        chapter_name = os.path.basename(chapter_pdf_path.replace(".pdf", ""))
        
        # Path to the solved examples JSON file
        solved_examples_json_path = os.path.join(
            CSV_OUTPUT_FOLDER_PATH,
            chapter_name + "_solved_examples.json"
        )
        
        # Check if the solved examples JSON file exists
        if not os.path.exists(solved_examples_json_path):
            logger.warning(f"Solved examples JSON not found for {chapter_name} at {solved_examples_json_path}. Skipping.")
            return chapter_name, {}
        
        try:
            # Load the solved examples bank from JSON (run in thread pool)
            logger.info(f"Loading solved examples from: {solved_examples_json_path}")
            
            def _load_json():
                return load_solved_bank_json(solved_examples_json_path)
            
            solved_bank = await asyncio.get_event_loop().run_in_executor(None, _load_json)
            
            # Upload to Supabase
            logger.info(f"Processing chapter: {chapter_name}...")
            stats = await upload_solved_bank_to_supabase(
                client=client,
                solved_bank=solved_bank,
                subject_id=subject_id
            )
            
            logger.info(
                f"Completed {chapter_name}: "
                f"Questions [Found: {stats['questions_total']}, Upserted: {stats['questions_upserted']}], "
                f"Maps [Found: {stats['maps_total']}, Upserted: {stats['maps_upserted']}]"
            )
            return chapter_name, stats
            
        except Exception as e:
            logger.error(f"Error processing chapter {chapter_name}: {e}")
            return chapter_name, {}
    
    # Process all chapters with limited concurrency using a Semaphore
    # Limit to 1 concurrent upload (sequential) to avoid server disconnects
    semaphore = asyncio.Semaphore(1)

    async def process_with_semaphore(chapter_pdf_path):
        async with semaphore:
            return await process_chapter(chapter_pdf_path)

    logger.info(f"Starting concurrent processing of {len(chapter_pdf_path_list)} chapters (limit 3)")
    tasks = [process_with_semaphore(chapter_pdf_path) for chapter_pdf_path in chapter_pdf_path_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Summary
    successful_chapters = 0
    total_stats = {
        "questions_total": 0,
        "questions_upserted": 0,
        "maps_total": 0,
        "maps_upserted": 0
    }
    
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Task failed with exception: {result}")
            continue
        
        chapter_name, stats = result
        if stats:
            successful_chapters += 1
            total_stats["questions_total"] += stats.get("questions_total", 0)
            total_stats["questions_upserted"] += stats.get("questions_upserted", 0)
            total_stats["maps_total"] += stats.get("maps_total", 0)
            total_stats["maps_upserted"] += stats.get("maps_upserted", 0)
            
    logger.info("="*50)
    logger.info(f"FINAL SUBMISSION REPORT")
    logger.info("="*50)
    logger.info(f"Chapters Processed: {successful_chapters}/{len(chapter_pdf_path_list)}")
    logger.info(f"Total Questions    : {total_stats['questions_total']} found -> {total_stats['questions_upserted']} upserted")
    logger.info(f"Total Concept Maps : {total_stats['maps_total']} found -> {total_stats['maps_upserted']} upserted")
    logger.info("="*50)

async def main6():
    tasks = []
    for chapter_pdf_path in chapter_pdf_path_list:
        output_json_path = os.path.join(
            CSV_OUTPUT_FOLDER_PATH,
            os.path.basename(chapter_pdf_path.replace(".pdf", "")) + "_exercise_questions.json"
        )
        concepts_csv_path = os.path.join(
            CSV_OUTPUT_FOLDER_PATH,
            os.path.basename(chapter_pdf_path.replace(".pdf", "")) + "_concepts.csv"
        )
        logger.info(f"Appending chapter PDF: {chapter_pdf_path} to async tasks for exercise questions")
        tasks.append(
            process_chapter_for_exercise_questions(
                chapter_pdf_path=chapter_pdf_path,
                prompt=MATHS_6_CORODOVA_EXERCISE_PROMPT,
                concepts_csv_path=concepts_csv_path,
                output_json_path=output_json_path
            )
        )
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Task failed with exception: {result}")

# if __name__ == "__main__":
#     asyncio.run(main6())

async def main7():
    tasks = []
    logger.info(f"Generating PDFs for {len(chapter_pdf_path_list)} chapters")
    
    async def process_pdf_generation(chapter_pdf_path):
        chapter_name = os.path.basename(chapter_pdf_path.replace(".pdf", ""))
        json_path = os.path.join(
            CSV_OUTPUT_FOLDER_PATH,
            chapter_name + "_exercise_questions.json"
        )
        pdf_path = os.path.join(
            CSV_OUTPUT_FOLDER_PATH,
            chapter_name + "_exercise_questions.pdf"
        )
        
        if not os.path.exists(json_path):
            logger.warning(f"JSON not found for {chapter_name} at {json_path}. Skipping PDF generation.")
            return

        try:
            logger.info(f"Generating PDF for {chapter_name}...")
            # Run json loading in executor to avoid blocking if it's slow/sync (though it's fast usually)
            # Actually load_exercise_bank_json is sync, so we can run it directly or in executor.
            # But since it reads file, executor is better.
            bank = await asyncio.to_thread(load_exercise_bank_json, json_path)
            
            await save_exercise_bank_pdf(bank, pdf_path)
            logger.info(f"Successfully generated PDF for {chapter_name}")
        except Exception as e:
            logger.error(f"Failed to generate PDF for {chapter_name}: {e}")

    for chapter_pdf_path in chapter_pdf_path_list:
        tasks.append(process_pdf_generation(chapter_pdf_path))
    
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main7())

