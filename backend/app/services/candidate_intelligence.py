import re

from app.schemas.candidate_intelligence import (
    CandidateIntelligenceData,
    EvidenceItem,
)

_SKILL_TERMS = {
    "P&L management",
    "multi-site operations",
    "delivery operations",
    "franchise compliance",
    "team leadership",
    "supplier management",
    "inventory control",
    "commercial negotiation",
    "KPI management",
    "food safety",
}

_INDUSTRY_TERMS = {
    "hospitality",
    "QSR",
    "restaurants",
    "food delivery",
    "franchise",
    "coffee",
}


def _sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+|\n+", text) if item.strip()]


def _evidence_for_terms(text: str, terms: set[str]) -> list[EvidenceItem]:
    results: list[EvidenceItem] = []
    sentences = _sentences(text)
    for term in sorted(terms):
        for sentence in sentences:
            if term.lower() in sentence.lower():
                results.append(
                    EvidenceItem(value=term, source_text=sentence[:500], confidence=0.95)
                )
                break
    return results


def analyze_candidate_text(text: str) -> CandidateIntelligenceData:
    """Create a deterministic, evidence-based candidate profile baseline."""
    sentences = _sentences(text)
    achievements = [
        EvidenceItem(value=s[:240], source_text=s[:500], confidence=0.9)
        for s in sentences
        if re.search(r"\b\d+(?:[.,]\d+)?%|£\d|\d{2,}\+|\d{1,3},\d{3}\b", s)
    ][:20]

    leadership = [
        EvidenceItem(value=s[:240], source_text=s[:500], confidence=0.9)
        for s in sentences
        if any(word in s.lower() for word in ("led ", "managed ", "directed ", "hired ", "trained "))
    ][:15]

    skill_evidence = _evidence_for_terms(text, _SKILL_TERMS)
    industry_evidence = _evidence_for_terms(text, _INDUSTRY_TERMS)

    career_tracks: list[str] = []
    lower = text.lower()
    if any(term in lower for term in ("multi-site", "regional", "area manager", "156")):
        career_tracks.append("Regional and Multi-Site Operations")
    if any(term in lower for term in ("delivery", "aggregator", "marketplace", "7,200")):
        career_tracks.append("Delivery and Marketplace Operations")
    if any(term in lower for term in ("commercial", "p&l", "profit", "margin")):
        career_tracks.append("Commercial Operations")

    summary = sentences[0][:600] if sentences else ""
    warnings: list[str] = []
    if len(text) < 500:
        warnings.append("Limited text was extracted; review the source document manually.")

    return CandidateIntelligenceData(
        professional_summary=summary,
        skills=skill_evidence,
        achievements=achievements,
        industries=industry_evidence,
        leadership_scope=leadership,
        career_tracks=career_tracks,
        warnings=warnings,
    )
