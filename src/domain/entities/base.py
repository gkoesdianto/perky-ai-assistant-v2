from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class BaseEntity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True
