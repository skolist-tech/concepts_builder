import os
import logging

import uuid6

from schemas.concept_schema import Chapter

logger = logging.getLogger(__name__)


def escape_sql_string(value: str) -> str:
    """
    Escape a string for safe inclusion in a PostgreSQL SQL statement.
    Escapes single quotes by doubling them.
    
    Args:
        value: The string value to escape.
        
    Returns:
        The escaped string safe for SQL insertion.
    """
    if value is None:
        return ""
    return value.replace("'", "''")

def chapter_to_sql(subject_id: str, chapter: Chapter, output_sql_path : str, position : int = None) -> str:
    """
    Convert a Chapter object to SQL insert statements.

    Args:
        chapter (Chapter): The chapter object to convert.
        subject_id (str): The subject ID to associate with the chapter.
        output_sql_path (str): The file path to save the SQL statements.
        position (int, optional): The position of the chapter in the subject/course. Defaults to None.

    Returns:
        str: SQL insert statements as a string.
    """
    if not subject_id:
        raise ValueError("subject_id cannot be empty.")
    if not chapter:
        raise ValueError("chapter cannot be empty.")
    if not output_sql_path:
        raise ValueError("output_sql_path cannot be empty.")
    try:
        if not os.path.exists(os.path.dirname(output_sql_path)):
            os.makedirs(os.path.dirname(output_sql_path))
            logger.info(f"Created directory for SQL output: {os.path.dirname(output_sql_path)}")
    except Exception as e:
        logger.error(f"Error creating directory for SQL output: {e}")
        raise e
    if not chapter.name:
        raise ValueError("chapter.name cannot be empty.")
    if not chapter.topics:
        raise ValueError("chapter.topics cannot be empty.")
    for topic in chapter.topics:
        if not topic.name:
            raise ValueError("topic.name cannot be empty.")
        if not topic.position:
            raise ValueError("topic.position cannot be empty.")
        if not topic.concepts:
            raise ValueError("topic.concepts cannot be empty.")
        for concept in topic.concepts:
            if not concept.name:
                raise ValueError("concept.name cannot be empty.")
            if not concept.page_number:
                raise ValueError("concept.page_number cannot be empty.")
        

    sql_statements = []
    chapter_id = str(uuid6.uuid7())
    chapter_name = escape_sql_string(chapter.name)
    chapter_description = escape_sql_string(chapter.description)
    chapter_sql = f"INSERT INTO chapters (id, name, description, subject_id, position) VALUES ('{chapter_id}', '{chapter_name}', '{chapter_description}', '{subject_id}', {position});"
    sql_statements.append(chapter_sql)

    for topic in chapter.topics:
        topic_id = str(uuid6.uuid7())
        topic_name = escape_sql_string(topic.name)
        topic_description = escape_sql_string(topic.description)
        topic_sql = f"INSERT INTO topics (id, name, description, chapter_id, position) VALUES ('{topic_id}', '{topic_name}', '{topic_description}', '{chapter_id}', {topic.position});"
        sql_statements.append(topic_sql)
        for concept in topic.concepts:
            concept_id = str(uuid6.uuid7())
            concept_name = escape_sql_string(concept.name)
            concept_description = escape_sql_string(concept.description)
            concept_sql = f"INSERT INTO concepts (id, name, description, topic_id, page_number) VALUES ('{concept_id}', '{concept_name}', '{concept_description}', '{topic_id}', {concept.page_number});"
            sql_statements.append(concept_sql)
    
    
    
    with open(output_sql_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_statements))
        logger.info(f"SQL statements saved to {output_sql_path}")

    return sql_statements
