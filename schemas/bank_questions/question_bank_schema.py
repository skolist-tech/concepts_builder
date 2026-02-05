"""
Question bank schemas for solved examples and exercise questions.

Uses a base question class to eliminate duplication between question types.
"""

from typing import List, Optional, Literal

from pydantic import BaseModel, Field

from schemas.bank_questions.question_types import SVG


class MatchColumn(BaseModel):
    """Represents a column in a 'Match The Following' question."""
    column_name: str = Field(..., description="Name/header of the column (e.g., 'Column A', 'Column B')")
    items: List[str] = Field(..., description="List of items in this column")


class BaseQuestion(BaseModel):
    """
    Base class for all question types.
    Contains common fields shared between SolvedExample and ExerciseQuestion.
    """
    # Question Text Related
    question_text: str = Field(
        default=None, 
        description="The question text, formatted properly in latex wherever needed"
    )

    option1: Optional[str] = Field(default=None, description="First option (if applicable in MCQ or MSQ)")
    option2: Optional[str] = Field(default=None, description="Second option (if applicable in MCQ or MSQ)")
    option3: Optional[str] = Field(default=None, description="Third option (if applicable in MCQ or MSQ)")
    option4: Optional[str] = Field(default=None, description="Fourth option (if applicable in MCQ or MSQ)")
    
    match_columns: Optional[List[MatchColumn]] = Field(
        default=None, 
        description="List of columns for 'Match The Following' type questions"
    )

    svgs: Optional[List[SVG]] = Field(
        default=None, 
        description="List of SVGs relevant to the question if needed"
    )

    # Answer Related
    correct_mcq_option: Optional[int] = Field(
        default=None, 
        description="Correct option (1-4) (if applicable in MCQ)"
    )
    msq_option1_answer: Optional[bool] = Field(
        default=None, 
        description="Is option 1 correct (if applicable in MSQ)"
    )
    msq_option2_answer: Optional[bool] = Field(
        default=None, 
        description="Is option 2 correct (if applicable in MSQ)"
    )
    msq_option3_answer: Optional[bool] = Field(
        default=None, 
        description="Is option 3 correct (if applicable in MSQ)"
    )
    msq_option4_answer: Optional[bool] = Field(
        default=None, 
        description="Is option 4 correct (if applicable in MSQ)"
    )
    istrue: Optional[bool] = Field(
        default=None, 
        description="True/False answer (if applicable in True/False questions)"
    )
    explanation: str = Field(
        default=None, 
        description="Explanation for the answer"
    )
    answer_text: str = Field(
        default=None, 
        description="Answer text if applicable"
    )

    # Metadata
    hardness_level: Optional[str] = Field(
        default=None, 
        description="Difficulty: easy, medium, hard"
    )
    question_type: Literal[
        "MCQ4",
        "MSQ4",
        "Short Answer",
        "Long Answer",
        "FillInTheBlank",
        "TrueFalse",
        "MathTheFollowing"
    ] = Field(
        default=None, 
        description="Type of question, to be strictly one of MCQ4, MSQ4, Short Answer, Long Answer, FillInTheBlank, TrueFalse, MathTheFollowing"
    )
    concepts: List[str] = Field(
        default=[], 
        description="List of concepts involved in the question, map to the concepts list provided separately"
    )
    is_image_needed: Optional[int] = Field(
        default=0, 
        description="1 if figure or image is referenced or needed, else 0"
    )


class SolvedExample(BaseQuestion):
    """
    Represents a solved example question from a chapter.
    Inherits all fields from BaseQuestion.
    """
    pass


class ExerciseQuestion(BaseQuestion):
    """
    Represents an exercise question from a chapter.
    Inherits all fields from BaseQuestion.
    """
    pass


class SolvedExamplesBank(BaseModel):
    """Collection of all solved examples from a chapter."""
    chapter_name: str = Field(..., description="Name of the chapter")
    solved_examples_questions: List[SolvedExample] = Field(
        ..., 
        description="List of all solved example questions from the chapter"
    )


class ExerciseQuestionsBank(BaseModel):
    """Collection of all exercise questions from a chapter."""
    chapter_name: str = Field(..., description="Name of the chapter")
    exercise_questions: List[ExerciseQuestion] = Field(
        ..., 
        description="List of all exercise questions from the chapter"
    )