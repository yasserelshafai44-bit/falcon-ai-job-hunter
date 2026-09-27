import json
import shutil
import subprocess
from pathlib import Path

import pytest
from app.ai.providers.text_factory import get_text_generation_provider
from app.services.grounded_materials import (
    MaterialEvidenceError,
    complete,
    plan_material,
    render_material,
    validate_material,
)
from app.services.prompt_builder import build_resume_prompt

CV = """ALEX EXAMPLE
Regional Operations Manager
PROFESSIONAL SUMMARY
Restaurant operations leader with 14 years of experience in multi-site QSR.
CORE SKILLS
Full P&L accountability across 18 restaurants and annual sales of £4m.
Managed 180 colleagues and developed six restaurant managers.
Reduced labour costs by 8% while maintaining food safety standards.
Led franchise delivery operations handling 2,400 daily orders.
EDUCATION
Diploma in Hospitality Management, Example College, 2011.
"""


def evidence(value: str, source: str | None = None) -> dict:
    return {"value": value, "source_text": source or value, "confidence": 0.99}


def payload(kind: str = "resume") -> dict:
    lines = CV.splitlines()
    return {
        "document_type": kind,
        "max_words": 350,
        "candidate": {
            "source_text": CV,
            "profile_full_name": "Alex Example",
            "professional_summary": lines[3],
            "achievements": [evidence(lines[7]), evidence(lines[8])],
            "leadership_scope": [evidence(lines[5]), evidence(lines[6])],
            "skills": [],
            "certifications_qualifications": [evidence(lines[10])],
        },
        "job": {
            "title": "Area Restaurant Leader",
            "company": "Employer from database",
            "description": "Lead multiple restaurants with full P&L accountability. "
            "Manage financial performance and develop restaurant managers.",
            "requirements": ["Budget planning and food safety governance."],
        },
    }


@pytest.mark.parametrize("kind", ["resume", "cover_letter"])
def test_materials_use_source_evidence_and_actual_vacancy(kind: str) -> None:
    content = render_material(payload(kind))
    assert "Employer from database" in content
    assert "Area Restaurant Leader" in content
    assert "18 restaurants" in content
    assert "£4m" in content
    assert "180 colleagues" in content
    assert "Verified achievement included" not in content
    assert "Evidence-based operations leader tailored" not in content
    assert "Raising Cane" not in content
    assert len(content.split()) <= 350
    if kind == "resume":
        assert "Selected Achievements" in content
        assert "14 years" in content
    else:
        assert "Dear Hiring Team" in content
        assert "Your vacancy states:" not in content


def test_parsed_hallucinations_and_unverified_profile_claims_are_not_used() -> None:
    data = payload()
    data["candidate"]["achievements"].extend(
        [
            evidence("Managed 999 outlets", "Managed 999 outlets"),
            evidence(
                "Managed 999 outlets",
                "Managed 180 colleagues and developed six restaurant managers.",
            ),
        ]
    )
    data["candidate"]["profile_years_experience"] = 99
    data["candidate"]["accepted_profile_enrichment"] = {
        "certifications_qualifications": [evidence("MBA from Harvard")]
    }
    data["job"]["description"] += " Must have an MBA and responsibility for £50m."
    content = render_material(data)
    assert "999" not in content
    assert "99 years" not in content
    assert "Harvard" not in content
    assert "£50m" not in content
    assert "180 colleagues" in content


def test_missing_source_fails_instead_of_filling_in_generic_claims() -> None:
    data = payload()
    data["candidate"].pop("source_text")
    with pytest.raises(MaterialEvidenceError, match="original CV text"):
        render_material(data)


def test_parser_truncation_uses_complete_cv_sentence() -> None:
    data = payload()
    original = "Managed 180 colleagues and developed six restaurant managers."
    data["candidate"]["leadership_scope"] = [evidence(original[:15])]
    assert original in render_material(data)


@pytest.mark.asyncio
async def test_live_factory_uses_evidence_provider_and_full_context() -> None:
    data = payload()
    system, user = build_resume_prompt(
        candidate_analysis=data["candidate"],
        job_title=data["job"]["title"],
        company=data["job"]["company"],
        job_description=data["job"]["description"],
        job_requirements=data["job"]["requirements"],
        tone="professional",
        max_words=350,
    )
    assert json.loads(user)["candidate"]["source_text"] == CV
    provider = get_text_generation_provider()
    assert provider.name == "evidence_grounded"
    result = await provider.generate_text(system_prompt=system, user_prompt=user)
    assert "18 restaurants" in result


def test_frontend_material_regeneration() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required for frontend behavioral tests")
    result = subprocess.run(
        [node, str(Path(__file__).with_name("frontend_application_materials.mjs"))],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("kind", ["resume", "cover_letter"])
def test_quality_gate_rejects_changed_metrics_and_placeholder_text(kind: str) -> None:
    data = payload(kind)
    content = render_material(data)
    for replacement in ("999 restaurants", "verified achievement included"):
        with pytest.raises(MaterialEvidenceError):
            validate_material(content.replace("18 restaurants", replacement), data)


def test_soft_wrapped_bullets_are_completed_before_rewriting() -> None:
    data = payload()
    data["candidate"]["source_text"] += (
        "\nSELECTED ACHIEVEMENTS\n"
        "• Led a 42-outlet, multi-brand portfolio generating approximately £6m "
        "in monthly sales, with full P&L\naccountability.\n"
        "• Recruited, trained and developed 220 frontline and management staff "
        "across multiple market entries and\npromotions.\n"
        "• Reduced operating costs by 7% through supplier and contract\n"
        "renegotiation.\n"
        "• Managed an incomplete portfolio with\n"
        "EDUCATION\n"
        "Example College | 2011\n"
    )
    plan = plan_material(data)
    claims = [item["text"] for item in plan["claims"]]
    assert all(complete(claim) for claim in claims)
    assert any("42 outlets with full P&L accountability" in claim for claim in claims)
    assert any("supporting market entries and staff promotions." in claim for claim in claims)
    assert not any("incomplete portfolio" in claim for claim in claims)
    assert len(claims) == len(set(claims))
    assert len(claims) <= 8
    content = render_material(data)
    with pytest.raises(MaterialEvidenceError):
        validate_material(content + "\n- Managed an incomplete portfolio with", data)
    bullet = next(line for line in content.splitlines() if line.startswith("- "))
    with pytest.raises(MaterialEvidenceError):
        validate_material(content + "\n" + bullet, data)


def test_long_copied_vacancy_block_is_rejected() -> None:
    data = payload("cover_letter")
    content = render_material(data)
    copied = " ".join(content.split("\n\n")[2].split()[:20])
    data["job"]["description"] += " " + copied
    with pytest.raises(MaterialEvidenceError):
        render_material(data)


@pytest.mark.parametrize("ending", ["with", "and", "P&L", "approximately"])
def test_dangling_bullets_are_not_considered_complete(ending: str) -> None:
    assert not complete("Led a regional restaurant portfolio " + ending + ".")
