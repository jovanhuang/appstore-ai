"""Common Pydantic models and functions."""""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId

class Artifact(BaseModel):
    """Artifact model for model cards.
    Artifacts can be linked models, datasets, or other artifacts.
    """
    artifact_type: str = Field(..., alias="artifactType")
    name: str
    url: str
    timestamp: Optional[datetime] = None
    framework: Optional[str] = None

    class Config:
        """Pydantic config to allow creation of data model
        from a JSON object with camelCase keys."""
        allow_population_by_field_name = True

class PyObjectId(ObjectId):
    """Custom Pydantic type for MongoDB ObjectIds."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: str) -> ObjectId:
        """Validate the objectid.

        Args:
            v (str): Objectid to validate

        Raises:
            ValueError: If objectid is invalid

        Returns:
            ObjectId: Validated objectid
        """
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")
