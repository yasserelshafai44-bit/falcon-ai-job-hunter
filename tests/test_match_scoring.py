# ruff: noqa: E501

from app.services.match_scoring import JobInput, score_candidate_against_job


def candidate() -> dict:
    return {
        "years_experience": {
            "value": "22",
            "source_text": "22+ years of experience in QSR operations.",
        },
        "seniority": {
            "value": "Senior",
            "source_text": "Regional Operations Director",
        },
        "role_family": {
            "value": "Regional Operations Director",
            "source_text": "Regional Operations Director",
        },
        "skills": [
            {
                "value": "multi-site operations",
                "source_text": "Led multi-site operations across 156 outlets.",
            },
            {
                "value": "P&L management",
                "source_text": "Held full P&L ownership and budget control.",
            },
            {
                "value": "delivery operations",
                "source_text": "Directed delivery operations and marketplace performance.",
            },
            {
                "value": "KPI management",
                "source_text": "Owned KPI management and performance reporting.",
            },
            {
                "value": "team leadership",
                "source_text": "Led regional teams and coached site managers.",
            },
            {
                "value": "inventory control",
                "source_text": "Improved inventory and supplier management.",
            },
            {
                "value": "food safety",
                "source_text": "Accountable for food safety and franchise compliance.",
            },
            {
                "value": "stakeholder management",
                "source_text": "Managed senior stakeholders and franchise partners.",
            },
        ],
        "industries": [
            {
                "value": "QSR",
                "source_text": "22+ years across QSR and restaurant operations.",
            },
            {
                "value": "franchise",
                "source_text": "Led multi-brand franchise operations.",
            },
        ],
        "leadership_scope": [
            {
                "value": "156-outlet portfolio",
                "source_text": "Led a regional 156-outlet portfolio with full P&L.",
            }
        ],
        "career_tracks": [
            "Regional and Multi-Site Operations",
            "Commercial Operations",
        ],
        "preferred_locations": ["London", "UK"],
    }


def job(
    title: str, description: str, *, location: str = "London", remote: bool = False
) -> JobInput:
    return JobInput(
        title=title,
        company="Real Employer",
        location=location,
        description=description,
        remote=remote,
    )


def component(result, name: str):
    return next(item for item in result.evidence if item.dimension == name)


def test_aligned_regional_operations_role_scores_high_with_exact_components() -> None:
    result = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "Regional Operations Manager",
            "Lead multi-site QSR restaurant operations with P&L ownership, KPI "
            "performance, budget control, food safety, inventory, franchise "
            "partners and coaching of site managers. Requires 10 years of "
            "operations experience.",
        ),
    )

    assert result.overall_score >= 85
    assert result.recommendation.value in {"strong_apply", "apply"}
    assert component(result, "role_family").contribution == 25
    assert component(result, "responsibilities").contribution >= 20
    assert component(result, "industry").contribution == 10
    assert component(result, "leadership_scope").sources
    assert {item.dimension for item in result.evidence} == {
        "role_family",
        "seniority",
        "responsibilities",
        "industry",
        "leadership_scope",
        "location",
        "experience",
        "mandatory",
    }


def test_delivery_operations_role_remains_plausible() -> None:
    result = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "Delivery Operations Lead",
            "Own delivery network performance, service delivery, KPIs, partner "
            "management and cross-functional operational improvement in a food "
            "delivery marketplace.",
        ),
    )

    assert result.overall_score >= 60
    assert result.recommendation.value in {"strong_apply", "apply", "review"}


def test_unrelated_specialist_roles_cannot_win_on_generic_words() -> None:
    descriptions = {
        "Beauty Merchandiser": "Manage commercial KPIs, inventory and stakeholder relationships for beauty merchandising.",
        "Estimator": "Lead commercial operations, budgets, KPIs and teams. Must have construction estimating experience.",
        "Senior Software Engineer": "Lead a software team, own delivery KPIs and stakeholder management.",
        "Clinical Operations Manager": "Lead clinical operations and teams. Must have a registered nursing licence.",
        "Sales Assistant": "Support store operations, customer KPIs, inventory and the management team.",
        "Field Technician": "Own field operations, service delivery KPIs and regional customer relationships.",
    }
    results = {
        title: score_candidate_against_job(
            candidate_analysis=candidate(), job=job(title, description)
        )
        for title, description in descriptions.items()
    }

    assert all(result.overall_score <= 29 for result in results.values())
    assert all(result.recommendation.value == "reject" for result in results.values())
    assert all(
        component(result, "role_family").status == "mismatched"
        for result in results.values()
    )


