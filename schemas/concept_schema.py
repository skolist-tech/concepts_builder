"""
Pydantic schemas for the concept hierarchy.

Defines the data models for the Chapter → Topic → Concept structure
extracted from textbook PDFs by the AI agents.
"""

from typing import List
from pydantic import BaseModel, Field


class Concept(BaseModel):
    """
    A single educational concept within a topic.
    
    Represents the most granular unit of knowledge, such as
    "Addition of Fractions" or "Pythagorean Theorem".
    
    Attributes:
        name: Short concept name (2-3 words).
        description: Brief explanation of the concept (1-2 sentences).
        page_number: Page in the PDF where this concept appears.
    """

    name: str = Field(description="Name of the concept, in 2-3 words")
    description: str = Field(
        description="Description of the concept, in 1-2 lines. 3-4 only if required in rare case"
    )
    page_number: int = Field(description="Page number of the concept")



class Topic(BaseModel):
    """
    A topic containing multiple related concepts.
    
    Groups concepts that belong together, such as "Operations on Fractions"
    containing concepts like "Addition", "Subtraction", "Multiplication".
    
    Attributes:
        name: Short topic name (2-3 words).
        description: Brief explanation of the topic (1-2 sentences).
        concepts: List of Concept objects within this topic.
        position: Order of this topic within the chapter (1-indexed).
    """

    name: str = Field(description="Name of the topic, in 2-3 words")
    description: str = Field(
        description="Description of the topic, in 1-2 lines. 3-4 only if required in rare case"
    )
    concepts: List[Concept] = Field(description="List of concepts in this topic")
    position: int = Field(description="Position of the topic in the chapter")



class Chapter(BaseModel):
    """
    A chapter containing multiple topics.
    
    Top-level container for a textbook chapter's educational content.
    Each chapter contains topics, which in turn contain concepts.
    
    Attributes:
        name: Short chapter name (2-3 words).
        description: Brief explanation of the chapter (1-2 sentences).
        topics: List of Topic objects within this chapter.
    """

    name: str = Field(description="Name of the chapter, in 2-3 words")
    description: str = Field(
        description="Description of the chapter, in 1-2 lines. 3-4 only if required in rare case"
    )
    topics: List[Topic] = Field(description="List of topics in this chapter")
    # position: int = Field(description="Position of the chapter in the book/course")

