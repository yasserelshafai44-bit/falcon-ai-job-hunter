from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate_analysis import CandidateAnalysis
from app.models.discovered_job import DiscoveredJob
from app.models.job_match import JobMatch
from app.schemas.job_matching import JobMatchRead
from app.services.candidate_context import enrich_analysis_with_profile
from app.services.match_scoring import JobInput, score_candidate_against_job


class MatchingInputError(ValueError):
    """Raised when the requested candidate analysis or job cannot be matched."""


def to_match_read(record: JobMatch) -> JobMatchRead:
    return JobMatchRead(
        id=record.id,
        user_id=record.user_id,
        candidate_analysis_id=record.candidate_analysis_id,
        job_id=record.job_id,
        overall_score=record.overall_score,
        career_fit_score=record.overall_score,
        location_fit=_location_value(record.evidence, "status"),
        location_fit_explanation=_location_value(record.evidence, "explanation"),
        recommendation=record.recommendation,
        occupational_family=record.occupational_family,
        seniority_assessment=record.seniority_assessment,
        strengths=record.strengths,
        gaps=record.gaps,
        mandatory_failures=record.mandatory_failures,
        evidence=record.evidence,
        uncertainty=record.uncertainty,
        recommended_cv_track=record.recommended_cv_track,
        recommended_next_action=record.recommended_next_action,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _location_value(evidence: list[dict], field: str) -> str:
    location = next(
        (item for item in evidence if item.get("dimension") == "location"), None
    )
    if location is None:
        return "unknown" if field == "status" else "Location has not been assessed"
    value = str(location.get(field) or "")
    if field == "status":
        return {"matched": "good", "mismatched": "outside_preference"}.get(
            value, "unknown"
        )
    return value or "Location has not been assessed"


async def calculate_and_persist_match(
    *,
    session: AsyncSession,
    user_id: int,
    candidate_analysis_id: int,
    job_id: int,
) -> JobMatchRead:
    analysis = await session.scalar(
        select(CandidateAnalysis).where(
            CandidateAnalysis.id == candidate_analysis_id,
            CandidateAnalysis.user_id == user_id,
        )
    )
    if analysis is None:
        raise MatchingInputError("Candidate analysis not found")

    job = await session.get(DiscoveredJob, job_id)
    if job is None:
        raise MatchingInputError("Job not found")

    candidate_evidence = dict(analysis.analysis_data)
    candidate_evidence["source_text"] = analysis.extracted_text
    candidate_evidence = await enrich_analysis_with_profile(
        session, user_id, candidate_evidence
    )
    score = score_candidate_against_job(
        candidate_analysis=candidate_evidence,
        job=JobInput(
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            remote=job.remote,
            workplace_type=job.workplace_type,
            requirements=tuple(job.requirements or []),
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            currency=job.currency,
        ),
    )

    record = await session.scalar(
        select(JobMatch).where(
            JobMatch.user_id == user_id,
            JobMatch.candidate_analysis_id == candidate_analysis_id,
            JobMatch.job_id == job_id,
        )
    )
    payload = score.model_dump(mode="json")
    evidence = payload.pop("evidence")
    payload.pop("career_fit_score")
    payload.pop("location_fit")
    payload.pop("location_fit_explanation")

    if record is None:
        record = JobMatch(
            user_id=user_id,
            candidate_analysis_id=candidate_analysis_id,
            job_id=job_id,
            evidence=evidence,
            **payload,
        )
        session.add(record)
    else:
        for field, value in payload.items():
            setattr(record, field, value)
        record.evidence = evidence

    await session.commit()
    await session.refresh(record)
    return to_match_read(record)


async def calculate_and_persist_matches(
    *,
    session: AsyncSession,
    user_id: int,
    candidate_analysis_id: int,
    job_ids: list[int],
) -> list[JobMatchRead]:
    """Score a bounded batch while reusing candidate context and one commit."""
    analysis = await session.scalar(
        select(CandidateAnalysis).where(
            CandidateAnalysis.id == candidate_analysis_id,
            CandidateAnalysis.user_id == user_id,
        )
    )
    if analysis is None:
        raise MatchingInputError("Candidate analysis not found")

    candidate_evidence = dict(analysis.analysis_data)
    candidate_evidence["source_text"] = analysis.extracted_text
    candidate_evidence = await enrich_analysis_with_profile(
        session, user_id, candidate_evidence
    )
    unique_ids = list(dict.fromkeys(job_ids))
    jobs = list(
        await session.scalars(
            select(DiscoveredJob).where(DiscoveredJob.id.in_(unique_ids))
        )
    )
    jobs_by_id = {job.id: job for job in jobs}
    existing = list(
        await session.scalars(
            select(JobMatch).where(
                JobMatch.user_id == user_id,
                JobMatch.candidate_analysis_id == candidate_analysis_id,
                JobMatch.job_id.in_(unique_ids),
            )
        )
    )
    existing_by_job = {record.job_id: record for record in existing}
    for job_id in unique_ids:
        job = jobs_by_id.get(job_id)
        if job is None:
            continue
        score = score_candidate_against_job(
            candidate_analysis=candidate_evidence,
            job=JobInput(
                title=job.title,
                company=job.company,
                location=job.location,
                description=job.description,
                remote=job.remote,
                workplace_type=job.workplace_type,
                requirements=tuple(job.requirements or []),
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                currency=job.currency,
            ),
        )
        payload = score.model_dump(mode="json")
        evidence = payload.pop("evidence")
        payload.pop("career_fit_score")
        payload.pop("location_fit")
        payload.pop("location_fit_explanation")
        record = existing_by_job.get(job_id)
        if record is None:
            record = JobMatch(
                user_id=user_id,
                candidate_analysis_id=candidate_analysis_id,
                job_id=job_id,
                evidence=evidence,
                **payload,
            )
            session.add(record)
            existing_by_job[job_id] = record
        else:
            for field, value in payload.items():
                setattr(record, field, value)
            record.evidence = evidence

    await session.commit()
    records = list(
        await session.scalars(
            select(JobMatch).where(
                JobMatch.user_id == user_id,
                JobMatch.candidate_analysis_id == candidate_analysis_id,
                JobMatch.job_id.in_(unique_ids),
            )
        )
    )
    return [to_match_read(record) for record in records]


async def list_matches(
    *,
    session: AsyncSession,
    user_id: int,
) -> tuple[list[JobMatchRead], int]:
    total = (
        await session.scalar(
            select(func.count())
            .select_from(JobMatch)
            .where(JobMatch.user_id == user_id)
        )
        or 0
    )
    rows = await session.scalars(
        select(JobMatch)
        .where(JobMatch.user_id == user_id)
        .order_by(JobMatch.overall_score.desc(), JobMatch.updated_at.desc())
    )
    return [to_match_read(row) for row in rows], total


async def get_match(
    *,
    session: AsyncSession,
    user_id: int,
    match_id: int,
) -> JobMatchRead | None:
    record = await session.scalar(
        select(JobMatch).where(
            JobMatch.id == match_id,
            JobMatch.user_id == user_id,
        )
    )
    return to_match_read(record) if record else None
