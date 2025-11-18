"""
Database Schemas for the English-for-Kids app

Each Pydantic model represents a collection in your MongoDB database.
Collection name is the lowercase of the class name.
"""
from pydantic import BaseModel, Field
from typing import Optional, List

class Lesson(BaseModel):
    """
    Collection: "lesson"
    Represents a lesson unit children can learn (e.g., Colors, Animals).
    """
    title: str = Field(..., description="Lesson title in Hebrew (for UI)")
    english_title: Optional[str] = Field(None, description="Optional English title")
    description: Optional[str] = Field(None, description="Short description in Hebrew")
    level: str = Field("beginner", description="Level: beginner | intermediate | advanced")
    cover_emoji: str = Field("📘", description="Emoji icon for the lesson card")

class Word(BaseModel):
    """
    Collection: "word"
    Vocabulary items mapped to a lesson.
    """
    lesson_id: str = Field(..., description="ID of the lesson this word belongs to")
    english: str = Field(..., description="English word")
    hebrew: str = Field(..., description="Hebrew translation")
    image_url: Optional[str] = Field(None, description="Optional image to illustrate the word")
    example: Optional[str] = Field(None, description="Short example sentence in simple English")

class Progress(BaseModel):
    """
    Collection: "progress"
    Tracks a user's correct answers and streaks per lesson.
    """
    user_id: str = Field(..., description="User identifier (e.g., 'guest' or UUID)")
    lesson_id: str = Field(..., description="Related lesson id")
    correct: int = Field(0, ge=0)
    incorrect: int = Field(0, ge=0)
    last_score: Optional[int] = Field(None, description="Last quiz score out of N")

# Optional: Example initial content (not used directly by API)
class SeedData(BaseModel):
    lessons: List[Lesson] = []
    words: List[Word] = []
