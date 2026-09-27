# ruff: noqa: E501
# Explanations are deliberately complete user-facing sentences.

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.job_providers.location import normalize_location
from app.schemas.job_matching import MatchEvidence, MatchRecommendation, MatchScore
from app.services.career_evidence import (
    extract_remit,
    normalized,
    required_years,
    role_description,
)
from app.services.occupational_identity import specialist_evidence, specialist_identity
from app.services.operational_scope import assess_operational_scope

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9&+\-/]{2,}")
_STOP = {
    "and",
    "the",
    "with",
    "for",
    "from",
    "that",
    "this",
    "will",
    "you",
    "your",
    "our",
    "are",
    "have",
    "has",
    "role",
    "team",
    "job",
    "work",
    "experience",
    "years",
    "strong",
    "management",
    "manager",
    "required",
    "essential",
    "must",
    "ability",
    "skills",
}
_WEIGHTS = {
    "role_family": 25,
    "seniority": 15,
    "responsibilities": 25,
    "industry": 10,
    "leadership_scope": 10,
    "location": 0,
    "experience": 5,
    "mandatory": 5,
}
_RESPONSIBILITIES = (
    (
        "Contact-centre operations",
        (
            "call-centre",
            "call centre",
            "contact centre",
            "contact-center",
            "agent performance",
            "service queues",
            "backlog reduction",
        ),
    ),
    (
        "Multi-site operations",
        (
            "multi-site",
            "multi site",
            "multi-unit",
            "multiple sites",
            "portfolio of sites",
            "region of",
            "group of restaurants",
            "regional operations",
        ),
    ),
    (
        "P&L ownership",
        (
            "p&l",
            "profit and loss",
            "ebitdar",
            "full pnl",
            "commercial ownership",
            "commercial accountability",
            "own profit",
        ),
    ),
    (
        "Operational performance",
        (
            "operational performance",
            "operational excellence",
            "service delivery",
            "continuous improvement",
            "operating standards",
            "operational improvement",
            "transformation",
            "guest performance",
        ),
    ),
    (
        "Workforce leadership",
        (
            "lead teams",
            "leading teams",
            "team leadership",
            "people leadership",
            "coach managers",
            "staff development",
            "coach area",
            "coach site",
            "lead managers",
            "lead regional",
            "people development",
            "develop your teams",
            "growing your gms",
            "managing and developing",
            "succession",
        ),
    ),
    (
        "KPI ownership",
        ("kpi", "performance metrics", "performance reporting", "performance targets"),
    ),
    (
        "Budget and cost control",
        (
            "budget control",
            "budget ownership",
            "cost control",
            "labour cost",
            "margin improvement",
        ),
    ),
    (
        "Compliance",
        (
            "food safety",
            "regulatory compliance",
            "health and safety",
            "brand standards",
            "franchise compliance",
        ),
    ),
    (
        "Inventory and supply chain",
        (
            "inventory",
            "stock control",
            "supply chain",
            "supplier management",
            "procurement",
        ),
    ),
    (
        "Franchise operations",
        (
            "franchise operations",
            "franchise partners",
            "franchisees",
            "franchise compliance",
        ),
    ),
    (
        "Delivery operations",
        (
            "delivery operations",
            "last mile",
            "delivery network",
            "delivery performance",
            "marketplace operations",
        ),
    ),
    (
        "Stakeholder management",
        (
            "stakeholder management",
            "cross-functional",
            "senior stakeholders",
            "partner management",
        ),
    ),
)
_SPECIALIST_ROLES = (
    (
        "merchandising",
        ("merchandiser", "merchandising specialist", "visual merchandising"),
    ),
    (
        "estimating",
        ("estimator", "estimating engineer", "quantity surveyor", "cost estimator"),
    ),
    (
        "software",
        (
            "software engineer",
            "software developer",
            "devops",
            "data engineer",
            "frontend developer",
            "backend developer",
        ),
    ),
    (
        "accounting",
        (
            "accountant",
            "accounting manager",
            "finance operations manager",
            "finance manager",
            "financial controller",
            "auditor",
            "bookkeeper",
        ),
    ),
    (
        "clinical",
        (
            "nurse",
            "physician",
            "clinical",
            "therapist",
            "pharmacist",
            "medical practitioner",
        ),
    ),
    ("design", ("graphic designer", "product designer", "ux designer", "art director")),
    (
        "sales",
        (
            "sales assistant",
            "sales representative",
            "account executive",
            "business development representative",
        ),
    ),
    (
        "field_technical",
        (
            "field technician",
            "service technician",
            "field engineer",
            "maintenance engineer",
            "electrical engineer",
            "mechanical engineer",
            "engineering manager",
            "technical operations manager",
        ),
    ),
    (
        "human_resources",
        (
            "human resources",
            "compensation benefits",
            "compensation and benefits",
            "talent acquisition",
            "recruiter",
            "payroll",
            "learning & development",
            "learning and development",
            "training manager",
        ),
    ),
    ("education", ("teacher", "instructor", "academic", "curriculum")),
    (
        "administration",
        ("executive assistant", "administrative assistant", "office assistant"),
    ),
    (
        "emergency_services",
        ("fire fighter", "firefighter", "paramedic", "emergency responder"),
    ),
    ("marketing", ("marketing operations", "marketing manager", "growth marketing")),
    (
        "finance_operations",
        ("billing officer", "billing specialist", "credit controller"),
    ),
    (
        "product_technology",
        ("product operations manager", "product manager", "technical product"),
    ),
    (
        "account_sales",
        ("account manager", "regional account manager", "key account manager"),
    ),
    (
        "risk_specialist",
        ("fraud", "payments risk", "financial crime", "risk operations"),
    ),
)
_SITE_ROLES = (
    "store manager",
    "shop manager",
    "branch manager",
    "site manager",
    "restaurant general manager",
)
_ADJACENT_TITLES = {
    "warehouse_operations": ("warehouse operations manager", "fulfilment manager"),
    "logistics": ("logistics manager", "transport manager"),
    "customer_operations": (
        "customer operations manager",
        "customer service manager",
        "care operations manager",
    ),
    "commercial_operations": ("commercial operations manager",),
    "retail_management": ("retail manager",),
    "hospitality_management": ("hospitality manager",),
}
_OPERATION_TITLES = (
    "operations",
    "operational excellence",
    "area manager",
    "area coach",
    "regional manager",
    "district manager",
    "general manager",
    "franchise manager",
    "performance lead",
    "operations director",
)
_INDUSTRIES = {
    "hospitality/food service": (
        "hospitality",
        "restaurant",
        "qsr",
        "food service",
        "foodservice",
        "catering",
        "coffee",
        "quick service",
    ),
    "franchise": ("franchise", "franchisee", "multi-brand"),
    "delivery": (
        "food delivery",
        "last mile",
        "delivery platform",
        "delivery network",
        "marketplace",
    ),
    "retail": ("retail", "store", "merchandising", "consumer goods"),
    "construction": (
        "construction",
        "estimating",
        "quantity surveying",
        "civil engineering",
    ),
    "technology": ("software", "saas", "technology platform", "cloud"),
    "healthcare": ("healthcare", "clinical", "patient", "hospital"),
}
_MANDATORY_PATTERNS = (
    re.compile(r"\bmust have\s*[:\-]?\s*([^.;\n]{3,180})", re.I),
    re.compile(
        r"([^.;\n]{3,140}(?:licen[cs]e|certification|qualification|degree|registered nurse)[^.;\n]{0,40})\s+(?:is|are)\s+(?:required|essential)\b",
        re.I,
    ),
)


