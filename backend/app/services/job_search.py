import asyncio
import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.job_providers.base import JobProvider, NormalizedJob
from app.job_providers.location import normalize_location
from app.job_providers.smartrecruiters import SmartRecruitersProvider
from app.models.discovered_job import DiscoveredJob
from app.schemas.job_search import ManualJobImport


def canonical_job_key(
    title: str, company: str, location: str, *, is_demo: bool = False
) -> str:
    normalized = "|".join(
        (
            _normalize_title(title),
            _normalize_company(company),
            normalize_location(location).canonical,
        )
    )
    source_class = "demo" if is_demo else "real"
    return hashlib.sha256(f"{source_class}|{normalized}".encode()).hexdigest()


_COMPANY_ALIASES = {
    "deliveroo": "deliveroo",
    "roofoods": "deliveroo",
    "raising cane s": "raising-canes",
    "raising cane s uk": "raising-canes",
    "raising canes": "raising-canes",
    "kfc": "kfc-uk",
    "kfc uk": "kfc-uk",
    "kfc great britain": "kfc-uk",
    "kentucky fried chicken": "kfc-uk",
}
_DESCRIPTION_STOP = {
    "and",
    "the",
    "for",
    "with",
    "this",
    "that",
    "you",
    "your",
    "our",
    "role",
    "job",
    "will",
    "are",
    "from",
    "have",
    "team",
    "work",
}


def canonicalize_url(value: str) -> str | None:
    try:
        parts = urlsplit(value.strip())
    except ValueError:
        return None
    if parts.scheme.casefold() not in {"http", "https"} or not parts.netloc:
        return None
    path = re.sub(r"/+", "/", parts.path).rstrip("/") or "/"
    return urlunsplit(("https", parts.netloc.casefold(), path, "", ""))


def _normalize_company(value: str) -> str:
    folded = re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()
    folded = re.sub(r"\b(?:limited|ltd|plc|inc|llc)\b", "", folded)
    folded = re.sub(r"\s+", " ", folded).strip()
    return _COMPANY_ALIASES.get(folded, folded)


def _normalize_title(value: str) -> str:
    folded = re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()
    folded = re.sub(r"\bops\b", "operations", folded)
    return re.sub(r"\s+", " ", folded)


def _description_similarity(left: str, right: str) -> float:
    def tokens(value: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]{3,}", value.casefold())
            if token not in _DESCRIPTION_STOP
        }

    left_tokens, right_tokens = tokens(left), tokens(right)
    if not left_tokens or not right_tokens:
        return 0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _disambiguated_key(base_key: str, provider: str, external_id: str) -> str:
    return hashlib.sha256(
        f"{base_key}|{provider.casefold()}|{external_id.casefold()}".encode()
    ).hexdigest()


async def import_manual_job(
    *, session: AsyncSession, payload: ManualJobImport
) -> tuple[DiscoveredJob, bool]:
    """Persist employer text supplied by a user without fetching or scraping its URL."""
    now = datetime.now(UTC)
    canonical_url = canonicalize_url(payload.source_url) if payload.source_url else None
    identity = canonical_url or "|".join(
        (payload.employer, payload.title, payload.location, payload.description)
    )
    external_id = hashlib.sha256(identity.encode()).hexdigest()
    canonical_key = canonical_job_key(payload.title, payload.employer, payload.location)
    identity_filters = [
        (DiscoveredJob.provider == "manual_official")
        & (DiscoveredJob.external_id == external_id)
    ]
    if canonical_url:
        identity_filters.append(DiscoveredJob.canonical_url == canonical_url)
    record = await session.scalar(select(DiscoveredJob).where(or_(*identity_filters)))
    source_record = {
        "provider": "manual_official",
        "external_id": external_id,
        "url": payload.source_url,
        "retrieved_at": now.isoformat(),
        "active": True,
        "last_seen_at": now.isoformat(),
        "closed_at": None,
        "ingestion": "user_supplied_employer_text",
    }
    if record is not None and record.provider != "manual_official":
        sources = list(record.source_records or [])
        if not any(
            item.get("provider") == "manual_official"
            and item.get("external_id") == external_id
            for item in sources
        ):
            record.source_records = [*sources, source_record]
            await session.commit()
            await session.refresh(record)
        return record, False
    if record is None:
        collision = await session.scalar(
            select(DiscoveredJob).where(DiscoveredJob.canonical_key == canonical_key)
        )
        if collision is not None:
            canonical_key = _disambiguated_key(
                canonical_key, "manual_official", external_id
            )
        record = DiscoveredJob(
            provider="manual_official",
            external_id=external_id,
            canonical_key=canonical_key,
            canonical_url=canonical_url,
            title=payload.title.strip(),
            company=payload.employer.strip(),
            location=payload.location.strip(),
            description=payload.description.strip(),
            url=payload.source_url or "",
            remote=payload.workplace_type == "remote",
            is_demo=False,
            is_active=True,
            workplace_type=payload.workplace_type,
            requirements=[
                item.strip() for item in payload.requirements if item.strip()
            ],
            source_records=[source_record],
            salary_min=payload.salary_min,
            salary_max=payload.salary_max,
            currency=payload.currency,
            last_seen_at=now,
        )
        session.add(record)
        created = True
    else:
        record.title = payload.title.strip()
        record.company = payload.employer.strip()
        record.location = payload.location.strip()
        record.description = payload.description.strip()
        record.url = payload.source_url or ""
        record.remote = payload.workplace_type == "remote"
        record.workplace_type = payload.workplace_type
        record.requirements = [
            item.strip() for item in payload.requirements if item.strip()
        ]
        record.salary_min = payload.salary_min
        record.salary_max = payload.salary_max
        record.currency = payload.currency
        record.last_seen_at = now
        record.is_active = True
        record.closed_at = None
        record.source_records = [source_record]
        created = False
    await session.commit()
    await session.refresh(record)
    return record, created


