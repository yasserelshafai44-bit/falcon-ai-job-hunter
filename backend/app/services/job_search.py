import asyncio
from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.job_providers.base import JobProvider
from app.models.discovered_job import DiscoveredJob


@dataclass(slots=True)
class SyncResult:
    discovered: int
    inserted: int
    updated: int
    errors: dict[str, str]


async def sync_jobs(
    *,
    session: AsyncSession,
    providers: list[JobProvider],
    keyword: str | None,
    location: str | None,
    limit_per_provider: int,
) -> SyncResult:
    errors: dict[str, str] = {}

    async def fetch(provider: JobProvider):
        try:
            return provider.name, await provider.search(
                keyword=keyword,
                location=location,
                limit=limit_per_provider,
            )
        except Exception as exc:
            errors[provider.name] = str(exc)
            return provider.name, []

    batches = await asyncio.gather(*(fetch(provider) for provider in providers))
    jobs = [job for _, batch in batches for job in batch]

    inserted = 0
    updated = 0

    for job in jobs:
        record = await session.scalar(
            select(DiscoveredJob).where(
                DiscoveredJob.provider == job.provider,
                DiscoveredJob.external_id == job.external_id,
            )
        )

        if record is None:
            record = DiscoveredJob(
                provider=job.provider,
                external_id=job.external_id,
                title=job.title,
                company=job.company,
                location=job.location,
                description=job.description,
                url=job.url,
                remote=job.remote,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                currency=job.currency,
                posted_at=job.posted_at,
            )
            session.add(record)
            inserted += 1
        else:
            record.title = job.title
            record.company = job.company
            record.location = job.location
            record.description = job.description
            record.url = job.url
            record.remote = job.remote
            record.salary_min = job.salary_min
            record.salary_max = job.salary_max
            record.currency = job.currency
            record.posted_at = job.posted_at
            updated += 1

    await session.commit()
    return SyncResult(
        discovered=len(jobs),
        inserted=inserted,
        updated=updated,
        errors=errors,
    )


async def search_jobs(
    *,
    session: AsyncSession,
    keyword: str | None,
    location: str | None,
    remote: bool | None,
    page: int,
    page_size: int,
) -> tuple[list[DiscoveredJob], int]:
    filters = []

    if keyword:
        pattern = f"%{keyword}%"
        filters.append(
            or_(
                DiscoveredJob.title.ilike(pattern),
                DiscoveredJob.company.ilike(pattern),
                DiscoveredJob.description.ilike(pattern),
            )
        )

    if location:
        filters.append(DiscoveredJob.location.ilike(f"%{location}%"))

    if remote is not None:
        filters.append(DiscoveredJob.remote.is_(remote))

    base_query = select(DiscoveredJob).where(*filters)
    total = await session.scalar(
        select(func.count()).select_from(base_query.subquery())
    ) or 0

    rows = await session.scalars(
        base_query.order_by(DiscoveredJob.discovered_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(rows), total


async def get_job(
    *, session: AsyncSession, job_id: int
) -> DiscoveredJob | None:
    return await session.get(DiscoveredJob, job_id)
