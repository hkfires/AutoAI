"""Pydantic Schemas for Request/Response Validation.

Schemas for Task and ExecutionLog API endpoints with
automatic API key masking in responses.
"""

import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.utils.security import mask_api_key


# Valid schedule types
ScheduleType = Literal["interval", "fixed_time"]

# Field length constraints (matching database model)
MAX_NAME_LENGTH = 100
MAX_API_ENDPOINT_LENGTH = 500
MAX_API_KEY_LENGTH = 500
MAX_MODEL_LENGTH = 100


class TaskBase(BaseModel):
    """Base schema for Task with common fields."""

    name: str = Field(..., min_length=1, max_length=MAX_NAME_LENGTH)
    api_endpoint: str = Field(..., min_length=1, max_length=MAX_API_ENDPOINT_LENGTH)
    schedule_type: ScheduleType  # interval | fixed_time
    interval_minutes: Optional[int] = None
    fixed_time: Optional[str] = None  # HH:MM
    message_content: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1, max_length=MAX_MODEL_LENGTH)
    enabled: bool = True

    @field_validator("fixed_time")
    @classmethod
    def validate_fixed_time_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate fixed_time is in HH:MM format."""
        if v is not None:
            if not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", v):
                raise ValueError("fixed_time must be in HH:MM format (00:00-23:59)")
        return v

    @field_validator("interval_minutes")
    @classmethod
    def validate_interval_minutes(cls, v: Optional[int]) -> Optional[int]:
        """Validate interval_minutes is positive."""
        if v is not None and v <= 0:
            raise ValueError("interval_minutes must be a positive integer")
        return v

    @model_validator(mode="after")
    def validate_schedule_config(self) -> "TaskBase":
        """Validate schedule configuration consistency."""
        if self.schedule_type == "interval":
            if self.interval_minutes is None:
                raise ValueError(
                    "interval_minutes is required when schedule_type is 'interval'"
                )
        elif self.schedule_type == "fixed_time":
            if self.fixed_time is None:
                raise ValueError(
                    "fixed_time is required when schedule_type is 'fixed_time'"
                )
        return self


class TaskCreate(TaskBase):
    """Schema for creating a new Task."""

    api_key: str = Field(..., min_length=1, max_length=MAX_API_KEY_LENGTH)


class TaskUpdate(BaseModel):
    """Schema for updating an existing Task.

    All fields are optional to allow partial updates.
    Note: Schedule logic validation must be done at the API layer
    since we don't have access to existing values here.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=MAX_NAME_LENGTH)
    api_endpoint: Optional[str] = Field(None, min_length=1, max_length=MAX_API_ENDPOINT_LENGTH)
    api_key: Optional[str] = Field(None, min_length=1, max_length=MAX_API_KEY_LENGTH)
    schedule_type: Optional[ScheduleType] = None
    interval_minutes: Optional[int] = None
    fixed_time: Optional[str] = None
    message_content: Optional[str] = Field(None, min_length=1)
    model: Optional[str] = Field(None, min_length=1, max_length=MAX_MODEL_LENGTH)
    enabled: Optional[bool] = None

    @field_validator("fixed_time")
    @classmethod
    def validate_fixed_time_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate fixed_time is in HH:MM format."""
        if v is not None:
            if not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", v):
                raise ValueError("fixed_time must be in HH:MM format (00:00-23:59)")
        return v

    @field_validator("interval_minutes")
    @classmethod
    def validate_interval_minutes(cls, v: Optional[int]) -> Optional[int]:
        """Validate interval_minutes is positive."""
        if v is not None and v <= 0:
            raise ValueError("interval_minutes must be a positive integer")
        return v


class TaskResponse(TaskBase):
    """Schema for Task API responses.

    API key is automatically masked for security.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    api_key: str  # Will be masked
    created_at: datetime
    updated_at: datetime

    @field_validator("api_key", mode="before")
    @classmethod
    def mask_key(cls, v: str) -> str:
        """Mask API key before returning in response."""
        return mask_api_key(v)


class ExecutionLogResponse(BaseModel):
    """Schema for ExecutionLog API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    executed_at: datetime
    status: str  # success | failed
    response_summary: Optional[str] = None
    error_message: Optional[str] = None
