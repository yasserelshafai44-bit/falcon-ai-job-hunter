from app.schemas.job_matching import MatchRecommendation
from app.services.match_scoring import JobInput, score_candidate_against_job


def test_score_is_deterministic() -> None:
    candidate = {
        "skills": [{"value": "delivery operations"}],
        "industries": [{"value": "food delivery"}],
        "leadership_scope": [{"value": "managed delivery teams"}],
        "achievements": [{"value": "processed 7,200 orders daily"}],
        "career_tracks": ["Delivery and Marketplace Operations"],
    }
    job = JobInput(
        title="Head of Delivery Operations",
        company="Marketplace Co",
        location="UK",
        description="Own food delivery operations and manage delivery teams.",
        remote=True,
    )

    first = score_candidate_against_job(candidate_analysis=candidate, job=job)
    second = score_candidate_against_job(candidate_analysis=candidate, job=job)

    assert first == second
    assert isinstance(first.recommendation, MatchRecommendation)
