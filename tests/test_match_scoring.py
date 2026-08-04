from app.services.match_scoring import JobInput, score_candidate_against_job


def test_high_match_produces_explainable_score() -> None:
    candidate = {
        "skills": [
            {"value": "multi-site operations"},
            {"value": "P&L management"},
            {"value": "delivery operations"},
        ],
        "industries": [{"value": "hospitality"}, {"value": "restaurants"}],
        "leadership_scope": [{"value": "managed regional restaurant teams"}],
        "achievements": [{"value": "managed 156 restaurants"}],
        "career_tracks": ["Regional and Multi-Site Operations"],
        "preferred_locations": ["London", "UK"],
    }
    job = JobInput(
        title="Regional Operations Director",
        company="Example Hospitality",
        location="London",
        description=(
            "Lead multi-site restaurant operations, P&L management, delivery "
            "operations and regional hospitality teams."
        ),
        remote=False,
        salary_min=90000,
        salary_max=110000,
        currency="GBP",
    )

    result = score_candidate_against_job(candidate_analysis=candidate, job=job)

    assert 0 <= result.overall_score <= 100
    assert result.strengths
    assert result.evidence
    assert result.recommendation.value in {
        "strong_apply", "apply", "review", "weak_match", "reject"
    }


def test_mandatory_gap_is_reported() -> None:
    candidate = {
        "skills": [{"value": "restaurant operations"}],
        "industries": [{"value": "hospitality"}],
        "leadership_scope": [],
        "achievements": [],
        "career_tracks": [],
    }
    job = JobInput(
        title="Operations Manager",
        company="Example",
        location="London",
        description="Must have CIMA qualification. Lead restaurant operations.",
        remote=False,
    )

    result = score_candidate_against_job(candidate_analysis=candidate, job=job)

    assert result.mandatory_failures
    assert result.uncertainty
