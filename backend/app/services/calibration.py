from __future__ import annotations

from collections import Counter, defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calibration_review import CalibrationReview
from app.models.candidate_analysis import CandidateAnalysis
from app.models.discovered_job import DiscoveredJob
from app.models.job_match import JobMatch
from app.schemas.calibration import CalibrationEvaluation
from app.services.match_scoring import (
    assess_job_seniority,
    classify_occupational_family,
)
from app.services.operational_scope import assess_operational_scope

LABEL_RANK = {
    "reject": 0,
    "weak_match": 1,
    "adjacent": 2,
    "good_match": 3,
    "strong_match": 4,
}
PREDICTED_LABEL = {
    "reject": "reject",
    "weak_match": "weak_match",
    "review": "adjacent",
    "apply": "good_match",
    "strong_apply": "strong_match",
}


async def build_corpus(
    session: AsyncSession,
    *,
    user_id: int,
    candidate_analysis_id: int,
    providers: list[str],
    corpus_version: str,
) -> list[CalibrationReview]:
    analysis = await session.scalar(
        select(CandidateAnalysis).where(
            CandidateAnalysis.id == candidate_analysis_id,
            CandidateAnalysis.user_id == user_id,
        )
    )
    if analysis is None:
        raise ValueError("Candidate analysis not found")
    rows = await session.execute(
        select(JobMatch, DiscoveredJob)
        .join(DiscoveredJob, DiscoveredJob.id == JobMatch.job_id)
        .where(
            JobMatch.user_id == user_id,
            JobMatch.candidate_analysis_id == candidate_analysis_id,
            DiscoveredJob.provider.in_(providers),
            DiscoveredJob.is_demo.is_(False),
        )
    )
    result = []
    for match, job in rows:
        review = await session.scalar(
            select(CalibrationReview).where(
                CalibrationReview.user_id == user_id,
                CalibrationReview.candidate_analysis_id == candidate_analysis_id,
                CalibrationReview.job_id == job.id,
                CalibrationReview.corpus_version == corpus_version,
            )
        )
        vacancy = {
            "provider": job.provider,
            "company": job.company,
            "title": job.title,
            "location": job.location,
            "source_url": job.url,
            "vacancy_id": job.external_id,
            "description": job.description,
            "requirements": job.requirements,
            "retrieval_timestamp": job.last_seen_at.isoformat(),
        }
        falcon = {
            "score": match.overall_score,
            "recommendation": match.recommendation,
            "occupational_family": match.occupational_family,
            "seniority_assessment": match.seniority_assessment,
            "evidence": match.evidence,
            "strengths": match.strengths,
            "gaps": match.gaps,
            "mandatory_failures": match.mandatory_failures,
            "uncertainty": match.uncertainty,
            "scored_at": match.updated_at.isoformat(),
        }
        if review is None:
            review = CalibrationReview(
                user_id=user_id,
                candidate_analysis_id=candidate_analysis_id,
                job_id=job.id,
                vacancy_snapshot=vacancy,
                falcon_snapshot=falcon,
                corpus_version=corpus_version,
            )
            session.add(review)
        else:
            review.vacancy_snapshot = vacancy
            review.falcon_snapshot = falcon
            review.corpus_version = corpus_version
        result.append(review)
    await session.commit()
    for review in result:
        await session.refresh(review)
    return result


def select_validation_sample(
    rows: list[tuple[JobMatch, DiscoveredJob]], size: int
) -> list[tuple[JobMatch, DiscoveredJob, dict]]:
    """Select deterministic, diverse decision-boundary cases for human review."""
    candidates = []
    boundaries = (35, 60, 78, 90)
    for match, job in rows:
        family = match.occupational_family or classify_occupational_family(
            job.title, job.description
        )
        scope = assess_operational_scope(
            job.title, job.description, occupational_family=family
        )
        distance = min(abs(match.overall_score - point) for point in boundaries)
        ambiguity = {
            "unknown": 0,
            "potential_operations": 1,
            "operational_leadership": 2,
            "single_site_frontline": 3,
            "senior_multisite_ownership": 4,
            "unrelated": 5,
        }[scope.tier]
        priority = distance * 10 + ambiguity
        candidates.append(
            (priority, job.provider, match.recommendation, job.id, match, job, scope)
        )
    candidates.sort(key=lambda item: (item[0], item[1], item[3]))

    selected = []
    seen_provider: Counter[str] = Counter()
    seen_recommendation: Counter[str] = Counter()
    seen_tier: Counter[str] = Counter()
    remaining = candidates[:]
    while remaining and len(selected) < size:
        best = min(
            remaining,
            key=lambda item: (
                item[0]
                + seen_provider[item[1]] * 16
                + seen_recommendation[str(item[2])] * 9
                + seen_tier[item[6].tier] * 7,
                item[3],
            ),
        )
        remaining.remove(best)
        _, provider, recommendation, _, match, job, scope = best
        seen_provider[provider] += 1
        seen_recommendation[str(recommendation)] += 1
        seen_tier[scope.tier] += 1
        selected.append(
            (
                match,
                job,
                {
                    "scope_assessment": scope.as_dict(),
                    "validation_reason": (
                        f"Informative {scope.tier.replace('_', ' ')} case near a "
                        "recommendation boundary"
                    ),
                    "seniority_assessment": assess_job_seniority(
                        job.title, job.description
                    ),
                },
            )
        )
    return selected