def test_misleading_operations_keywords_do_not_override_title_occupation() -> None:
    result = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "Senior Estimator",
            "This estimator manages operational excellence, multi-site stakeholder "
            "delivery, P&L, budgets, KPIs and teams across a regional portfolio.",
        ),
    )

    assert result.overall_score <= 29
    assert result.recommendation.value == "reject"


def test_junior_operations_role_is_capped_by_seniority_mismatch() -> None:
    result = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "Operations Assistant",
            "Assist one manager with daily operations and reporting.",
        ),
    )

    assert component(result, "seniority").status == "mismatched"
    assert result.recommendation.value not in {"strong_apply", "apply"}


def test_geographic_mismatch_is_separate_from_career_fit() -> None:
    local = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "Regional Operations Manager",
            "Lead multi-site restaurant operations, P&L, KPIs and regional teams.",
            location="London, UK",
        ),
    )
    distant = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "Regional Operations Manager",
            "Lead multi-site restaurant operations, P&L, KPIs and regional teams.",
            location="Sydney, Australia",
        ),
    )

    assert component(distant, "location").status == "mismatched"
    assert distant.location_fit == "outside_preference"
    assert distant.career_fit_score == local.career_fit_score
    assert distant.overall_score == local.overall_score


def test_single_site_store_manager_is_penalised_for_scope() -> None:
    result = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "Store Manager Bunbury",
            "Run one retail store, lead store staff, manage inventory, sales KPIs "
            "and customer service in Bunbury.",
            location="Bunbury, Australia",
        ),
    )

    assert result.overall_score <= 54
    assert result.recommendation.value in {"weak_match", "reject"}
    assert component(result, "seniority").status == "mismatched"
    assert component(result, "leadership_scope").status == "mismatched"
    assert component(result, "location").status == "mismatched"


def test_mandatory_specialist_requirement_caps_recommendation() -> None:
    result = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "Head of Operations",
            "Lead multi-site restaurant operations, P&L and regional teams. "
            "Must have a CIMA qualification.",
        ),
    )

    assert result.mandatory_failures
    assert result.overall_score <= 49
    assert result.recommendation.value not in {"strong_apply", "apply"}
    assert component(result, "mandatory").status == "unknown"


def test_accessibility_and_soft_skill_language_is_not_a_mandatory_failure() -> None:
    result = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "Operations Manager",
            "Lead operational teams and KPI delivery. Essential behaviours include "
            "curiosity and communication. Tell us if adjustments are required during "
            "the recruitment process.",
        ),
    )

    assert result.mandatory_failures == []
    assert component(result, "mandatory").status == "unknown"


def test_missing_information_is_unknown_not_matched() -> None:
    result = score_candidate_against_job(
        candidate_analysis={},
        job=job(
            "Operations Coordinator",
            "Support day-to-day work.",
            remote=True,
            location="Remote",
        ),
    )

    assert component(result, "location").status == "unknown"
    assert component(result, "experience").status == "unknown"
    assert component(result, "mandatory").status == "unknown"
    assert all(item.status != "matched" for item in result.evidence)


def test_duplicate_evidence_does_not_inflate_any_component_or_score() -> None:
    base = candidate()
    duplicated = candidate()
    duplicated["skills"] += [item.copy() for item in duplicated["skills"]]
    vacancy = job(
        "Regional Operations Manager",
        "Lead multi-site restaurant operations, P&L, KPIs, inventory and regional teams.",
    )

    single = score_candidate_against_job(candidate_analysis=base, job=vacancy)
    duplicate = score_candidate_against_job(candidate_analysis=duplicated, job=vacancy)

    assert duplicate.overall_score == single.overall_score
    assert [item.contribution for item in duplicate.evidence] == [
        item.contribution for item in single.evidence
    ]


