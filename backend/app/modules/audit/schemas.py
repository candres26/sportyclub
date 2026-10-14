import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_type: str
    actor_id: uuid.UUID | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    data: dict | None = None
    created_at: datetime
