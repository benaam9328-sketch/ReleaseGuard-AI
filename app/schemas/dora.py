from pydantic import BaseModel, Field


class DoraMetric(BaseModel):
    unavailable: bool
    event_count: int | None = None
    value: float | None = None
    unit: str | None = None
    window_days: int
    validation_errors: list[str] = Field(default_factory=list)


class DoraWindow(BaseModel):
    window_days: int
    deployment_frequency: DoraMetric
    lead_time_for_changes: DoraMetric
    change_failure_rate: DoraMetric
    time_to_restore_service: DoraMetric


class DoraSnapshot(BaseModel):
    window: DoraWindow
    trend: DoraWindow
    includes_synthetic: bool = False
