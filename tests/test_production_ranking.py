"""Real production vacancy snapshots; candidate is synthetic, never a private CV."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from app.services.career_evidence import extract_remit, required_years, role_description
from app.services.match_scoring import JobInput, score_candidate_against_job


@pytest.fixture
def vacancies():
    data = json.loads(
        (
            Path(__file__).parent / "fixtures/production_ranking_vacancies.json"
        ).read_text(encoding="utf-8")
    )
    return {
        (j["provider"], j["location"]): JobInput(
            **{key: j[key] for key in JobInput.__dataclass_fields__ if key in j}
        )
        for j in data["jobs"]
    }


def candidate():
    return {
        "role_family": {"value": "Regional Operations Manager"},
        "years_experience": {"value": "20"},
        "source_text": (
            "20 years of QSR, restaurant and franchise operations experience.\n"
            "Led a multi-site portfolio of 30 restaurants and managed 200 staff.\n"
            "Owned full P&L, budget control and cost control.\n"
            "Directed delivery operations and call-centre operations.\n"
            "Led operational performance, KPI ownership and performance reporting.\n"
            "Led team leadership, staff development and coached site managers.\n"
            "Managed stakeholder management, franchise partners, inventory, "
            "supplier management, food safety and brand standards.\n"
            "Full UK driving licence and valid right to work in the UK."
        ),
    }


def score(job, analysis=None):
    return score_candidate_against_job(
        candidate_analysis=analysis or candidate(), job=job
    )


def dimension(result, name):
    return next(e for e in result.evidence if e.dimension == name)


def test_real_vacancies_no_longer_saturate_at_89(vacancies):
    results = {key: score(job) for key, job in vacancies.items()}
    by_provider = {key[0]: result for key, result in results.items()}
    kfc = by_provider["kfc_uk"]
    deliveroo = by_provider["deliveroo"]
    caterlink = by_provider["wsh_group_uk"]
    canes = by_provider["raising_canes_uk"]
    assert (
        len(
            {
                kfc.career_fit_score,
                deliveroo.career_fit_score,
                caterlink.career_fit_score,
            }
        )
        == 3
    )
    assert canes.career_fit_score > kfc.career_fit_score > caterlink.career_fit_score
    assert kfc.career_fit_score > deliveroo.career_fit_score
    assert canes.recommendation.value == "strong_apply"
    assert deliveroo.occupational_family == "customer_operations"
    assert "CRM systems experience" in deliveroo.mandatory_failures
    assert "Catering management experience" in caterlink.mandatory_failures


def test_real_scope_does_not_invent_company_scale_or_pnl(vacancies):
    for (provider, _), job in vacancies.items():
        remit = extract_remit(role_description(job.description))
        assert remit.site_count is None
        assert remit.team_count is None
        if provider != "raising_canes_uk":
            assert not remit.pnl
        result = score(job)
        assert (
            "Site/portfolio count is NOT STATED"
            in dimension(result, "leadership_scope").explanation
        )
        if provider == "deliveroo":
            assert not remit.multisite
        if provider == "wsh_group_uk":
            assert remit.multisite
            assert dimension(result, "experience").status == "unknown"


@pytest.mark.parametrize("location", ["", "UNKNOWN", "London, UK", "Sydney, Australia"])
def test_location_never_changes_real_career_scores(vacancies, location):
    analysis = {**candidate(), "preferred_locations": ["London, UK"]}
    for job in vacancies.values():
        original = score(job, analysis)
        moved = score(replace(job, location=location), analysis)
        assert moved.career_fit_score == original.career_fit_score
        assert moved.recommendation == original.recommendation
        assert dimension(moved, "location").contribution == 0


def test_company_age_does_not_become_required_experience():
    assert required_years("For over 20 years, the Company has delivered meals.") is None
    assert required_years("4+ years’ experience in restaurant operations.") == 4
    assert required_years("Requires 10 years of operations experience.") == 10


def test_company_size_and_reporting_line_do_not_establish_role_scope():
    job = JobInput(
        "Operations Manager",
        "Example",
        "Unknown",
        "Our company operates 1000 restaurants with 5000 employees. "
        "About the role: Update spreadsheets and report to the Regional Director. "
        "Previous multi-site experience is desirable. No P&L ownership.",
        False,
    )
    remit = extract_remit(role_description(job.description))
    assert not remit.multisite
    assert not remit.pnl
    assert remit.site_count is None
    assert remit.team_count is None
    assert score(job).career_fit_score < 60


def test_explicit_scale_and_pnl_improve_scope_without_fabricating_unknowns():
    job = JobInput(
        "Regional Operations Manager",
        "Example",
        "Unknown",
        "Lead multi-site QSR operations and coach restaurant managers. "
        "Own KPI reporting, food safety, inventory and delivery operations. "
        "Requires 10 years of operations experience.",
        False,
    )
    expanded = replace(
        job,
        description=job.description
        + " Lead a portfolio of 25 restaurants and manage 150 staff "
        "with full P&L ownership.",
    )
    before, after = score(job), score(expanded)
    assert after.career_fit_score > before.career_fit_score
    assert after.recommendation.value == "strong_apply"
    remit = extract_remit(expanded.description)
    assert remit.site_count == 25
    assert remit.team_count == 150
    assert (
        "vacancy 25, candidate evidence 30"
        in dimension(after, "leadership_scope").explanation
    )


def test_generic_overlap_and_repeated_boilerplate_cannot_raise_fit():
    job = JobInput(
        "Operations Manager", "Example", "Unknown", "Update a spreadsheet.", False
    )
    padded = replace(
        job, description=job.description + " Operations manager management. " * 30
    )
    assert score(padded).career_fit_score == score(job).career_fit_score


def test_mandatory_evidence_and_optional_sql_are_distinguished(vacancies):
    deliveroo = next(
        j for (provider, _), j in vacancies.items() if provider == "deliveroo"
    )
    before = score(deliveroo)
    assert before.mandatory_failures == ["CRM systems experience"]
    analysis = candidate()
    analysis["source_text"] += "\nManaged Zendesk CRM systems."
    after = score(deliveroo, analysis)
    assert after.mandatory_failures == []
    assert after.career_fit_score > before.career_fit_score
    assert after.occupational_family == "customer_operations"


def test_confirmed_profile_facts_support_explicit_licence_requirements(vacancies):
    job = next(j for (p, _), j in vacancies.items() if p == "raising_canes_uk")
    analysis = candidate()
    analysis["source_text"] = analysis["source_text"].replace(
        "Full UK driving licence and valid right to work in the UK.", ""
    )
    unknown = score(job, analysis)
    assert "Valid driving licence" in unknown.mandatory_failures
    assert "Valid right to work" in unknown.mandatory_failures
    assert dimension(unknown, "mandatory").status == "unknown"
    confirmed = score(
        job, {**analysis, "full_uk_driving_licence": True, "right_to_work_uk": True}
    )
    assert not confirmed.mandatory_failures
    assert confirmed.career_fit_score > unknown.career_fit_score
