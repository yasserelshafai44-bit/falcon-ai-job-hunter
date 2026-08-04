from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from app.schemas.job_matching import MatchEvidence, MatchRecommendation, MatchScore

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9&+\-/]{2,}")
_STOP_WORDS = {
    "and", "the", "with", "for", "from", "that", "this", "will", "you",
    "your", "our", "are", "have", "has", "into", "within", "role", "team",
    "job", "work", "working", "experience", "years",
}
_WEIGHTS = {
    "skills": 30,
    "career_track": 18,
    "leadership": 16,
    "industry": 14,
    "achievements": 10,
    "location_remote": 7,
    "salary": 5,
}
_MANDATORY_PATTERNS = (
    re.compile(r"\bmust have\b[:\s-]*(.+?)(?:[.;\n]|$)", re.I),
    re.compile(r"\brequired\b[:\s-]*(.+?)(?:[.;\n]|$)", re.I),
    re.compile(r"\bessential\b[:\s-]*(.+?)(?:[.;\n]|$)", re.I),
)


@dataclass(frozen=True, slots=True)
class JobInput:
    title: str
    company: str
    location: str
    description: str
    remote: bool
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None


def _tokens(value: str) -> set[str]:
    return {
        token.casefold()
        for token in _TOKEN_RE.findall(value or "")
        if token.casefold() not in _STOP_WORDS
    }


