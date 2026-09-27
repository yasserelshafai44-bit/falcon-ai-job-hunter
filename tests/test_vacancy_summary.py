from app.models.discovered_job import DiscoveredJob
from app.services.vacancy_summary import NOT_STATED, build_human_review_summary


def test_summary_uses_only_stored_employer_vacancy_evidence() -> None:
    vacancy = {
        "title": "Operations Manager – New Partner Experience",
        "company": "Deliveroo",
        "location": "Manchester - Main Office",
        "description": (
            "The Role Oversee and develop high-performing operational teams while "
            "delivering long-term strategic frameworks for commercial performance. "
            "Based in Manchester and reporting to the Head of New Partner Experience. "
            "Core Responsibilities Guide daily activities across operational "
            "functions. "
            "Supporting day-to-day Contact Centre operations. "
            "Monitor KPIs and financial metrics to support strategic decisions. "
            "Drive transformation and continuous improvement initiatives. "
            "Communicate operational insights to executive teams and commercial "
            "partners. "
            "Manage a team of Onboarding Agents and mentor junior Team Leads. "
            "The required skills include: Exceptional stakeholder management. "
            "The desired experiences include: Minimum 3 years of experience driving "
            "performance improvements. Minimum 5 years in people leadership roles. "
            "Experience working within Contact Centre environments."
        ),
        "requirements": [],
    }
    job = DiscoveredJob(workplace_type="onsite")

    summary = build_human_review_summary(vacancy, job)

    rendered = " ".join(
        value if isinstance(value, str) else " ".join(value)
        for value in summary.values()
    ).lower()
    assert summary["title"] == vacancy["title"]
    assert summary["location"] == "Manchester - Main Office"
    assert summary["workplace_type"] == "ONSITE"
    assert "operational teams" in rendered
    assert "contact centre" in rendered
    assert "commercial performance" in rendered
    assert "kpis and financial metrics" in rendered
    assert "continuous improvement" in rendered
    assert "stakeholder management" in rendered
    assert "onboarding agents" in rendered
    assert len(summary["role_purpose"]) <= 2
    assert len(summary["main_responsibilities"]) <= 5
    assert len(summary["mandatory_requirements"]) <= 5
    assert "79" not in rendered
    assert "strong_apply" not in rendered


def test_summary_marks_missing_employer_evidence_not_stated() -> None:
    summary = build_human_review_summary(
        {
            "title": "Operations Manager",
            "company": "Example Employer",
            "location": "",
            "description": "",
            "requirements": [],
        }
    )

    assert summary["location"] == NOT_STATED
    assert summary["workplace_type"] == NOT_STATED
    assert summary["salary"] == NOT_STATED
    assert summary["role_purpose"] == []
    assert summary["main_responsibilities"] == []
    assert summary["mandatory_requirements"] == []
    assert summary["leadership_scope"] == []
    assert summary["experience_qualifications"] == []
    assert summary["practical_constraints"] == []


def test_caterlink_benefits_and_training_are_not_candidate_requirements() -> None:
    summary = build_human_review_summary(
        {
            "title": "Operations Manager",
            "company": "Caterlink - WSH Group UK",
            "location": "Kent",
            "description": (
                "Lead catering operations across a portfolio of schools. "
                "Our Employee Assistance Program and Virtual GP benefits support you. "
                "We offer apprenticeships and classroom learning through our "
                "development programme."
            ),
            "requirements": [],
        }
    )

    assert summary["experience_qualifications"] == []
    rendered = " ".join(
        item
        for key in (
            "role_purpose",
            "main_responsibilities",
            "mandatory_requirements",
            "leadership_scope",
            "experience_qualifications",
            "practical_constraints",
        )
        for item in summary[key]
    ).lower()
    assert "employee assistance" not in rendered
    assert "virtual gp" not in rendered
    assert "apprenticeship" not in rendered
    assert "classroom learning" not in rendered


def test_benefits_do_not_override_genuine_candidate_requirements() -> None:
    summary = build_human_review_summary(
        {
            "title": "Regional Operations Manager",
            "company": "Example Employer",
            "location": "South East England",
            "description": (
                "Manage operational performance across multiple sites. "
                "Previous multi-site hospitality experience is required. "
                "A full UK driving licence is essential. "
                "Benefits include pension, employee discounts, wellbeing programmes, "
                "25 days holiday and company-provided training and development."
            ),
            "requirements": [
                "Previous multi-site hospitality experience is required.",
                "Benefits include pension and employee discounts.",
            ],
        }
    )

    experience = " ".join(summary["experience_qualifications"]).lower()
    mandatory = " ".join(summary["mandatory_requirements"]).lower()
    assert "multi-site hospitality experience" in experience
    assert "multi-site hospitality experience" in mandatory
    assert "pension" not in experience + mandatory
    assert "discount" not in experience + mandatory
    assert "training and development" not in experience + mandatory
