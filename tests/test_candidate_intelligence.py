from app.services.candidate_intelligence import analyze_candidate_text


def test_deterministic_candidate_analysis_extracts_evidence() -> None:
    text = """
    Operations leader with multi-site operations and P&L management.
    Managed 156 restaurants and directed delivery operations.
    Processed 7,200 orders daily.
    Reduced costs by 12% through commercial negotiation.
    """
    result = analyze_candidate_text(text)

    assert "Regional and Multi-Site Operations" in result.career_tracks
    assert "Delivery and Marketplace Operations" in result.career_tracks
    assert result.achievements
    assert any(item.value == "P&L management" for item in result.skills)


def test_profile_fields_are_evidence_backed_and_summary_skips_name() -> None:
    text = """JANE SAMPLE
Regional Operations Director
London, UK | jane@example.com
PROFESSIONAL SUMMARY
Regional operations leader with 18+ years of experience across hospitality and QSR.
CORE SKILLS
Team leadership and multi-site operations.
EDUCATION
• Example University — Bachelor's Degree, Business
LANGUAGES
English — Fluent
"""
    result = analyze_candidate_text(text)

    assert result.full_name.value == "Jane Sample"
    assert result.full_name.source_text == "JANE SAMPLE"
    assert result.primary_location.value == "London, UK"
    assert result.years_experience.value == "18"
    assert result.professional_summary.startswith("Regional operations leader")
    assert result.professional_summary != result.full_name.value
    assert result.role_family.value == "Regional Operations Director"
    assert result.seniority.value == "Senior"
    assert result.certifications_qualifications[0].source_text
    assert all(item.confidence > 0 for item in result.skills)


def test_missing_profile_fields_remain_unknown() -> None:
    result = analyze_candidate_text("Team leadership and inventory control.")

    assert result.full_name is None
    assert result.primary_location is None
    assert result.years_experience is None
    assert result.professional_summary == ""
