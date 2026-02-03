from typing import Optional, List

from pydantic import BaseModel, Field
class SVG(BaseModel):
    svg: str = Field(description="SVG relavant to the question if needed")


class MSQ4(BaseModel):
    """MSQ4 question schema for Gemini structured output."""

    question_text: Optional[str] = Field(default=None, description="The question text")
    option1: Optional[str] = Field(default=None, description="First option")
    option2: Optional[str] = Field(default=None, description="Second option")
    option3: Optional[str] = Field(default=None, description="Third option")
    option4: Optional[str] = Field(default=None, description="Fourth option")
    msq_option1_answer: Optional[bool] = Field(
        default=None, description="Is option 1 correct"
    )
    msq_option2_answer: Optional[bool] = Field(
        default=None, description="Is option 2 correct"
    )
    msq_option3_answer: Optional[bool] = Field(
        default=None, description="Is option 3 correct"
    )
    msq_option4_answer: Optional[bool] = Field(
        default=None, description="Is option 4 correct"
    )
    explanation: Optional[str] = Field(
        default=None, description="Explanation for the answer"
    )
    hardness_level: Optional[str] = Field(
        default=None, description="Difficulty: easy, medium, hard"
    )
    marks: Optional[int] = Field(default=None, description="Marks for this question")
    answer_text: Optional[str] = Field(
        default=None, description="Answer text if applicable"
    )
    svgs: Optional[List[SVG]] = Field(
        default=None, description="List of SVGs relavant to the question if needed"
    )


class MCQ4(BaseModel):
    """MCQ4 question schema for Gemini structured output."""

    question_text: str = Field(description="The question text")
    option1: str = Field(description="First option")
    option2: str = Field(description="Second option")
    option3: str = Field(description="Third option")
    option4: str = Field(description="Fourth option")
    correct_mcq_option: int = Field(description="Correct option (1-4)")
    explanation: Optional[str] = Field(
        default=None, description="Explanation for the answer"
    )
    hardness_level: Optional[str] = Field(
        default=None, description="Difficulty: easy, medium, hard"
    )
    marks: Optional[int] = Field(default=None, description="Marks for this question")
    answer_text: Optional[str] = Field(
        default=None, description="Answer text if applicable"
    )
    svgs: Optional[List[SVG]] = Field(
        default=None, description="List of SVGs relavant to the question if needed"
    )


class FillInTheBlank(BaseModel):
    """Fill in the blank question schema for Gemini structured output."""

    question_text: Optional[str] = Field(
        default=None, description="The question text with blank"
    )
    answer_text: Optional[str] = Field(default=None, description="The correct answer")
    explanation: Optional[str] = Field(
        default=None, description="Explanation for the answer"
    )
    hardness_level: Optional[str] = Field(
        default=None, description="Difficulty: easy, medium, hard"
    )
    marks: Optional[int] = Field(default=None, description="Marks for this question")
    svgs: Optional[List[SVG]] = Field(
        default=None, description="List of SVGs relavant to the question if needed"
    )


class TrueFalse(BaseModel):
    """True/False question schema for Gemini structured output."""

    question_text: Optional[str] = Field(
        default=None, description="The statement to evaluate"
    )
    answer_text: Optional[str] = Field(default=None, description="True or False")
    explanation: Optional[str] = Field(
        default=None, description="Explanation for the answer"
    )
    hardness_level: Optional[str] = Field(
        default=None, description="Difficulty: easy, medium, hard"
    )
    marks: Optional[int] = Field(default=None, description="Marks for this question")
    svgs: Optional[List[SVG]] = Field(
        default=None, description="List of SVGs relavant to the question if needed"
    )


class ShortAnswer(BaseModel):
    """Short answer question schema for Gemini structured output."""

    question_text: Optional[str] = Field(default=None, description="The question text")
    answer_text: Optional[str] = Field(default=None, description="The short answer")
    explanation: Optional[str] = Field(
        default=None, description="Explanation for the answer"
    )
    hardness_level: Optional[str] = Field(
        default=None, description="Difficulty: easy, medium, hard"
    )
    marks: Optional[int] = Field(default=None, description="Marks for this question")
    svgs: Optional[List[SVG]] = Field(
        default=None, description="List of SVGs relavant to the question if needed"
    )


class LongAnswer(BaseModel):
    """Long answer question schema for Gemini structured output."""

    question_text: Optional[str] = Field(default=None, description="The question text")
    answer_text: Optional[str] = Field(default=None, description="The long answer")
    explanation: Optional[str] = Field(
        default=None, description="Explanation for the answer"
    )
    hardness_level: Optional[str] = Field(
        default=None, description="Difficulty: easy, medium, hard"
    )
    marks: Optional[int] = Field(default=None, description="Marks for this question")
    svgs: Optional[List[SVG]] = Field(
        default=None, description="List of SVGs relavant to the question if needed"
    )


class Column(BaseModel):
    name: str = Field(description="Column header, e.g., 'Column A' or 'List I'")
    items: List[str] = Field(description="Items in the column")


class MatchTheFollowing(BaseModel):
    "Match the following question schema for Gemini structured output."

    question_text: Optional[str] = Field(
        default=None,
        description="The main question text, like Match The Following Things",
    )
    columns: List[Column] = Field(
        default=None, description="List of columns for matching"
    )
    answer_text: Optional[str] = Field(default=None, description="The answer text")
    explanation: Optional[str] = Field(
        default=None, description="Explanation for the answer"
    )
    hardness_level: Optional[str] = Field(
        default=None, description="Difficulty: easy, medium, hard"
    )
    marks: Optional[int] = Field(default=None, description="Marks for this question")
    svgs: Optional[List[SVG]] = Field(
        default=None, description="List of SVGs relavant to the question if needed"
    )