def _candidate_values(items: Iterable[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for item in items:
        value = str(item.get("value") or "").strip()
        if value:
            values.append(value)
    return values


def _overlap(candidate_values: Iterable[str], job_text: str) -> tuple[float, set[str]]:
    candidate_tokens = _tokens(" ".join(candidate_values))
    if not candidate_tokens:
        return 0.0, set()
    matched = candidate_tokens & _tokens(job_text)
    return len(matched) / len(candidate_tokens), matched


def _mandatory_requirements(description: str) -> list[str]:
    requirements: list[str] = []
    for pattern in _MANDATORY_PATTERNS:
        for match in pattern.finditer(description):
            value = re.sub(r"\s+", " ", match.group(1)).strip()
            if 3 <= len(value) <= 180:
                requirements.append(value)
    return list(dict.fromkeys(requirements))[:10]


def _recommendation(score: int, failures: list[str]) -> MatchRecommendation:
    if failures:
        return MatchRecommendation.REJECT if score < 65 else MatchRecommendation.REVIEW
    if score >= 85:
        return MatchRecommendation.STRONG_APPLY
    if score >= 70:
        return MatchRecommendation.APPLY
    if score >= 55:
        return MatchRecommendation.REVIEW
    if score >= 35:
        return MatchRecommendation.WEAK_MATCH
    return MatchRecommendation.REJECT


def score_candidate_against_job(
    *,
    candidate_analysis: dict[str, Any],
    job: JobInput,
) -> MatchScore:
    """Return a deterministic and explainable candidate-to-job score."""
    job_text = " ".join([job.title, job.company, job.location, job.description]).strip()

    skills = _candidate_values(candidate_analysis.get("skills", []))
    industries = _candidate_values(candidate_analysis.get("industries", []))
    leadership = _candidate_values(candidate_analysis.get("leadership_scope", []))
    achievements = _candidate_values(candidate_analysis.get("achievements", []))
    career_tracks = [
        str(value)
        for value in candidate_analysis.get("career_tracks", [])
        if value
    ]

    dimensions = {
        "skills": _overlap(skills, job_text),
        "career_track": _overlap(career_tracks, job_text),
        "leadership": _overlap(leadership, job_text),
        "industry": _overlap(industries, job_text),
        "achievements": _overlap(achievements, job_text),
    }

    evidence: list[MatchEvidence] = []
    strengths: list[str] = []
    gaps: list[str] = []
    raw_score = 0.0

    for dimension, (ratio, matched) in dimensions.items():
        contribution = round(_WEIGHTS[dimension] * ratio, 2)
        raw_score += contribution
        label = dimension.replace("_", " ").title()
        if matched:
            strengths.append(f"{label}: {', '.join(sorted(matched)[:8])}")
        elif dimension in {"skills", "career_track", "industry"}:
            gaps.append(f"No clear {dimension.replace('_', ' ')} evidence matched")
        evidence.append(
            MatchEvidence(
                dimension=dimension,
                contribution=contribution,
                explanation=f"{round(ratio * 100)}% candidate evidence overlap",
                sources=sorted(matched)[:12],
            )
        )

    location_score = 0.0
    candidate_locations = " ".join(
        str(value) for value in candidate_analysis.get("preferred_locations", [])
    )
    if job.remote:
        location_score = _WEIGHTS["location_remote"]
        strengths.append("Role is remote")
    elif candidate_locations and _tokens(candidate_locations) & _tokens(job.location):
        location_score = _WEIGHTS["location_remote"]
        strengths.append("Location aligns with candidate preference")
    else:
        gaps.append("Location alignment is not confirmed")

    raw_score += location_score
    evidence.append(
        MatchEvidence(
            dimension="location_remote",
            contribution=location_score,
            explanation="Remote or location preference alignment",
            sources=[job.location] if job.location else [],
        )
    )

    salary_score = 0.0
    candidate_salary_min = candidate_analysis.get("salary_min")
    if candidate_salary_min and job.salary_max:
        salary_score = (
            _WEIGHTS["salary"]
            if job.salary_max >= int(candidate_salary_min)
            else 0.0
        )
    elif job.salary_min or job.salary_max:
        salary_score = _WEIGHTS["salary"] * 0.5

    raw_score += salary_score
    evidence.append(
        MatchEvidence(
            dimension="salary",
            contribution=salary_score,
            explanation="Compensation alignment based on available data",
            sources=[
                value
                for value in (
                    str(job.salary_min) if job.salary_min else "",
                    str(job.salary_max) if job.salary_max else "",
                )
                if value
            ],
        )
    )

    candidate_text = " ".join(
        skills + industries + leadership + achievements + career_tracks
    ).casefold()
    mandatory_failures: list[str] = []
    for requirement in _mandatory_requirements(job.description):
        requirement_tokens = _tokens(requirement)
        if requirement_tokens and not (requirement_tokens & _tokens(candidate_text)):
            mandatory_failures.append(requirement)

    overall_score = max(
        0,
        min(100, round(raw_score - min(35, len(mandatory_failures) * 15))),
    )

    uncertainty: list[str] = []
    if not skills:
        uncertainty.append("Candidate skill evidence is missing")
    if not industries:
        uncertainty.append("Candidate industry evidence is missing")
    if not job.description.strip():
        uncertainty.append("Job description is empty")
    if not (job.salary_min or job.salary_max):
        uncertainty.append("Salary information is unavailable")
    if mandatory_failures:
        uncertainty.append(
            "Mandatory requirements were inferred from job-description wording"
        )

    recommendation = _recommendation(overall_score, mandatory_failures)
    next_action = {
        MatchRecommendation.STRONG_APPLY: "Prepare tailored CV and cover letter",
        MatchRecommendation.APPLY: "Review gaps, then prepare application materials",
        MatchRecommendation.REVIEW: "Human review required before applying",
        MatchRecommendation.WEAK_MATCH: "Do not prioritize unless strategic",
        MatchRecommendation.REJECT: "Do not apply without resolving mandatory gaps",
    }[recommendation]

    return MatchScore(
        overall_score=overall_score,
        recommendation=recommendation,
        strengths=strengths,
        gaps=gaps,
        mandatory_failures=mandatory_failures,
        evidence=evidence,
        uncertainty=uncertainty,
        recommended_cv_track=career_tracks[0] if career_tracks else None,
        recommended_next_action=next_action,
    )
