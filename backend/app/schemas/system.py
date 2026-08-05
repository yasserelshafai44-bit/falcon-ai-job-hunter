from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "falcon-ai-job-hunter"


class ReadinessCheck(BaseModel):
    name: str
    status: str
    detail: str | None = None


class ReadinessResponse(BaseModel):
    status: str
    checks: list[ReadinessCheck] = Field(default_factory=list)
