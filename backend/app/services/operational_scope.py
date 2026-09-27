from __future__ import annotations

import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class OperationalScopeAssessment:
    tier: str
    stated_evidence: tuple[str, ...]
    unknowns: tuple[str, ...]

    def as_dict(self) -> dict:
        return asdict(self)


_SENIOR_TITLE = re.compile(
    r"\b(?:regional|area|district|cluster|multi[ -]?site|multi-unit|"
    r"head of operations|operations director|director of operations)\b",
    re.I,
)
_SITE_TITLE = re.compile(
    r"\b(?:assistant|deputy|shift|hourly|store manager|shop manager|"
    r"restaurant manager|restaurant leader|general manager|site manager)\b",
    re.I,
)
_OWNERSHIP = re.compile(
    r"\b(?:own|owns|owning|lead|leads|leading|manage|manages|managing|"
    r"oversee|oversees|overseeing|responsible for|accountable for|direct|directs)\b",
    re.I,
)
_MULTISITE = re.compile(
    r"\b(?:multiple sites|multi[ -]?site|multi-unit|portfolio of sites|"
    r"group of (?:restaurants|sites|stores|pubs)|cluster of sites|"
    r"across (?:the )?(?:region|area|estate|markets|locations)|"
    r"regional portfolio|district|territory)\b",
    re.I,
)
_PEOPLE = re.compile(
    r"\b(?:lead|manage|coach|develop|mentor|direct)\w*\b[^.\n]{0,100}"
    r"\b(?:managers|leaders|teams|people|employees|colleagues|reports)\b",
    re.I,
)
_PNL = re.compile(
    r"\b(?:p&l|profit and loss|commercial accountability|budget ownership|"
    r"own\w* (?:the )?(?:budget|profitability|margin))\b",
    re.I,
)
_OPERATIONS = re.compile(
    r"\b(?:operational performance|operational excellence|service delivery|"
    r"delivery network|marketplace operations|franchise operations|"
    r"continuous improvement|operating standards|kpis?)\b",
    re.I,
)


def _explicit_excerpt(pattern: re.Pattern[str], text: str, label: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    start = max(0, text.rfind(".", 0, match.start()) + 1)
    end = text.find(".", match.end())
    if end < 0:
        end = min(len(text), match.end() + 120)
    excerpt = re.sub(r"\s+", " ", text[start : end + 1]).strip()
    return f"{label}: {excerpt[:240]}"


def assess_operational_scope(
    title: str, description: str, *, occupational_family: str
) -> OperationalScopeAssessment:
    """Classify stated vacancy scope without inferring missing responsibility."""
    combined = f"{title}. {description}"
    evidence: list[str] = []
    for pattern, label in (
        (_MULTISITE, "Geographic/site scope"),
        (_PEOPLE, "People leadership"),
        (_PNL, "Commercial/P&L ownership"),
        (_OPERATIONS, "Operational ownership"),
    ):
        if excerpt := _explicit_excerpt(pattern, combined, label):
            evidence.append(excerpt)

    has_multisite_ownership = bool(
        _SENIOR_TITLE.search(title)
        or re.search(
            rf"{_OWNERSHIP.pattern}[^.\n]{{0,140}}{_MULTISITE.pattern}",
            description,
            re.I,
        )
    )
    ownership_dimensions = sum(
        bool(pattern.search(description)) for pattern in (_PEOPLE, _PNL, _OPERATIONS)
    )
    unrelated = occupational_family in {
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
        "junior_support",
    }
    if unrelated:
        tier = "unrelated"
    elif occupational_family == "retail_site" or _SITE_TITLE.search(title):
        tier = "single_site_frontline"
    elif has_multisite_ownership and ownership_dimensions >= 1:
        tier = "senior_multisite_ownership"
    elif occupational_family == "operations_leadership" and ownership_dimensions >= 2:
        tier = "operational_leadership"
    elif occupational_family == "operations_leadership":
        tier = "potential_operations"
    else:
        tier = "unknown"

    unknowns: list[str] = []
    if not _MULTISITE.search(combined):
        unknowns.append("Multi-site or geographic accountability is NOT STATED")
    if not _PEOPLE.search(description):
        unknowns.append("People-leadership scope is NOT STATED")
    if not _PNL.search(description):
        unknowns.append("P&L or budget ownership is NOT STATED")
    return OperationalScopeAssessment(tier, tuple(evidence), tuple(unknowns))
