from fastapi import APIRouter, HTTPException

from app.schemas.integration import (
    ConnectorListResponse,
    ConnectorSearchRequest,
    ConnectorSearchResponse,
    NormalizedJobRead,
)
from app.services.integration_service import build_default_registry

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/connectors", response_model=ConnectorListResponse)
async def list_connectors() -> ConnectorListResponse:
    registry = build_default_registry()
    return ConnectorListResponse(connectors=registry.names())


@router.post(
    "/connectors/{connector_name}/search",
    response_model=ConnectorSearchResponse,
)
async def search_connector(
    connector_name: str,
    payload: ConnectorSearchRequest,
) -> ConnectorSearchResponse:
    registry = build_default_registry()
    try:
        connector = registry.get(connector_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        jobs = await connector.search(
            query=payload.query,
            location=payload.location,
            limit=payload.limit,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Connector request failed: {exc}") from exc

    items = [
        NormalizedJobRead(
            source=job.source,
            external_id=job.external_id,
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            url=job.url,
            remote=job.remote,
            metadata=job.metadata,
        )
        for job in jobs
    ]
    return ConnectorSearchResponse(items=items, total=len(items))