async def build_validation_sample(
    session: AsyncSession,
    *,
    user_id: int,
    candidate_analysis_id: int,
    providers: list[str],
    corpus_version: str,
    sample_size: int,
) -> list[CalibrationReview]:
    analysis = await session.scalar(
        select(CandidateAnalysis).where(
            CandidateAnalysis.id == candidate_analysis_id,
            CandidateAnalysis.user_id == user_id,
        )
    )
    if analysis is None:
        raise ValueError("Candidate analysis not found")
    filters = [
        JobMatch.user_id == user_id,
        JobMatch.candidate_analysis_id == candidate_analysis_id,
        DiscoveredJob.is_demo.is_(False),
        DiscoveredJob.is_active.is_(True),
    ]
    if providers:
        filters.append(DiscoveredJob.provider.in_(providers))
    rows = list(
        (
            await session.execute(
                select(JobMatch, DiscoveredJob)
                .join(DiscoveredJob, DiscoveredJob.id == JobMatch.job_id)
                .where(*filters)
            )
        ).all()
    )
    if len(rows) < sample_size:
        raise ValueError(f"Only {len(rows)} scored live vacancies are available")
    result = []
    for match, job, metadata in select_validation_sample(rows, sample_size):
        review = await session.scalar(
            select(CalibrationReview).where(
                CalibrationReview.user_id == user_id,
                CalibrationReview.candidate_analysis_id == candidate_analysis_id,
                CalibrationReview.job_id == job.id,
                CalibrationReview.corpus_version == corpus_version,
            )
        )
        vacancy = {
            "provider": job.provider,
            "company": job.company,
            "title": job.title,
            "location": job.location,
            "source_url": job.url,
            "vacancy_id": job.external_id,
            "description": job.description,
            "requirements": job.requirements,
            "retrieval_timestamp": job.last_seen_at.isoformat(),
        }
        falcon = {
            "score": match.overall_score,
            "recommendation": match.recommendation,
            "occupational_family": match.occupational_family,
            "seniority_assessment": match.seniority_assessment,
            "evidence": match.evidence,
            "strengths": match.strengths,
            "gaps": match.gaps,
            "mandatory_failures": match.mandatory_failures,
            "uncertainty": match.uncertainty,
            "scored_at": match.updated_at.isoformat(),
            **metadata,
        }
        if review is None:
            review = CalibrationReview(
                user_id=user_id,
                candidate_analysis_id=candidate_analysis_id,
                job_id=job.id,
                vacancy_snapshot=vacancy,
                falcon_snapshot=falcon,
                corpus_version=corpus_version,
            )
            session.add(review)
        else:
            review.vacancy_snapshot = vacancy
            review.falcon_snapshot = falcon
        result.append(review)
    await session.commit()
    for review in result:
        await session.refresh(review)
    return result


async def evaluate_corpus(
    session: AsyncSession, *, user_id: int, corpus_version: str
) -> CalibrationEvaluation:
    reviews = list(
        await session.scalars(
            select(CalibrationReview).where(
                CalibrationReview.user_id == user_id,
                CalibrationReview.corpus_version == corpus_version,
            )
        )
    )
    labelled = [item for item in reviews if item.human_label]
    label_counts = Counter(item.human_label for item in labelled)
    matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item in labelled:
        predicted = PREDICTED_LABEL[item.falcon_snapshot["recommendation"]]
        matrix[item.human_label][predicted] += 1

    def precision(recommendation: str, accepted: set[str]) -> float | None:
        predictions = [
            r for r in labelled if r.falcon_snapshot["recommendation"] == recommendation
        ]
        return (
            sum(r.human_label in accepted for r in predictions) / len(predictions)
            if predictions
            else None
        )

    recommended = [
        r
        for r in labelled
        if r.falcon_snapshot["recommendation"] in {"strong_apply", "apply"}
    ]
    false_positive_rate = (
        sum(r.human_label in {"weak_match", "reject"} for r in recommended)
        / len(recommended)
        if recommended
        else None
    )
    genuine = [r for r in labelled if r.human_label in {"strong_match", "good_match"}]
    false_negative_rate = (
        sum(
            r.falcon_snapshot["recommendation"] in {"weak_match", "reject"}
            for r in genuine
        )
        / len(genuine)
        if genuine
        else None
    )
    ordered = total = 0
    for left in labelled:
        for right in labelled:
            if LABEL_RANK[left.human_label] <= LABEL_RANK[right.human_label]:
                continue
            total += 1
            ordered += left.falcon_snapshot["score"] > right.falcon_snapshot["score"]
    distributions = {}
    for label in LABEL_RANK:
        scores = [
            r.falcon_snapshot["score"] for r in labelled if r.human_label == label
        ]
        if scores:
            distributions[label] = {
                "count": len(scores),
                "min": min(scores),
                "average": round(sum(scores) / len(scores), 2),
                "max": max(scores),
            }
    return CalibrationEvaluation(
        corpus_version=corpus_version,
        reviewed=len(labelled),
        unreviewed=len(reviews) - len(labelled),
        human_label_distribution=dict(label_counts),
        strong_apply_precision=precision("strong_apply", {"strong_match"}),
        apply_precision=precision("apply", {"strong_match", "good_match"}),
        false_positive_rate=false_positive_rate,
        false_negative_rate=false_negative_rate,
        confusion_matrix={key: dict(value) for key, value in matrix.items()},
        ranking_order_accuracy=ordered / total if total else None,
        score_distribution_by_human_label=distributions,
    )