@dataclass(slots=True)
class SyncResult:
    discovered: int
    inserted: int
    updated: int
    duplicates: int
    closed: int
    errors: dict[str, str]
    provider_metrics: dict[str, dict[str, int]]


async def sync_jobs(
    *,
    session: AsyncSession,
    providers: list[JobProvider],
    keyword: str | None,
    location: str | None,
    limit_per_provider: int,
) -> SyncResult:
    # Reuse unchanged published detail, never the list of active postings.
    for provider in providers:
        if isinstance(provider, SmartRecruitersProvider):
            existing = await session.scalars(
                select(DiscoveredJob).where(DiscoveredJob.provider == provider.name)
            )
            provider.cached_jobs = {
                row.external_id: NormalizedJob(
                    **{
                        key: getattr(row, key)
                        for key in NormalizedJob.__dataclass_fields__
                        if hasattr(row, key)
                    }
                )
                for row in existing
            }
    errors: dict[str, str] = {}
    provider_metrics = {
        provider.name: {"retrieved": 0, "inserted": 0, "updated": 0, "closed": 0}
        for provider in providers
    }

    async def fetch(provider: JobProvider):
        try:
            jobs = await asyncio.wait_for(
                provider.search(
                    keyword=keyword,
                    location=location,
                    limit=limit_per_provider,
                ),
                timeout=getattr(provider, "refresh_timeout_seconds", 600),
            )
            return provider, jobs, True
        except TimeoutError:
            errors[provider.name] = (
                f"{provider.name} refresh exceeded "
                f"{getattr(provider, 'refresh_timeout_seconds', 600):.0f}-second "
                "deadline"
            )
            return provider, [], False
        except Exception as exc:
            errors[provider.name] = str(exc)[:240] or "Provider request failed"
            return provider, [], False

    batches = await asyncio.gather(*(fetch(provider) for provider in providers))
    jobs = [job for _, batch, succeeded in batches if succeeded for job in batch]
    for job in jobs:
        provider_metrics[job.provider]["retrieved"] += 1

    inserted = 0
    updated = 0
    duplicates = 0
    closed = 0
    now = datetime.now(UTC)

    for job in jobs:
        canonical_key = canonical_job_key(
            job.title, job.company, job.location, is_demo=job.is_demo
        )
        canonical_url = canonicalize_url(job.url)
        retrieved_at = job.retrieved_at or now
        source_record = {
            "provider": job.provider,
            "external_id": job.external_id,
            "url": job.url,
            "retrieved_at": retrieved_at.isoformat(),
            "active": True,
            "last_seen_at": retrieved_at.isoformat(),
            "closed_at": None,
        }
        identity_filters = [
            (DiscoveredJob.provider == job.provider)
            & (DiscoveredJob.external_id == job.external_id),
            DiscoveredJob.canonical_key == canonical_key,
        ]
        if canonical_url:
            identity_filters.append(DiscoveredJob.canonical_url == canonical_url)
        candidates = list(
            await session.scalars(select(DiscoveredJob).where(or_(*identity_filters)))
        )
        record = None
        for candidate in candidates:
            same_source = (
                candidate.provider == job.provider
                and candidate.external_id == job.external_id
            )
            same_url = bool(canonical_url and candidate.canonical_url == canonical_url)
            safe_cross_provider = (
                candidate.provider != job.provider
                and candidate.canonical_key == canonical_key
                and _description_similarity(candidate.description, job.description)
                >= 0.55
            )
            if same_source or same_url or safe_cross_provider:
                record = candidate
                break
        if record is None and any(
            candidate.canonical_key == canonical_key for candidate in candidates
        ):
            canonical_key = _disambiguated_key(
                canonical_key, job.provider, job.external_id
            )

        if record is None:
            record = DiscoveredJob(
                provider=job.provider,
                external_id=job.external_id,
                canonical_key=canonical_key,
                canonical_url=canonical_url,
                title=job.title,
                company=job.company,
                location=job.location,
                description=job.description,
                url=job.url,
                remote=job.remote,
                is_demo=job.is_demo,
                is_active=job.expires_at is None or job.expires_at > now,
                workplace_type=job.workplace_type,
                requirements=list(job.requirements),
                source_records=[source_record],
                employment_type=job.employment_type,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                currency=job.currency,
                posted_at=job.posted_at,
                expires_at=job.expires_at,
                last_seen_at=now,
            )
            session.add(record)
            inserted += 1
            provider_metrics[job.provider]["inserted"] += 1
        else:
            if record.provider != job.provider or record.external_id != job.external_id:
                duplicates += 1
                existing = list(record.source_records or [])
                identity = (job.provider, job.external_id)
                record.source_records = [
                    item
                    for item in existing
                    if (item.get("provider"), item.get("external_id")) != identity
                ] + [source_record]
                record.last_seen_at = now
                record.is_active = True
                record.closed_at = None
                continue
            if record.canonical_key and record.canonical_key != canonical_key:
                canonical_key = record.canonical_key
            content_changed = any(
                (
                    record.title != job.title,
                    record.company != job.company,
                    record.location != job.location,
                    record.description != job.description,
                    record.url != job.url,
                    record.remote != job.remote,
                    record.workplace_type != job.workplace_type,
                    list(record.requirements or []) != list(job.requirements),
                    record.salary_min != job.salary_min,
                    record.salary_max != job.salary_max,
                    record.posted_at != job.posted_at,
                )
            )
            record.title = job.title
            record.company = job.company
            record.location = job.location
            record.description = job.description
            record.url = job.url
            record.remote = job.remote
            record.is_demo = job.is_demo
            record.is_active = job.expires_at is None or job.expires_at > now
            record.closed_at = None if record.is_active else now
            record.last_seen_at = now
            record.canonical_key = canonical_key
            record.canonical_url = canonical_url
            record.workplace_type = job.workplace_type
            record.requirements = list(job.requirements)
            existing = list(record.source_records or [])
            record.source_records = [
                item
                for item in existing
                if (item.get("provider"), item.get("external_id"))
                != (job.provider, job.external_id)
            ] + [source_record]
            record.employment_type = job.employment_type
            record.salary_min = job.salary_min
            record.salary_max = job.salary_max
            record.currency = job.currency
            record.posted_at = job.posted_at
            record.expires_at = job.expires_at
            updated += 1
            if content_changed:
                provider_metrics[job.provider]["updated"] += 1

    for provider, _, succeeded in batches:
        if (
            not succeeded
            or not provider.complete_snapshot
            or (
                not any(job.provider == provider.name for job in jobs)
                and not provider.authoritative_empty
            )
        ):
            continue
        seen_ids = {job.external_id for job in jobs if job.provider == provider.name}
        records = list(await session.scalars(select(DiscoveredJob)))
        for record in records:
            sources = [dict(source) for source in (record.source_records or [])]
            changed = False
            for source in sources:
                if (
                    source.get("provider") == provider.name
                    and source.get("external_id") not in seen_ids
                    and source.get("active", True)
                ):
                    source["active"] = False
                    source["closed_at"] = now.isoformat()
                    changed = True
            if not changed:
                continue
            record.source_records = sources
            if not any(source.get("active", True) for source in sources):
                if record.is_active:
                    closed += 1
                    provider_metrics[provider.name]["closed"] += 1
                record.is_active = False
                record.closed_at = now

    await session.commit()
    return SyncResult(
        discovered=len(jobs),
        inserted=inserted,
        updated=updated,
        duplicates=duplicates,
        closed=closed,
        errors=errors,
        provider_metrics=provider_metrics,
    )


async def search_jobs(
    *,
    session: AsyncSession,
    keyword: str | None,
    location: str | None,
    remote: bool | None,
    provider: str | None,
    active_only: bool,
    page: int,
    page_size: int,
) -> tuple[list[DiscoveredJob], int]:
    filters = []

    if active_only:
        filters.append(DiscoveredJob.is_active.is_(True))

    if provider:
        filters.append(DiscoveredJob.provider == provider)

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
    total = (
        await session.scalar(select(func.count()).select_from(base_query.subquery()))
        or 0
    )

    rows = await session.scalars(
        base_query.order_by(DiscoveredJob.discovered_at.desc(), DiscoveredJob.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(rows), total


async def get_job(*, session: AsyncSession, job_id: int) -> DiscoveredJob | None:
    return await session.get(DiscoveredJob, job_id)
