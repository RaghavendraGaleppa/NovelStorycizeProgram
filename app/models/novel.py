from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2 compatibility."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any, *args) -> ObjectId:
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError(f"Invalid ObjectId: {v}")

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic import GetCoreSchemaHandler
        from pydantic_core import core_schema

        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.to_string_ser_schema(),
        )


class Novel(BaseModel):
    """Schema for the 'novels' MongoDB collection."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    title: str = Field(..., description="Novel title/name")
    novel_url: str = Field(..., description="URL to the main novel page on novelbin.me")
    author: str = Field(default="Unknown", description="Author name")
    description: str = Field(default="", description="Novel description/synopsis")
    n_chapters: int = Field(default=0, description="Total number of chapters")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }

    def to_mongo_dict(self) -> dict:
        """Convert to a dict suitable for MongoDB insertion (excludes _id)."""
        data = self.model_dump(by_alias=True, exclude={"id"})
        data.pop("_id", None)
        return data
