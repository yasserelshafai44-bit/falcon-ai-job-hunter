"""Specialist prerequisites outweigh transferable management responsibilities."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from app.services.match_scoring import JobInput, score_candidate_against_job
from app.services.occupational_identity import specialist_evidence

from tests.test_production_ranking import candidate


def score(job, cv=None):
    return score_candidate_against_job(candidate_analysis=cv or candidate(), job=job)


def chef_job():
    data = json.loads(
        (Path(__file__).parent / "fixtures/production_chef_manager.json").read_text()
    )
    return JobInput(**{k: data[k] for k in JobInput.__dataclass_fields__ if k in data})


def test_live_chef_manager_cannot_borrow_qsr_operations_identity():
    job = chef_job()
    result = score(job)
    assert result.occupational_family == "culinary"
    assert result.career_fit_score <= 24
    assert result.recommendation.value == "reject"
    assert "Culinary occupational experience" in result.mandatory_failures
    assert any(
        "UNKNOWN" in e.explanation
        for e in result.evidence
        if e.dimension == "mandatory"
    )
    assert (
        score(replace(job, location="UNKNOWN")).career_fit_score
        == result.career_fit_score
    )


@pytest.mark.parametrize(
    "title",
    [
        "Executive Chef",
        "Chef Manager",
        "Kitchen Manager",
        "Culinary Director",
        "Finance Manager",
        "Regional Sales Manager",
        "Engineering Manager",
        "HR Operations Manager",
        "IT Operations Manager",
        "Clinical Manager",
        "Technical Operations Manager",
        "Software Engineer",
        "Head of Finance",
    ],
)
def test_generic_pnl_and_multisite_boilerplate_cannot_override_specialist_title(title):
    job = replace(chef_job(), title=title)
    assert score(job).career_fit_score <= 24
    assert score(job).recommendation.value == "reject"


@pytest.mark.parametrize(
    "claim",
    [
        "Managed chefs and kitchen production across 30 restaurants.",
        "Oversaw HR, finance, IT and engineering teams.",
        "Managed food safety, menu development and culinary standards.",
        "Not a professional chef. No experience as a chef.",
        "Seeking Chef Manager roles.",
    ],
)
def test_oversight_and_inferred_labels_are_not_professional_chef_experience(claim):
    cv = candidate()
    cv["source_text"] += "\n" + claim
    cv["role_family"] = {"value": "Chef Manager"}  # unsupported inferred label
    assert not specialist_evidence(cv, "culinary")
    assert score(chef_job(), cv).career_fit_score <= 24


def test_explicit_professional_chef_career_is_not_rejected_as_an_operations_mismatch():
    cv = candidate()
    cv["source_text"] += (
        "\nExecutive Chef | Example Catering\nWorked as a Chef Manager."
    )
    result = score(chef_job(), cv)
    assert result.career_fit_score > 24
    assert "Culinary occupational experience" not in result.mandatory_failures


def test_neutral_title_does_not_hide_mandatory_chef_requirement():
    job = replace(
        chef_job(),
        title="Operations Manager",
        description=(
            "Lead multi-site restaurant operations, P&L and people management. "
            "Must be a qualified chef."
        ),
    )
    assert score(job).occupational_family == "culinary"
    assert score(job).career_fit_score <= 24


def test_real_area_leader_not_rejected_for_overseeing_specialist_departments():
    data = json.loads(
        (
            Path(__file__).parent / "fixtures/production_ranking_vacancies.json"
        ).read_text()
    )
    data = next(j for j in data["jobs"] if j["provider"] == "raising_canes_uk")
    job = JobInput(**{k: data[k] for k in JobInput.__dataclass_fields__ if k in data})
    baseline = score(job)
    job = replace(
        job,
        description=job.description
        + (
            "\nOversee chefs and kitchen production; collaborate with HR, finance, "
            "sales, engineering, IT and clinical teams. Work with the Finance "
            "Manager and Executive Chef."
        ),
    )
    result = score(job)
    assert result.occupational_family == "operations_leadership"
    assert result.career_fit_score == baseline.career_fit_score
    assert result.recommendation.value == "strong_apply"


def test_education_sector_is_not_a_teacher_occupation():
    job = replace(chef_job(), title="Regional Operations Manager - Education Catering")
    assert score(job).occupational_family == "operations_leadership"
