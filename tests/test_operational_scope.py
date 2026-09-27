from types import SimpleNamespace

from app.services.calibration import select_validation_sample
from app.services.operational_scope import assess_operational_scope


def test_scope_requires_stated_multisite_ownership() -> None:
    senior = assess_operational_scope(
        "Regional Operations Manager",
        "Lead operational performance across 18 restaurants and coach site managers.",
        occupational_family="operations_leadership",
    )
    assert senior.tier == "senior_multisite_ownership"
    assert senior.stated_evidence

    site = assess_operational_scope(
        "General Manager",
        "Run this restaurant. Previous multi-site management experience is desirable.",
        occupational_family="retail_site",
    )
    assert site.tier == "single_site_frontline"


def test_scope_preserves_unknowns_instead_of_inventing_evidence() -> None:
    assessment = assess_operational_scope(
        "Operations Manager",
        "Help the operation perform well.",
        occupational_family="operations_leadership",
    )
    assert assessment.tier == "potential_operations"
    assert assessment.stated_evidence == ()
    assert (
        "Multi-site or geographic accountability is NOT STATED" in assessment.unknowns
    )
    assert "P&L or budget ownership is NOT STATED" in assessment.unknowns


def test_validation_sampler_is_small_deterministic_and_diverse() -> None:
    rows = []
    titles = (
        "Regional Operations Manager",
        "Area Manager",
        "Operations Manager",
        "General Manager",
        "Restaurant Manager",
        "Field Technician",
    )
    for index in range(30):
        title = titles[index % len(titles)]
        family = (
            "field_technical"
            if title == "Field Technician"
            else "retail_site"
            if "General" in title or "Restaurant Manager" in title
            else "operations_leadership"
        )
        job = SimpleNamespace(
            id=index + 1,
            provider=("deliveroo", "kfc_uk", "wsh_group_uk")[index % 3],
            title=title,
            description=(
                "Lead operational performance across multiple sites and coach managers."
                if "Regional" in title or "Area" in title
                else "Run this restaurant and manage the team."
            ),
        )
        match = SimpleNamespace(
            overall_score=(34, 59, 61, 77, 79, 89)[index % 6],
            recommendation=("reject", "weak_match", "review", "apply")[index % 4],
            occupational_family=family,
        )
        rows.append((match, job))

    first = select_validation_sample(rows, 12)
    second = select_validation_sample(rows, 12)
    assert [item[1].id for item in first] == [item[1].id for item in second]
    assert len(first) == 12
    assert len({item[1].provider for item in first}) == 3
    assert len({item[2]["scope_assessment"]["tier"] for item in first}) >= 3
