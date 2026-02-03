import os
from prompts import NCERT_GEN
from agents import generate_concepts
from schemas import Chapter, save_csv

def test():
    print("Starting concept generation...")
    
    # CHANGE THESE VALUES TO SWITCH CLASS/CHAPTER:
    # 
    # For Class 10 Math Chapter 1: "Class_10", "jemh101.pdf"
    # For Class 10 Math Chapter 2: "Class_10", "jemh102.pdf"
    # For Class 11 Math Chapter 1: "Class_11", "kemh101.pdf"
    # For Class 9 Math Chapter 1:  "Class_09", "iemh101.pdf"
    
    class_folder = "test_client"        # ← CHANGE THIS
    pdf_filename = "ch01.pdf"     # ← CHANGE THIS
    
    pdf_path = os.path.join("helper", class_folder, pdf_filename)
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        print("Please run the NCERT downloader first: python helper/ncert_download.py")
        return
    
    print(f"Processing PDF: {pdf_path}")
    output : Chapter = generate_concepts(
        prompt = NCERT_GEN,
        pdf_path = pdf_path
        )
    print("Generation complete. Saving to CSV...")
    save_csv(output, "helper/data.csv", 1)
    print("Done!")
