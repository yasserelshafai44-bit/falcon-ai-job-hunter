from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.job_providers.factory import build_job_providers
from app.schemas.job_search import (
    JobRead,
    JobSearchResponse,
    JobSyncRequest,
    JobSyncResponse,
)
from app.services.job_search import get_job, search_jobs, sync_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobSearchResponse)
async def list_jobs(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    keyword: str | None = None,
    location: str | None = None,
    remote: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> JobSearchResponse:
    items, total = await search_jobs(
        session=session,
        keyword=keyword,
        location=location,
        remote=remote,
        page=page,
        page_size=page_size,
    )
    return JobSearchResponse(
        items=[JobRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=JobRead)
async def read_job(
    job_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobRead:
    item = await get_job(session=session, job_id=job_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobRead.model_validate(item)


@router.post("/sync", response_model=JobSyncResponse)
async def synchronize_jobs(
    payload: JobSyncRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobSyncResponse:
    providers = build_job_providers(set(payload.providers))
    result = await sync_jobs(
        session=session,
        providers=providers,
        keyword=payload.keyword,
        location=payload.location,
        limit_per_provider=payload.limit_per_provider,
    )
    return JobSyncResponse(
        providers_requested=payload.providers,
        discovered=result.discovered,
        inserted=result.inserted,
        updated=result.updated,
        provider_errors=result.errors,
    )
