import os
import logging
import asyncio

from dotenv import load_dotenv

from config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

load_dotenv()

from helper.test_script import test, process_chapter_for_solved_examples
from helper.json_to_pdf import convert_all_json_to_pdf

from prompts.rbse import MATHS_6_CORODOVA_PROMPT, MATHS_6_CORODOVA_SOLVED_EG_PROMPT

PDF_FOLDER_PATH = "/home/purushottam/Desktop/startup_work/forks/platform_v1/concepts_builder/data/rbse/maths_6_corodova/"
CSV_OUTPUT_FOLDER_PATH = "/home/purushottam/Desktop/startup_work/forks/platform_v1/concepts_builder/data/rbse_output/maths_6_corodova/"

chapter_pdf_path_list = [os.path.join(PDF_FOLDER_PATH, chapter) for chapter in os.listdir(PDF_FOLDER_PATH) if not chapter.startswith("index") and chapter.endswith(".pdf")]


async def main():
    tasks = []
    for chapter_pdf_path in chapter_pdf_path_list:
        output_csv_path = os.path.join(
            CSV_OUTPUT_FOLDER_PATH,
            os.path.basename(chapter_pdf_path.replace(".pdf", "")) + "_concepts.csv"
        )
        logger.info(f"Appending chapter PDF: {chapter_pdf_path} to async tasks")
        tasks.append(
            test(
                chapter_pdf_path=chapter_pdf_path,
                prompt=MATHS_6_CORODOVA_PROMPT,
                output_csv_path=output_csv_path,
            )
        )
    
    # Process all chapters concurrently
    await asyncio.gather(*tasks)

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

async def main3():
    await convert_all_json_to_pdf(input_dir=CSV_OUTPUT_FOLDER_PATH)
if __name__ == "__main__":
    asyncio.run(main3())
