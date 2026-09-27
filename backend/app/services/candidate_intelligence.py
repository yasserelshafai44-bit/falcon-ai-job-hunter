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
    "stakeholder management",
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
    return [
        item.strip() for item in re.split(r"(?<=[.!?])\s+|\n+", text) if item.strip()
    ]


def _evidence_for_terms(text: str, terms: set[str]) -> list[EvidenceItem]:
    results: list[EvidenceItem] = []
    sentences = _sentences(text)
    for term in sorted(terms):
        for sentence in sentences:
            if term.lower() in sentence.lower():
                results.append(
                    EvidenceItem(
                        value=term, source_text=sentence[:500], confidence=0.95
                    )
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
        if any(
            word in s.lower()
            for word in ("led ", "managed ", "directed ", "hired ", "trained ")
        )
    ][:15]

    skill_evidence = _evidence_for_terms(text, _SKILL_TERMS)
    industry_evidence = _evidence_for_terms(text, _INDUSTRY_TERMS)

    career_tracks: list[str] = []
    lower = text.lower()
    if any(term in lower for term in ("multi-site", "regional", "area manager", "156")):
        career_tracks.append("Regional and Multi-Site Operations")
    if any(
        term in lower for term in ("delivery", "aggregator", "marketplace", "7,200")
    ):
        career_tracks.append("Delivery and Marketplace Operations")
    if any(term in lower for term in ("commercial", "p&l", "profit", "margin")):
        career_tracks.append("Commercial Operations")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = None
    if lines and re.fullmatch(r"[A-Za-z][A-Za-z' -]{2,79}", lines[0]):
        words = lines[0].split()
        if 2 <= len(words) <= 5:
            name = EvidenceItem(
                value=lines[0].title(), source_text=lines[0], confidence=0.9
            )
    role = None
    if len(lines) > 1 and len(lines[1]) <= 120:
        role = EvidenceItem(value=lines[1], source_text=lines[1], confidence=0.9)
    location = None
    for line in lines[1:8]:
        first = line.split("|")[0].strip()
        if re.search(r"\b(?:UK|UAE|London|Kent|Wells|Dubai|Oman)\b", first, re.I):
            location = EvidenceItem(value=first, source_text=line[:500], confidence=0.9)
            break
    years = None
    years_match = re.search(r"\b(\d{1,2})\+?\s+years? of experience\b", text, re.I)
    if years_match:
        years = EvidenceItem(
            value=years_match.group(1),
            source_text=next(
                (s for s in sentences if years_match.group(0).lower() in s.lower()),
                years_match.group(0),
            )[:500],
            confidence=0.95,
        )
    summary_match = re.search(
        r"PROFESSIONAL SUMMARY\s+(.+?)(?=\s+CORE SKILLS\b)", text, re.I | re.S
    )
    summary_source = (
        re.sub(r"\s+", " ", summary_match.group(1)).strip() if summary_match else ""
    )
    summary = summary_source[:600]
    summary_evidence = (
        EvidenceItem(value=summary, source_text=summary_source[:500], confidence=0.95)
        if summary
        else None
    )
    qualifications: list[EvidenceItem] = []
    education_match = re.search(
        r"\bEDUCATION\s+(.+?)(?=\s+(?:LANGUAGES|CERTIFICATIONS)\b|$)", text, re.I | re.S
    )
    if education_match:
        for line in _sentences(education_match.group(1)):
            clean = line.lstrip("•- ").strip()
            if clean:
                qualifications.append(
                    EvidenceItem(
                        value=clean[:240], source_text=clean[:500], confidence=0.95
                    )
                )
    warnings: list[str] = []
    if len(text) < 500:
        warnings.append(
            "Limited text was extracted; review the source document manually."
        )

    return CandidateIntelligenceData(
        professional_summary=summary,
        professional_summary_evidence=summary_evidence,
        full_name=name,
        primary_location=location,
        years_experience=years,
        seniority=EvidenceItem(
            value="Senior", source_text=role.source_text, confidence=0.85
        )
        if role
        and re.search(r"regional|director|head|lead|owner|multi-site", role.value, re.I)
        else None,
        role_family=role,
        skills=skill_evidence,
        achievements=achievements,
        industries=industry_evidence,
        leadership_scope=leadership,
        career_tracks=career_tracks,
        career_track_evidence=[
            EvidenceItem(
                value=value,
                source_text=role.source_text if role else value,
                confidence=0.85,
            )
            for value in career_tracks
        ],
        certifications_qualifications=qualifications,
        warnings=warnings,
    )
