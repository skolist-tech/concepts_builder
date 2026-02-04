import os
import logging

import csv

from schemas.concept_schema import Chapter, Topic, Concept

logger = logging.getLogger(__name__)

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
            rows.append(
                [
                    concept.name,
                    concept.description,
                    concept.page_number,
                    topic.name,
                    topic.description,
                    topic.position,
                    chapter.name,
                    chapter.description,
                    position,
                ]
            )
    logger.info(f"CSV data created with {len(rows)} rows, for chapter {chapter.name}")
    return headers, rows


def save_csv(chapter: Chapter, path: str, position: int):
    folder = os.path.dirname(path)
    if not os.path.exists(folder):
        os.makedirs(folder)
        logger.info(f"Created directory: {folder}")

    headers, rows = create_csv(chapter, position)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    logger.info(f"CSV saved successfully at: {path}")

def csv_to_chapter(csv_path: str) -> Chapter:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        topics_dict = {}
        for row in reader:
            topic_name = row["topic_name"]
            if topic_name not in topics_dict:
                topics_dict[topic_name] = {
                    "name": topic_name,
                    "description": row["topic_description"],
                    "concepts": [],
                    "position": int(row["topic_position"]),
                }
            concept = {
                "name": row["concept_name"],
                "description": row["concept_description"],
                "page_number": int(row["concept_page_number"]),
            }
            topics_dict[topic_name]["concepts"].append(concept)

        topics = []
        for topic_data in topics_dict.values():
            topic = Topic(
                name=topic_data["name"],
                description=topic_data["description"],
                concepts=[
                    Concept(
                        name=concept["name"],
                        description=concept["description"],
                        page_number=concept["page_number"],
                    )
                    for concept in topic_data["concepts"]
                ],
                position=topic_data["position"],
            )
            topics.append(topic)

        chapter = Chapter(
            name=row["chapter_name"],
            description=row["chapter_description"],
            topics=topics,
        )
        return chapter