"""Full public employer descriptions, with a synthetic operations candidate."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from app.services.match_scoring import JobInput, score_candidate_against_job

from tests.test_production_ranking import candidate

JOBS = json.loads(
    (Path(__file__).parent / "fixtures/coverage_ranking_vacancies.json").read_text(
        encoding="utf-8"
    )
)["jobs"]


@pytest.mark.parametrize("data", JOBS, ids=[j["title"] for j in JOBS])
def test_expanded_real_catalogue_respects_occupation_and_seniority(data):
    job = JobInput(**{k: data[k] for k in JobInput.__dataclass_fields__ if k in data})
    result = score_candidate_against_job(candidate_analysis=candidate(), job=job)
    if "Regional Coach" in job.title:
        assert result.career_fit_score >= 80
        assert result.recommendation.value in {"apply", "strong_apply"}
    else:
        assert result.career_fit_score < 60
        assert result.recommendation.value not in {"apply", "strong_apply", "review"}
    elsewhere = score_candidate_against_job(
        candidate_analysis=candidate(), job=replace(job, location="UNKNOWN")
    )
    assert elsewhere.career_fit_score == result.career_fit_score
