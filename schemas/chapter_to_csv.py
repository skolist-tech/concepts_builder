from schemas.concept_schema import Chapter

import csv

def create_csv(chapter: Chapter, position: int):
    headers = [
        "concept_name",
        "concept_description",
        "concept_page_number",
        "topic_name",
        "topic_description",
        "topic_position",
        "chapter_name",
        "chapter_description",
        "chapter_position",
    ]
    
    rows = []
    for topic in chapter.topics:
        for concept in topic.concepts:
            rows.append([
                concept.name,
                concept.description,
                concept.page_number,
                topic.name,
                topic.description,
                topic.position,
                chapter.name,
                chapter.description,
                position,
            ])
    return headers, rows

def save_csv(chapter: Chapter, path: str, position: int):
    headers, rows = create_csv(chapter, position)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    