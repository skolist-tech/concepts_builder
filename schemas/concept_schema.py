from typing import List
from pydantic import BaseModel, Field


class Concept(BaseModel):
    """
    This class represents a concept.
    """
    name: str = Field(description="Name of the concept, in 2-3 words")
    description: str = Field(
        description="Description of the concept, in 1-2 lines. 3-4 only if required in rare case"
    )
    page_number: int = Field(description="Page number of the concept")


class Topic(BaseModel):
    """
    This class represents a topic.
    """

    name: str = Field(description="Name of the topic, in 2-3 words")
    description: str = Field(
        description="Description of the topic, in 1-2 lines. 3-4 only if required in rare case"
    )
    concepts: List[Concept] = Field(description="List of concepts in this topic")
    position:int = Field(description="Position of the topic in the chapter")


class Chapter(BaseModel):
    """
    This class represents a chapter.
    """

    name: str = Field(description="Name of the chapter, in 2-3 words")
    description: str = Field(
        description="Description of the chapter, in 1-2 lines. 3-4 only if required in rare case"
    )
    topics: List[Topic] = Field(description="List of topics in this chapter")
    # position: int = Field(description="Position of the chapter in the book/course")

