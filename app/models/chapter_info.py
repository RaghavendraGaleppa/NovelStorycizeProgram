from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.novel import PyObjectId


class ChapterInfo(BaseModel):
    """Schema for the 'chapter_info' MongoDB collection."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    novel_id: PyObjectId = Field(..., description="Reference to the novel's _id")
    chapter_num: int = Field(..., description="Chapter number (1-indexed)")
    chapter_url: str = Field(..., description="Full URL to the chapter page")
    chapter_title: str = Field(default="", description="Chapter title text")

    # Phase 2+ fields — initialized with defaults
    is_parsed: bool = Field(default=False)
    parsed_path: Optional[str] = Field(default=None)
    parse_chapter_length_words: Optional[int] = Field(default=None)
    parse_chapter_length_chars: Optional[int] = Field(default=None)

    is_storycized: bool = Field(default=False)
    storycize_path: Optional[str] = Field(default=None)
    storycized_chapter_length_words: Optional[int] = Field(default=None)
    storycized_chapter_length_chars: Optional[int] = Field(default=None)

    is_chapter_audio_transcribed: bool = Field(default=False)
    chapter_audio_path: Optional[str] = Field(default=None)
    chapter_audio_length_seconds: Optional[int] = Field(default=None)

    is_storycize_audio_transcribed: bool = Field(default=False)
    storycize_audio_path: Optional[str] = Field(default=None)
    storycize_audio_length_seconds: Optional[int] = Field(default=None)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }

    def to_mongo_dict(self) -> dict:
        """Convert to a dict suitable for MongoDB insertion (excludes _id)."""
        data = self.model_dump(by_alias=True, exclude={"id"})
        data.pop("_id", None)
        # Ensure novel_id is an ObjectId, not a string
        if isinstance(data.get("novel_id"), str):
            data["novel_id"] = ObjectId(data["novel_id"])
        return data
