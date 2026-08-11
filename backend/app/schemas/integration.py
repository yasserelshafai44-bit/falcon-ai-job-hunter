from pydantic import BaseModel, Field


class ConnectorListResponse(BaseModel):
    connectors: list[str]


class ConnectorSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    limit: int = Field(default=25, ge=1, le=100)


class NormalizedJobRead(BaseModel):
    source: str
    external_id: str
    title: str
    company: str
    location: str | None
    description: str
    url: str
    remote: bool
    metadata: dict | None = None


class ConnectorSearchResponse(BaseModel):
    items: list[NormalizedJobRead]
    total: int
