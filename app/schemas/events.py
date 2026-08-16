from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.enums import (
    AttributionConfidence,
    AttributionMethod,
    EventType,
    SourceName,
)


class DeliveryEvent(BaseModel):
    event_id: str
    event_type: EventType
    timestamp: datetime
    service: str
    project: str | None = None
    release_id: str | None = None
    environment: str | None = None
    source: SourceName
    is_synthetic: bool
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def resolved_project(self) -> str:
        return self.project or self.service


class IncidentAttribution(BaseModel):
    incident_id: str
    release_id: str | None = None
    attribution_method: AttributionMethod
    attribution_confidence: AttributionConfidence
