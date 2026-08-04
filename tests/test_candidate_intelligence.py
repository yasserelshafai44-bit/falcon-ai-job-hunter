from pathlib import Path

from app.services.candidate_intelligence import analyze_candidate_text


def test_deterministic_candidate_analysis_extracts_evidence() -> None:
    text = """
    Operations leader with multi-site operations and P&L management.
    Managed 156 restaurants and directed delivery operations processing 7,200 orders daily.
    Reduced costs by 12% through commercial negotiation.
    """
    result = analyze_candidate_text(text)

    assert "Regional and Multi-Site Operations" in result.career_tracks
    assert "Delivery and Marketplace Operations" in result.career_tracks
    assert result.achievements
    assert any(item.value == "P&L management" for item in result.skills)
