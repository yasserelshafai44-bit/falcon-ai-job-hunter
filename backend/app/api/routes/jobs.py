from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.database.session import get_db_session
from app.job_providers.employer_registry import (
    EMPLOYER_REGISTRY,
    resolve_provider_selection,
)
from app.job_providers.factory import build_job_providers
from app.models.discovered_job import DiscoveredJob
from app.models.provider_refresh_run import ProviderRefreshRun
from app.models.user import User
from app.schemas.job_search import (
    EmployerRegistryRead,
    JobProviderRead,
    JobRead,
    JobSearchResponse,
    JobSyncRequest,
    JobSyncResponse,
    ManualJobImport,
    ManualJobImportResponse,
)
from app.services.job_search import get_job, import_manual_job, search_jobs, sync_jobs
from app.services.matching_engine import calculate_and_persist_match
from app.services.provider_monitoring import record_refresh_runs

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/employers", response_model=list[EmployerRegistryRead])
async def list_employers(
    _user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[EmployerRegistryRead]:
    results: list[EmployerRegistryRead] = []
    assessed_at = datetime(2026, 9, 27, tzinfo=UTC)
    for item in EMPLOYER_REGISTRY:
        provider = item["provider"]
        live_vacancies: int | None = None
        latest_refresh_vacancies: int | None = None
        last_checked_at = assessed_at
        last_successful_refresh = None
        latest_refresh_status = None
        latest_refresh_error = None
        if item["status"] == "LIVE" and provider:
            live_vacancies = int(
                await session.scalar(
                    select(func.count(DiscoveredJob.id)).where(
                        DiscoveredJob.provider == provider,
                        DiscoveredJob.is_active.is_(True),
                    )
                )
                or 0
            )
            refresh = await session.scalar(
                select(ProviderRefreshRun)
                .where(
                    ProviderRefreshRun.provider == provider,
                    ProviderRefreshRun.status == "completed",
                )
                .order_by(ProviderRefreshRun.completed_at.desc())
                .limit(1)
            )
            if refresh:
                latest_refresh_vacancies = refresh.jobs_retrieved
                last_successful_refresh = refresh.completed_at
            latest = await session.scalar(
                select(ProviderRefreshRun)
                .where(ProviderRefreshRun.provider == provider)
                .order_by(ProviderRefreshRun.completed_at.desc())
                .limit(1)
            )
            if latest:
                last_checked_at = latest.completed_at
                latest_refresh_status = latest.status
                if latest.status != "completed":
                    latest_refresh_error = str(
                        latest.failures.get("message") or "Latest refresh failed"
                    )
            else:
                last_checked_at = None
            if not refresh and live_vacancies == 0:
                live_vacancies = None
        results.append(
            EmployerRegistryRead(
                **item,
                live_vacancies=live_vacancies,
                latest_refresh_vacancies=latest_refresh_vacancies,
                last_checked_at=last_checked_at,
                last_successful_refresh=last_successful_refresh,
                latest_refresh_status=latest_refresh_status,
                latest_refresh_error=latest_refresh_error,
            )
        )
    return results


@router.post("/manual", response_model=ManualJobImportResponse)
async def create_manual_job(
    payload: ManualJobImport,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ManualJobImportResponse:
    try:
        job, created = await import_manual_job(session=session, payload=payload)
        match = await calculate_and_persist_match(
            session=session,
            user_id=user.id,
            candidate_analysis_id=payload.candidate_analysis_id,
            job_id=job.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ManualJobImportResponse(
        job=JobRead.model_validate(job),
        match=match,
        created=created,
        message=(
            "Official vacancy text imported and ranked"
            if created
            else "Existing official vacancy updated and ranked without duplication"
        ),
    )


@router.get("/refresh-runs")
async def list_refresh_runs(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    rows = list(
        await session.scalars(
            select(ProviderRefreshRun)
            .where(ProviderRefreshRun.user_id == user.id)
            .order_by(ProviderRefreshRun.id.desc())
            .limit(limit)
        )
    )
    return [
        {
            "id": row.id,
            "provider": row.provider,
            "status": row.status,
            "jobs_retrieved": row.jobs_retrieved,
            "new_jobs": row.new_jobs,
            "changed_jobs": row.changed_jobs,
            "closed_jobs": row.closed_jobs,
            "failures": row.failures,
            "score_distribution": row.score_distribution,
            "recommendation_distribution": row.recommendation_distribution,
            "occupational_family_distribution": row.occupational_family_distribution,
            "alerts": row.alerts,
            "started_at": row.started_at,
            "completed_at": row.completed_at,
        }
        for row in rows
    ]


@router.get("/providers", response_model=list[JobProviderRead])
async def list_job_providers(
    _user: Annotated[User, Depends(get_current_user)],
) -> list[JobProviderRead]:
    settings = get_settings()
    return [
        JobProviderRead(
            id="remoteok",
            name="Remote OK",
            kind="real",
            credentials_required=False,
            source_url="https://remoteok.com",
            recommended_refresh_minutes=settings.real_job_refresh_minutes,
        ),
        JobProviderRead(
            id="local",
            name="Local demo fixtures",
            kind="demo",
            credentials_required=False,
        ),
        *[
            JobProviderRead(
                id=e["provider"],
                name=e["employer"],
                kind="real",
                credentials_required=False,
                source_url=e["careers_url"],
                recommended_refresh_minutes=settings.real_job_refresh_minutes,
            )
            for e in EMPLOYER_REGISTRY
            if e["status"] == "LIVE" and e["provider"]
        ],
        JobProviderRead(
            id="manual_official",
            name="Manual official vacancy",
            kind="manual",
            credentials_required=False,
        ),
    ]


@router.get("", response_model=JobSearchResponse)
async def list_jobs(
    _user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    keyword: str | None = None,
    location: str | None = None,
    remote: bool | None = None,
    provider: str | None = None,
    active_only: bool = True,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> JobSearchResponse:
    items, total = await search_jobs(
        session=session,
        keyword=keyword,
        location=location,
        remote=remote,
        provider=provider,
        active_only=active_only,
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
    _user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobRead:
    item = await get_job(session=session, job_id=job_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobRead.model_validate(item)


@router.post("/sync", response_model=JobSyncResponse)
async def synchronize_jobs(
    payload: JobSyncRequest,
    _user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobSyncResponse:
    started_at = datetime.now(UTC)
    requested_providers = resolve_provider_selection(payload.providers)
    providers = build_job_providers(set(requested_providers))
    if not providers:
        raise HTTPException(
            status_code=422, detail="No supported job providers requested"
        )
    if not payload.refresh:
        return JobSyncResponse(providers_requested=requested_providers)
    result = await sync_jobs(
        session=session,
        providers=providers,
        keyword=payload.keyword,
        location=payload.location,
        limit_per_provider=payload.limit_per_provider,
    )
    if payload.candidate_analysis_id is not None:
        page = 1
        while True:
            jobs, total = await search_jobs(
                session=session,
                keyword=payload.keyword,
                location=payload.location,
                remote=None,
                provider=None,
                active_only=True,
                page=page,
                page_size=500,
            )
            for job in jobs:
                if job.provider not in requested_providers:
                    continue
                try:
                    await calculate_and_persist_match(
                        session=session,
                        user_id=_user.id,
                        candidate_analysis_id=payload.candidate_analysis_id,
                        job_id=job.id,
                    )
                except ValueError:
                    continue
            if page * 500 >= total:
                break
            page += 1
    runs = await record_refresh_runs(
        session,
        user_id=_user.id,
        result=result,
        providers=[
            provider
            for provider in requested_providers
            if provider not in result.skipped_providers
        ],
        candidate_analysis_id=payload.candidate_analysis_id,
        started_at=started_at,
    )
    return JobSyncResponse(
        providers_requested=requested_providers,
        discovered=result.discovered,
        inserted=result.inserted,
        updated=result.updated,
        duplicates=result.duplicates,
        closed=result.closed,
        provider_errors=result.errors,
        refresh_run_ids=[run.id for run in runs],
    )