@dataclass(frozen=True, slots=True)
class JobInput:
    title: str
    company: str
    location: str
    description: str
    remote: bool
    workplace_type: str = "unknown"
    requirements: tuple[str, ...] = ()
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None


def _tokens(value: str) -> set[str]:
    return {
        token.casefold()
        for token in _TOKEN_RE.findall(value or "")
        if token.casefold() not in _STOP
    }


def _value(item: Any) -> str:
    return str(item.get("value") if isinstance(item, dict) else item or "").strip()


def _source(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("source_text") or item.get("value") or "").strip()
    return str(item or "").strip()


def _candidate_items(analysis: dict[str, Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    fields = (
        "skills",
        "industries",
        "leadership_scope",
        "achievements",
        "certifications_qualifications",
        "career_track_evidence",
    )
    for field in fields:
        for item in analysis.get(field, []) or []:
            value, source = _value(item), _source(item)
            if value or source:
                result.append({"value": value, "source": source})
    for field in ("role_family", "seniority", "years_experience"):
        item = analysis.get(field)
        if item:
            result.append({"value": _value(item), "source": _source(item)})
    for line in re.split(r"[\r\n]+", str(analysis.get("source_text") or "")):
        if line.strip():
            result.append({"value": line.strip(), "source": line.strip()})
    unique, seen = [], set()
    for item in result:
        key = (item["value"].casefold(), item["source"].casefold())
        if key not in seen:
            unique.append(item)
            seen.add(key)
    return unique


def _contains(text: str, aliases: tuple[str, ...]) -> bool:
    folded = text.casefold()
    return any(
        re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", folded) for alias in aliases
    )


def _sources(items: list[dict[str, str]], aliases: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for alias in aliases:
        for item in items:
            if alias in f"{item['value']} {item['source']}".casefold():
                source = item["source"][:500]
                if source and source not in found:
                    found.append(source)
    return found[:3]


def _component(
    dimension: str,
    score: float,
    status: str,
    explanation: str,
    sources: list[str] | None = None,
) -> MatchEvidence:
    return MatchEvidence(
        dimension=dimension,
        contribution=round(score, 2),
        max_score=float(_WEIGHTS[dimension]),
        status=status,
        explanation=explanation,
        sources=sources or [],
    )


def _explicit_general_manager_scope(title: str, description: str) -> bool:
    if re.search(
        r"\b(?:regional|area|cluster|multi[ -]site|multi-unit)\b", title, re.I
    ):
        return True
    return bool(
        re.search(
            r"\b(?:lead|manage|oversee|responsible for|accountable for)\b"
            r"[^.\n]{0,120}\b(?:multiple sites|multi[ -]site|multi-unit|"
            r"regional portfolio|portfolio of sites|cluster of sites)\b",
            description,
            re.I,
        )
    )


def _role_family(title: str, description: str) -> str:
    folded = title.casefold()
    specialist = specialist_identity(title, description)
    if specialist:
        return specialist
    # Merchant/partner support is not ownership of the partner restaurants.
    if re.search(r"partner|merchant|support", folded) and re.search(
        r"(?:channel|queue|agent|contact.centre|call.centre)", description, re.I
    ):
        return "customer_operations"
    for family, patterns in _SPECIALIST_ROLES:
        if _contains(folded, patterns):
            return family
    if "general manager" in folded:
        if _explicit_general_manager_scope(title, description):
            return "operations_leadership"
        return "retail_site"
    if any(pattern in folded for pattern in _SITE_ROLES):
        return "retail_site"
    if re.search(r"\b(?:head|manager|lead)\b", folded) and re.search(
        r"\b(?:support|customer care)\b", folded
    ):
        return "customer_operations"
    for family, patterns in _ADJACENT_TITLES.items():
        if _contains(folded, patterns):
            return family
    if re.search(r"\b(?:assistant|coordinator|administrator)\b", folded):
        return "junior_support"
    density = sum(_contains(description, aliases) for _, aliases in _RESPONSIBILITIES)
    if _contains(title, _OPERATION_TITLES) or density >= 4:
        return "operations_leadership"
    if "director" in folded or "head of" in folded:
        return "general_leadership"
    return "unknown"


def _seniority(text: str, *, candidate: bool = False) -> int:
    folded = text.casefold()
    levels = (
        (6, ("chief ", "vice president", "vp ")),
        (5, ("director", "head of", "national ")),
        (
            4,
            (
                "regional",
                "area manager",
                "area coach",
                "district",
                "multi-site",
                "multi site",
                "multi-unit",
                "delivery operations lead",
                "marketplace operations manager",
            ),
        ),
        (
            3,
            (
                "senior manager",
                "operations manager",
                "operations lead",
                "general manager",
            ),
        ),
        (2, ("store manager", "site manager", "supervisor", "team lead")),
        (1, ("assistant", "associate", "junior", "coordinator")),
        (3, (" manager", "manager ")),
    )
    for level, markers in levels:
        if any(marker in folded for marker in markers):
            return level
    return 4 if candidate and "senior" in folded else 0


def classify_occupational_family(title: str, description: str) -> str:
    """Return the deterministic occupational family used by matching and monitoring."""
    return _role_family(title, description)


def assess_job_seniority(title: str, description: str) -> str:
    """Return a stable human-readable vacancy seniority band."""
    level = _seniority(title)
    if level == 3 and extract_remit(role_description(description)).multisite:
        level = 4
    return {
        6: "executive",
        5: "director_head",
        4: "regional_multisite",
        3: "manager_lead",
        2: "site_supervisory",
        1: "junior_support",
        0: "unknown",
    }[level]


def _years(value: Any, text: str) -> int | None:
    match = re.search(r"\b(\d{1,2})\+?\b", _value(value)) if value else None
    match = match or re.search(r"\b(\d{1,2})\+?\s+years?", text, re.I)
    return int(match.group(1)) if match else None


def _mandatory(description: str) -> list[str]:
    values: list[str] = []
    for pattern in _MANDATORY_PATTERNS:
        for match in pattern.finditer(description):
            value = re.sub(r"\s+", " ", match.group(1)).strip(" :-")
            if value and value.casefold() not in {item.casefold() for item in values}:
                values.append(value)
    text = normalized(description)
    for pattern, label in (
        (
            r"(?:must (?:have|hold)|possess|requires?|essential)[^.\n]{0,35}(?:driver's|driving) licen[cs]e",
            "Valid driving licence",
        ),
        (r"must hold[^.\n]{0,20}right to work", "Valid right to work"),
        (
            r"(?:knowledgeable|experience|proficien\w*)[^.\n]{0,25}CRM systems?",
            "CRM systems experience",
        ),
        (
            r"previous catering and operational management experience is essential",
            "Catering management experience",
        ),
    ):
        if re.search(pattern, text, re.I):
            values.append(label)
    return list(dict.fromkeys(values))[:10]


def _requirement_supported(requirement: str, candidate_text: str) -> bool:
    if requirement == "Valid driving licence":
        return bool(
            re.search(
                r"(?:full|valid|uk|driver's)\s+(?:uk\s+)?(?:driving |driver's )?licen[cs]e",
                candidate_text,
                re.I,
            )
        )
    if requirement == "Valid right to work":
        return "right to work" in candidate_text
    if requirement == "CRM systems experience":
        return bool(re.search(r"\b(?:crm|zendesk|salesforce)\b", candidate_text, re.I))
    if requirement == "Catering management experience":
        return bool(re.search(r"\b(?:catering|caterer)\b", candidate_text, re.I))
    required, candidate = _tokens(requirement), _tokens(candidate_text)
    specialist = required - {
        "qualification",
        "certification",
        "licence",
        "license",
        "degree",
    }
    compared = specialist or required
    return bool(compared) and compared <= candidate


def _recommendation(
    score: int, mismatch: bool, failures: list[str]
) -> MatchRecommendation:
    if score >= 90 and not mismatch and not failures:
        return MatchRecommendation.STRONG_APPLY
    if score >= 78 and not mismatch and not failures:
        return MatchRecommendation.APPLY
    if score >= 60:
        return MatchRecommendation.REVIEW
    if score >= 35:
        return MatchRecommendation.WEAK_MATCH
    return MatchRecommendation.REJECT


def score_candidate_against_job(
    *, candidate_analysis: dict[str, Any], job: JobInput
) -> MatchScore:
    """Score eight independent suitability dimensions using traceable evidence."""
    items = _candidate_items(candidate_analysis)
    candidate_text = " ".join(f"{x['value']} {x['source']}" for x in items).casefold()
    if candidate_analysis.get("right_to_work_uk") is True:
        candidate_text += " valid right to work in the UK."
    if candidate_analysis.get("full_uk_driving_licence") is True:
        candidate_text += " full UK driving licence."
    candidate_remit = extract_remit(candidate_text)
    responsibility_text = role_description(job.description)
    job_remit = extract_remit(responsibility_text)
    job_text = " ".join((job.title, responsibility_text)).casefold()
    evidence: list[MatchEvidence] = []

    family = _role_family(job.title, job.description)
    scope_assessment = assess_operational_scope(
        job.title, job.description, occupational_family=family
    )
    candidate_operations = (
        sum(
            marker in candidate_text
            for marker in (
                "operations",
                "multi-site",
                "multi site",
                "regional",
                "p&l",
                "operational performance",
                "delivery operations",
                "franchise",
            )
        )
        >= 2
    )
    specialist_sources = specialist_evidence(
        candidate_analysis, family, dict(_SPECIALIST_ROLES).get(family, ())
    )
    unrelated = not specialist_sources and family in {
        "culinary",
        "information_technology",
        "merchandising",
        "estimating",
        "software",
        "accounting",
        "clinical",
        "design",
        "sales",
        "human_resources",
        "education",
        "administration",
        "emergency_services",
        "marketing",
        "finance_operations",
        "field_technical",
        "product_technology",
        "account_sales",
        "risk_specialist",
    }
    adjacent_families = {
        "retail_site",
        "warehouse_operations",
        "logistics",
        "customer_operations",
        "commercial_operations",
        "retail_management",
        "hospitality_management",
    }
    role_sources = _sources(
        items, ("operations", "regional", "multi-site", "multi site")
    )
    if family == "operations_leadership" and candidate_operations:
        role = (
            25 if job_remit.multisite else 23 if job_remit.delivery else 18,
            "matched",
            "Role remit aligns with evidenced multi-site operations"
            if job_remit.multisite
            else "Delivery-network operations align with candidate operations experience"
            if job_remit.delivery
            else "Functional operations are transferable; regional restaurant responsibility is NOT STATED",
        )
    elif family in adjacent_families | {"general_leadership"} and candidate_operations:
        role = (
            18
            if family == "customer_operations"
            and _contains(
                candidate_text,
                ("call-centre", "call centre", "contact centre", "contact-center"),
            )
            else 15
            if family != "retail_site"
            else 12,
            "mismatched",
            f"{family.replace('_', ' ').title()} is adjacent, but not equivalent to senior multi-site operations leadership",
        )
    elif family == "junior_support":
        role = (
            3,
            "mismatched",
            "Junior support work is below the candidate's operations-leadership occupational scope",
        )
    elif specialist_sources:
        role_sources = specialist_sources[:3]
        role = (25, "matched", f"Explicit CV occupational evidence supports {family}")
    elif unrelated:
        role = (
            0,
            "mismatched",
            f"Job requires {family.replace('_', ' ')} occupational experience; explicit CV evidence is UNKNOWN. General management and functional oversight do not establish specialist experience",
        )
    else:
        role = (
            4,
            "unknown",
            "Role family cannot be confirmed as operations leadership from the title and responsibilities",
        )
    evidence.append(_component("role_family", *role, role_sources))

    candidate_level = (
        _seniority(_value(candidate_analysis.get("role_family")), candidate=True)
        or _seniority(_value(candidate_analysis.get("seniority")), candidate=True)
        or _seniority(candidate_text, candidate=True)
    )
    job_level = _seniority(job.title)
    if job_remit.multisite and job_level == 3:
        job_level = 4
    if not job_level:
        seniority = (
            0,
            "unknown",
            "Vacancy seniority and operating scope are not stated clearly",
        )
    elif not candidate_level:
        seniority = (
            0,
            "unknown",
            "Candidate seniority could not be confirmed from accepted CV/profile evidence",
        )
    elif candidate_level == job_level:
        seniority = (
            15,
            "matched",
            "Vacancy seniority is consistent with the candidate's evidenced leadership level",
        )
    elif abs(candidate_level - job_level) == 1:
        seniority = (
            12,
            "matched",
            "Vacancy is one leadership level from the candidate's evidenced seniority",
        )
    elif abs(candidate_level - job_level) == 2:
        seniority = (
            6,
            "mismatched",
            "Vacancy scope is materially below or above the candidate's evidenced leadership level",
        )
    else:
        seniority = (
            1,
            "mismatched",
            "Vacancy and candidate seniority levels are substantially different",
        )
    evidence.append(_component("seniority", *seniority))

    required = [
        (label, aliases)
        for label, aliases in _RESPONSIBILITIES
        if _contains(job_text, aliases)
    ]
    matched = [
        (label, _sources(items, aliases))
        for label, aliases in required
        if _sources(items, aliases)
    ]
    ratio = len(matched) / len(required) if required else 0
    # One generic responsibility cannot earn the same evidence coverage as a
    # substantive remit. More synonyms never create additional dimensions.
    coverage = min(1.0, len(required) / 4)
    if job_remit.multisite and candidate_remit.multisite:
        coverage = min(1.0, max(coverage, 0.9))
    if required:
        resp = (
            25 * ratio * coverage,
            "matched" if ratio >= 0.7 else "mismatched",
            f"Matched {len(matched)} of {len(required)} substantive responsibilities: "
            + (", ".join(label for label, _ in matched) or "none"),
        )
    else:
        resp = (
            0,
            "unknown",
            "No substantive operational responsibilities could be identified in the vacancy",
        )
    evidence.append(
        _component(
            "responsibilities",
            *resp,
            [s for _, sources in matched for s in sources][:5],
        )
    )

    candidate_industries = {
        name
        for name, aliases in _INDUSTRIES.items()
        if _contains(candidate_text, aliases)
    }
    job_industries = {
        name
        for name, aliases in _INDUSTRIES.items()
        if _contains(job.description, aliases)
    }
    direct = candidate_industries & job_industries
    adjacent = "retail" in job_industries and bool(
        candidate_industries & {"hospitality/food service", "franchise"}
    )
    education_catering = bool(
        re.search(
            r"(?:education sector catering|portfolio of schools|school catering)",
            job.description,
            re.I,
        )
    )
    if education_catering and not re.search(
        r"school catering|education catering|contract catering|catering management",
        candidate_text,
    ):
        industry = (
            6,
            "mismatched",
            "Food-service experience transfers, but education/contract-catering experience is NOT STATED in the CV",
        )
    elif direct:
        industry = (10, "matched", f"Sector match: {', '.join(sorted(direct))}")
    elif adjacent:
        industry = (
            4,
            "mismatched",
            "Retail is adjacent to hospitality operations, but direct sector evidence is absent",
        )
    elif job_industries:
        industry = (
            0,
            "mismatched",
            f"No CV evidence supports the vacancy sector: {', '.join(sorted(job_industries))}",
        )
    else:
        industry = (
            0,
            "unknown",
            "Vacancy sector is not stated clearly enough to verify",
        )
    aliases = tuple(a for name in direct for a in _INDUSTRIES[name])
    evidence.append(_component("industry", *industry, _sources(items, aliases)))

    scope_markers = ("multi-site", "multi site", "multi-unit", "regional", "p&l")
    candidate_scope = _sources(items, scope_markers)
    scope_points = 0.0
    scope_details = []
    scope_unknowns = []
    for label, vacancy_spans, candidate_spans, points in (
        (
            "Multi-site/regional responsibility",
            job_remit.multisite,
            candidate_remit.multisite,
            4,
        ),
        ("People leadership", job_remit.people, candidate_remit.people, 2),
        ("Explicit P&L/financial ownership", job_remit.pnl, candidate_remit.pnl, 2),
    ):
        if not vacancy_spans:
            scope_unknowns.append(f"{label} is NOT STATED for this vacancy")
        elif candidate_spans:
            scope_points += points
            scope_details.append(label + ": " + vacancy_spans[0][:220])
        else:
            scope_details.append(
                label
                + " is stated in the vacancy but not supported by candidate evidence"
            )
    if not job_remit.pnl and job_remit.budget and candidate_remit.budget:
        scope_points += 1
        scope_details.append(
            "Commercial/budget responsibility is supported; this does not establish full P&L ownership"
        )
    for label, vacancy_count, candidate_count in (
        ("Site/portfolio count", job_remit.site_count, candidate_remit.site_count),
        ("Team headcount", job_remit.team_count, candidate_remit.team_count),
    ):
        if vacancy_count is None:
            scope_unknowns.append(f"{label} is NOT STATED for this vacancy")
        elif candidate_count is None:
            scope_unknowns.append(
                f"{label}: vacancy states {vacancy_count}; candidate scale is UNKNOWN"
            )
        else:
            scope_points += min(1.0, candidate_count / vacancy_count)
            scope_details.append(
                f"{label}: vacancy {vacancy_count}, candidate evidence {candidate_count}"
            )
    scope_status = "matched" if scope_points else "unknown"
    if family == "retail_site" or (
        candidate_remit.multisite
        and not job_remit.multisite
        and family in adjacent_families
    ):
        scope_status = "mismatched"
        scope_points = min(scope_points, 3)
        scope_details.append(
            "Single-site or functional remit is not equivalent to the candidate's regional restaurant portfolio"
        )
    evidence.append(
        _component(
            "leadership_scope",
            scope_points,
            scope_status,
            "; ".join(scope_details + scope_unknowns),
            candidate_scope,
        )
    )

    preferences = [
        str(x) for x in candidate_analysis.get("preferred_locations", []) if x
    ]
    job_location = normalize_location(
        job.location, remote=job.remote, workplace_type=job.workplace_type
    )
    preferred_locations = [normalize_location(value) for value in preferences]
    geographic_match = any(
        preferred.canonical == job_location.canonical
        or (
            preferred.region_code is not None
            and preferred.region_code == job_location.region_code
        )
        or preferred.display.casefold() in job_location.display.casefold()
        or (
            preferred.country_code == job_location.country_code
            and preferred.canonical.endswith(":countrywide")
        )
        for preferred in preferred_locations
    )
    prefers_uk = any(preferred.is_uk for preferred in preferred_locations)
    anywhere_uk = candidate_analysis.get("anywhere_uk_acceptable")
    london_acceptable = candidate_analysis.get("london_acceptable")
    remote_acceptable = candidate_analysis.get("remote_acceptable")
    hybrid_acceptable = candidate_analysis.get("hybrid_acceptable")
    relocation_acceptable = candidate_analysis.get("relocation_acceptable")
    is_london = "london" in job_location.canonical
    if anywhere_uk is True and job_location.is_uk:
        geographic_match = True
    if london_acceptable is True and is_london:
        geographic_match = True
    if relocation_acceptable is True and job_location.is_uk is True:
        geographic_match = True
    arrangement_mismatch = bool(
        (job.remote and remote_acceptable is False)
        or (job.workplace_type == "hybrid" and hybrid_acceptable is False)
        or (is_london and london_acceptable is False)
    )
    geographic_mismatch = bool(
        arrangement_mismatch
        or (
            preferences
            and not geographic_match
            and (not job.remote or (prefers_uk and job_location.is_uk is False))
        )
    )
    if geographic_match:
        location = (
            0,
            "matched",
            f"Location — {job.location} matches a saved candidate location/preference",
        )
    elif geographic_mismatch:
        location = (
            0,
            "mismatched",
            f"Location — vacancy geography {job.location} is not supported by saved preferences",
        )
    elif job.remote:
        if remote_acceptable is True and job_location.is_uk is not False:
            location = (
                0,
                "matched",
                f"Location — remote work is explicitly acceptable ({job.location})",
            )
        else:
            location = (
                0,
                "unknown",
                f"Location — remote geography/eligibility is unconfirmed (listed: {job.location})",
            )
    else:
        location = (
            0,
            "unknown",
            f"Location — unconfirmed; no saved candidate preference supports {job.location}",
        )
    evidence.append(_component("location", *location, preferences[:3]))

    candidate_years = _years(
        candidate_analysis.get("years_experience")
        or candidate_analysis.get("profile_years_experience"),
        candidate_text,
    )
    job_years = required_years(job.description)
    if job_years is None:
        exp = (
            0,
            "unknown",
            "Vacancy does not state a measurable experience requirement",
        )
    elif candidate_years is None:
        exp = (
            0,
            "unknown",
            f"Vacancy asks for {job_years}+ years; candidate years are not confirmed",
        )
    elif unrelated:
        exp = (
            0,
            "mismatched",
            f"Candidate's {candidate_years} years are not evidence of experience in the vacancy's {family} discipline",
        )
    elif candidate_years >= job_years:
        exp = (
            5,
            "matched",
            f"Candidate's evidenced {candidate_years} years meets the {job_years}-year requirement in a compatible function",
        )
    else:
        exp = (
            0,
            "mismatched",
            f"Candidate has {candidate_years} evidenced years; vacancy asks for {job_years}",
        )
    evidence.append(_component("experience", *exp))

    requirements = _mandatory("\n".join((job.description, *job.requirements)))
    failures = [
        req for req in requirements if not _requirement_supported(req, candidate_text)
    ]
    if unrelated:
        requirements.append(
            f"{family.replace('_', ' ').title()} occupational experience"
        )
        failures.append(requirements[-1])
    if not requirements:
        mandatory = (
            0,
            "unknown",
            "No explicit mandatory qualification, licence, or specialist requirement was detected",
        )
    elif failures:
        mandatory = (
            0,
            "unknown",
            f"Candidate evidence is UNKNOWN for mandatory requirements: {'; '.join(failures)}",
        )
    else:
        mandatory = (
            5,
            "matched",
            "All explicitly stated mandatory requirements have supporting candidate evidence",
        )
    evidence.append(_component("mandatory", *mandatory))

    strengths = [
        x.explanation
        for x in evidence
        if x.dimension != "location" and x.status == "matched"
    ]
    gaps = [
        x.explanation
        for x in evidence
        if x.dimension != "location" and x.status == "mismatched"
    ]
    uncertainty = scope_unknowns + [
        x.explanation
        for x in evidence
        if x.dimension != "location" and x.status == "unknown"
    ]
    if (job.salary_min or job.salary_max) and not candidate_analysis.get("salary_min"):
        uncertainty.append(
            "Salary — vacancy range is available, but candidate preference is not stated"
        )
    elif not (job.salary_min or job.salary_max):
        uncertainty.append("Salary — information is unavailable for comparison")
    raw = round(
        100 * sum(x.contribution for x in evidence if x.dimension != "location") / 95
    )
    caps: list[tuple[int, str]] = []
    if unrelated:
        caps.append(
            (24, "Fundamental occupational role-family mismatch caps the score at 24")
        )
    elif family == "unknown":
        caps.append((34, "Unconfirmed role-family compatibility caps the score at 34"))
    if family == "retail_site" and candidate_level >= 4:
        caps.append(
            (
                59,
                "Single-site versus regional/multi-site scope mismatch caps the score at 59",
            )
        )
    if scope_assessment.tier == "potential_operations":
        caps.append(
            (
                69,
                "Relevant operations title without substantive stated ownership caps the score at 69",
            )
        )
    if family in adjacent_families - {"retail_site"}:
        caps.append(
            (
                69,
                "Adjacent management work without evidenced multi-site scope caps the score at 69",
            )
        )
    if family == "junior_support":
        caps.append((34, "Junior individual-contributor scope caps the score at 34"))
    if job_level and candidate_level and abs(candidate_level - job_level) >= 3:
        caps.append((49, "Substantial seniority mismatch caps the score at 49"))
    if required and ratio < 0.35:
        caps.append(
            (
                49,
                "Fewer than 35% of substantive responsibilities are supported; score capped at 49",
            )
        )
    if failures:
        functional_gaps = {"CRM systems experience", "Catering management experience"}
        cap = 69 if set(failures) <= functional_gaps else 49
        caps.append(
            (
                cap,
                f"Unconfirmed mandatory requirements require review; score capped at {cap}",
            )
        )
    score = min([raw, *(cap for cap, _ in caps)]) if caps else raw
    uncertainty.extend(message for cap, message in caps if raw > cap)
    recommendation = _recommendation(score, unrelated, failures)
    next_actions = {
        MatchRecommendation.STRONG_APPLY: "Strong apply — review evidence and prepare materials",
        MatchRecommendation.APPLY: "Apply — review gaps before preparing materials",
        MatchRecommendation.REVIEW: "Consider — human review of gaps and unknowns required",
        MatchRecommendation.WEAK_MATCH: "Weak match — deprioritize unless strategically relevant",
        MatchRecommendation.REJECT: "Do not recommend — fundamental fit issues identified",
    }
    tracks = [str(x) for x in candidate_analysis.get("career_tracks", []) if x]
    location_evidence = next(x for x in evidence if x.dimension == "location")
    location_fit = {
        "matched": "good",
        "mismatched": "outside_preference",
    }.get(location_evidence.status, "unknown")
    return MatchScore(
        overall_score=score,
        career_fit_score=score,
        location_fit=location_fit,
        location_fit_explanation=location_evidence.explanation,
        recommendation=recommendation,
        occupational_family=family,
        seniority_assessment=assess_job_seniority(job.title, job.description),
        strengths=list(dict.fromkeys(strengths)),
        gaps=list(dict.fromkeys(gaps)),
        mandatory_failures=list(dict.fromkeys(failures)),
        evidence=evidence,
        uncertainty=list(dict.fromkeys(uncertainty)),
        recommended_cv_track=tracks[0] if tracks else None,
        recommended_next_action=next_actions[recommendation],
    )
