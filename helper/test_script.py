from prompts import NCERT_CLASS_10_Maths
from agents import generate_concepts
from schemas import Chapter, save_csv

def test():
    print("Starting concept generation...")
    output : Chapter = generate_concepts(
        prompt = NCERT_CLASS_10_Maths,
        pdf_path = "/home/purushottam/Desktop/startup_work/forks/concepts_builder/data/ncert/NCERT_Maths/Class_11/kemh101.pdf"
        )
    print("Generation complete. Saving to CSV...")
    save_csv(output, "helper/data.csv", 1)
    print("Done!")
