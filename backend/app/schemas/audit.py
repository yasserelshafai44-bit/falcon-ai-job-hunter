from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditEventRead(BaseModel):
    id: int
    event_type: str
    user_id: int | None
    request_id: str | None
    ip_address: str | None
    resource_type: str | None
    resource_id: str | None
    metadata_json: dict[str, Any]
    occurred_at: datetime

    model_config = {"from_attributes": True}