def test_specific_evidence_only_improves_the_relevant_component() -> None:
    vacancy = job(
        "Regional Operations Manager",
        "Lead multi-site QSR operations with P&L ownership and inventory control.",
    )
    without_inventory = candidate()
    without_inventory["skills"] = [
        item
        for item in without_inventory["skills"]
        if item["value"] != "inventory control"
    ]
    before = score_candidate_against_job(
        candidate_analysis=without_inventory, job=vacancy
    )
    after = score_candidate_against_job(candidate_analysis=candidate(), job=vacancy)

    changed = [
        item.dimension
        for item in after.evidence
        if item.contribution != component(before, item.dimension).contribution
    ]
    assert changed == ["responsibilities"]


def test_ranking_order_prioritises_substantive_fit() -> None:
    vacancies = [
        job(
            "Beauty Merchandiser",
            "Manage inventory, commercial KPIs and a retail team.",
        ),
        job(
            "Store Manager Bunbury",
            "Manage one retail store, staff and inventory.",
            location="Bunbury",
        ),
        job(
            "Delivery Operations Lead",
            "Own food delivery operations, KPIs, delivery performance and partners.",
        ),
        job(
            "Regional Operations Manager",
            "Lead multi-site QSR operations, P&L, KPIs, budgets, inventory and regional teams.",
        ),
    ]
    ranked = sorted(
        (
            (
                vacancy.title,
                score_candidate_against_job(
                    candidate_analysis=candidate(), job=vacancy
                ).overall_score,
            )
            for vacancy in vacancies
        ),
        key=lambda item: item[1],
        reverse=True,
    )

    assert [title for title, _ in ranked] == [
        "Regional Operations Manager",
        "Delivery Operations Lead",
        "Store Manager Bunbury",
        "Beauty Merchandiser",
    ]


def test_learning_and_development_manager_is_occupationally_rejected() -> None:
    result = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "Learning & Development Manager",
            "Lead training delivery, manager capability, KPIs and regional leadership.",
        ),
    )

    assert result.occupational_family == "human_resources"
    assert result.career_fit_score <= 24
    assert result.recommendation.value == "reject"


def test_general_manager_requires_explicit_multisite_scope_for_strong_fit() -> None:
    site = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "General Manager - Lakeside Cafe",
            "Run this cafe, lead its team, own its budget and deliver site KPIs.",
        ),
    )
    regional = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "General Manager - Regional Operations",
            "Lead a regional portfolio of 20 restaurant sites and coach site managers.",
        ),
    )

    assert site.occupational_family == "retail_site"
    assert site.career_fit_score <= 59
    assert site.recommendation.value not in {"strong_apply", "apply"}
    assert regional.occupational_family == "operations_leadership"
    assert regional.career_fit_score > site.career_fit_score


def test_general_manager_experience_requirement_does_not_invent_role_scope() -> None:
    result = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "General Manager - Lakeside Cafe",
            "Run the cafe and its team with site budget accountability. Previous "
            "experience in a multi site management role is required.",
        ),
    )

    assert result.occupational_family == "retail_site"
    assert result.career_fit_score <= 59
    assert result.recommendation.value not in {"strong_apply", "apply"}


def test_corporate_general_manager_is_commercial_when_remit_is_commercial() -> None:
    result = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "General Manager, UK & Ireland",
            "Lead commercial performance and market strategy across the region. "
            "Own new business, account management, partnerships, enterprise "
            "opportunities, pipeline and forecasting for a B2B SaaS business.",
        ),
    )

    assert result.occupational_family == "commercial_operations"


def test_micro_fulfilment_site_leader_is_warehouse_operations() -> None:
    result = score_candidate_against_job(
        candidate_analysis=candidate(),
        job=job(
            "Site Leader",
            "Lead a micro-fulfilment centre. Own order fulfilment, inventory "
            "management, warehouse safety and last-mile customer delivery.",
        ),
    )

    assert result.occupational_family == "warehouse_operations"
