import asyncio
from collections import Counter
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovered_job import DiscoveredJob
from app.models.job_match import JobMatch
from app.models.provider_refresh_run import ProviderRefreshRun
from app.services.job_search import SyncResult
from app.services.match_scoring import classify_occupational_family


async def _family_distribution(jobs) -> Counter:
    """Keep health/login requests responsive while summarising large feeds."""
    distinct = Counter((job.title, job.description) for job in jobs)

    def classify():
        counts = Counter()
        for (title, description), vacancies in distinct.items():
            counts[classify_occupational_family(title, description)] += vacancies
        return counts

    return await asyncio.to_thread(classify)


async def record_refresh_runs(
    session: AsyncSession,
    *,
    user_id: int,
    result: SyncResult,
    providers: list[str],
    candidate_analysis_id: int | None,
    started_at: datetime,
) -> list[ProviderRefreshRun]:
    runs = []
    for provider in providers:
        metrics = result.provider_metrics.get(
            provider, {"retrieved": 0, "inserted": 0, "updated": 0, "closed": 0}
        )
        jobs = (
            await session.execute(
                select(DiscoveredJob.title, DiscoveredJob.description).where(
                    DiscoveredJob.provider == provider,
                    DiscoveredJob.is_active.is_(True),
                )
            )
        ).all()
        family_distribution = await _family_distribution(jobs)
        score_distribution: dict[str, int] = {}
        recommendation_distribution: dict[str, int] = {}
        if candidate_analysis_id is not None:
            matches = list(
                await session.scalars(
                    select(JobMatch)
                    .join(DiscoveredJob, DiscoveredJob.id == JobMatch.job_id)
                    .where(
                        JobMatch.user_id == user_id,
                        JobMatch.candidate_analysis_id == candidate_analysis_id,
                        DiscoveredJob.provider == provider,
                        DiscoveredJob.is_active.is_(True),
                    )
                )
            )
            score_distribution = dict(
                Counter(
                    "90-100"
                    if match.overall_score >= 90
                    else "78-89"
                    if match.overall_score >= 78
                    else "60-77"
                    if match.overall_score >= 60
                    else "35-59"
                    if match.overall_score >= 35
                    else "0-34"
                    for match in matches
                )
            )
            recommendation_distribution = dict(
                Counter(match.recommendation for match in matches)
            )

        previous = await session.scalar(
            select(ProviderRefreshRun)
            .where(ProviderRefreshRun.provider == provider)
            .order_by(ProviderRefreshRun.id.desc())
            .limit(1)
        )
        alerts = []
        error = result.errors.get(provider)
        if error:
            alerts.append(
                {"code": "provider_failure", "severity": "critical", "message": error}
            )
        if metrics["retrieved"] == 0:
            alerts.append(
                {
                    "code": "zero_jobs",
                    "severity": "critical",
                    "message": (
                        "Provider returned zero eligible jobs; closure reconciliation "
                        "was suppressed on failure/incomplete snapshots."
                    ),
                }
            )
        if metrics["retrieved"] and metrics["closed"] / metrics["retrieved"] > 0.5:
            alerts.append(
                {
                    "code": "abnormal_closure_rate",
                    "severity": "critical",
                    "message": "More than 50% as many jobs closed as were retrieved.",
                }
            )
        unknown_rate = family_distribution.get("unknown", 0) / len(jobs) if jobs else 0
        if unknown_rate > 0.25:
            alerts.append(
                {
                    "code": "unknown_family_spike",
                    "severity": "warning",
                    "message": (
                        f"Unknown occupational family rate is {unknown_rate:.0%}."
                    ),
                }
            )
        if previous and previous.jobs_retrieved:
            change = (
                abs(metrics["retrieved"] - previous.jobs_retrieved)
                / previous.jobs_retrieved
            )
            if change > 0.5:
                alerts.append(
                    {
                        "code": "retrieval_volume_shift",
                        "severity": "warning",
                        "message": f"Eligible vacancy volume changed by {change:.0%}.",
                    }
                )
            previous_high = sum(
                previous.score_distribution.get(key, 0) for key in ("90-100", "78-89")
            )
            current_high = sum(
                score_distribution.get(key, 0) for key in ("90-100", "78-89")
            )
            if previous_high and current_high > previous_high * 2:
                alerts.append(
                    {
                        "code": "high_score_spike",
                        "severity": "warning",
                        "message": "High-scoring vacancy count more than doubled.",
                    }
                )
        run = ProviderRefreshRun(
            user_id=user_id,
            provider=provider,
            status="failed" if error else "completed",
            jobs_retrieved=metrics["retrieved"],
            new_jobs=metrics["inserted"],
            changed_jobs=metrics["updated"],
            closed_jobs=metrics["closed"],
            failures={"message": error} if error else {},
            score_distribution=score_distribution,
            recommendation_distribution=recommendation_distribution,
            occupational_family_distribution=dict(family_distribution),
            alerts=alerts,
            started_at=started_at,
            completed_at=datetime.now(UTC),
        )
        session.add(run)
        runs.append(run)
    await session.commit()
    for run in runs:
        await session.refresh(run)
    return runs
