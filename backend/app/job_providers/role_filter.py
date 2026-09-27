import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RoleClassification:
    family: str
    eligible: bool
    reason: str


_NEGATIVE_TITLE_FAMILIES = (
    (
        "junior_site_management",
        (
            "assistant restaurant general manager",
            "assistant general manager",
            "operations assistant",
        ),
    ),
    (
        "beauty_merchandising",
        ("beauty merchandiser", "visual merchandiser", "merchandising assistant"),
    ),
    ("sales_assistant", ("sales assistant", "retail assistant", "shop assistant")),
    (
        "field_technical",
        (
            "field technician",
            "service technician",
            "maintenance engineer",
            "field engineer",
        ),
    ),
    (
        "estimating",
        ("estimator", "estimating engineer", "quantity surveyor", "cost estimator"),
    ),
    (
        "software_it",
        (
            "software engineer",
            "software developer",
            "devops",
            "data engineer",
            "frontend",
            "backend engineer",
            "it support",
            "systems engineer",
            "machine learning engineer",
            "data scientist",
        ),
    ),
    (
        "healthcare_clinical",
        (
            "nurse",
            "physician",
            "clinical",
            "therapist",
            "pharmacist",
            "medical practitioner",
        ),
    ),
    (
        "finance_accounting",
        (
            "accountant",
            "accounting manager",
            "finance manager",
            "financial controller",
            "auditor",
            "bookkeeper",
        ),
    ),
    (
        "specialist_sales",
        (
            "sales representative",
            "account executive",
            "business development representative",
            "business development manager",
            "account manager",
        ),
    ),
    (
        "specialist_profession",
        (
            "solicitor",
            "lawyer",
            "architect",
            "graphic designer",
            "product designer",
            "recruiter",
            "learning & development",
            "learning and development",
            "training manager",
            "human resources",
            "people manager",
        ),
    ),
)
_TARGET_TITLES = (
    "operations manager",
    "operations lead",
    "head of operations",
    "operations director",
    "regional manager",
    "area manager",
    "area coach",
    "district manager",
    "multi-site manager",
    "multi site manager",
    "general manager",
    "franchise manager",
    "delivery operations",
)
_SCOPE_MARKERS = (
    "multi-site",
    "multi site",
    "multi-unit",
    "multiple sites",
    "regional operations",
    "p&l",
    "profit and loss",
    "operational performance",
    "delivery network",
    "marketplace operations",
    "franchise operations",
    "coach managers",
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


def classify_role(title: str, description: str = "") -> RoleClassification:
    """Classify title first so generic description words cannot override occupation."""
    normalized_title = re.sub(r"\s+", " ", title.casefold()).strip()
    for family, markers in _NEGATIVE_TITLE_FAMILIES:
        if any(marker in normalized_title for marker in markers):
            return RoleClassification(
                family, False, f"title identifies {family.replace('_', ' ')}"
            )

    if "general manager" in normalized_title:
        has_multi_site_scope = _explicit_general_manager_scope(title, description)
        return RoleClassification(
            "operations_leadership" if has_multi_site_scope else "site_management",
            True,
            (
                "general manager role with explicit multi-site scope"
                if has_multi_site_scope
                else "adjacent single-site general manager role"
            ),
        )

    if normalized_title == "operations" or any(
        marker in normalized_title for marker in _TARGET_TITLES
    ):
        return RoleClassification(
            "operations_leadership", True, "target operations title"
        )

    folded_description = description.casefold()
    scope_count = sum(marker in folded_description for marker in _SCOPE_MARKERS)
    management_title = any(
        marker in normalized_title for marker in ("manager", "director", "head", "lead")
    )
    if management_title and scope_count >= 2:
        return RoleClassification(
            "adjacent_operations_management",
            True,
            "management title with substantive operating scope",
        )
    if any(
        marker in normalized_title
        for marker in (
            "store manager",
            "site manager",
            "branch manager",
            "restaurant manager",
        )
    ):
        return RoleClassification(
            "site_management", True, "adjacent site-management role"
        )
    return RoleClassification(
        "unknown",
        False,
        "insufficient evidence of a target or adjacent operations role",
    )
