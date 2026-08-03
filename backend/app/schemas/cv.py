from datetime import datetime

from pydantic import BaseModel


class CVResponse(BaseModel):
    id: int
    original_name: str
    content_type: str
    file_size: int
    career_track: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
