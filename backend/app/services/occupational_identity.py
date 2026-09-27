"""Identify specialist work, not departments an operations leader oversees."""

import re

SPECIALIST_TITLES = {
    "culinary": (
        r"(?:executive |head |sous |commis )?chef(?: manager| de partie)?|cook|"
        r"culinary (?:operations )?(?:manager|director|lead)|"
        r"kitchen (?:manager|production manager)"
    ),
    "software": r"software (?:engineer|developer)|devops|data engineer",
    "information_technology": (
        r"IT (?:operations |service |support )?"
        r"(?:manager|director|engineer|technician)|head of IT|"
        r"systems administrator|network engineer|cybersecurity (?:analyst|manager)"
    ),
    "accounting": (
        r"accountant|finance (?:operations )?(?:manager|director)|"
        r"financial controller|head of finance|bookkeeper|auditor"
    ),
    "human_resources": (
        r"HR (?:operations )?(?:manager|director|business partner|advisor)|"
        r"head of HR|human resources (?:manager|director)|"
        r"recruiter|payroll (?:manager|specialist)"
    ),
    "sales": (
        r"sales (?:operations )?(?:manager|director|executive|representative)|"
        r"head of sales|business development (?:manager|director)"
    ),
    "field_technical": (
        r"(?:mechanical|electrical|maintenance|field|civil) engineer|"
        r"engineering (?:manager|director)|head of engineering|"
        r"technical (?:operations )?(?:manager|director)|(?:service|field) technician"
    ),
    "clinical": (
        r"(?:registered )?nurse|physician|pharmacist|therapist|"
        r"clinical (?:manager|director|lead)|medical practitioner"
    ),
}


def specialist_identity(title: str, description: str) -> str | None:
    for family, pattern in SPECIALIST_TITLES.items():
        if re.search(rf"\b(?:{pattern})\b", title, re.I):
            return family
    # A neutral title must not hide an explicit professional prerequisite.
    # Department mentions, collaboration and oversight are not prerequisites.
    for family, pattern in SPECIALIST_TITLES.items():
        if re.search(
            rf"\b(?:must (?:be|have experience as)|required to be|"
            rf"(?:essential|required):?\s+(?:experience as|qualified as)|"
            rf"(?:proven|professional) experience as)\s+(?:an?\s+)?"
            rf"(?:qualified\s+)?(?:{pattern})\b",
            description,
            re.I,
        ):
            return family
    return None


def specialist_evidence(
    analysis: dict, family: str, aliases: tuple[str, ...] = ()
) -> list[str]:
    """Only explicit first-hand occupation claims support specialist identity.

    Raw CV takes priority over inferred analysis labels. Managing chefs, menus,
    food safety or IT suppliers never establishes a chef/IT career.
    """
    pattern = SPECIALIST_TITLES.get(family) or "|".join(re.escape(x) for x in aliases)
    if not pattern:
        return []
    source = str(analysis.get("source_text") or "")
    if not source:
        role = analysis.get("role_family") or ""
        source = str(role.get("source_text") or "") if isinstance(role, dict) else ""
    evidence = []
    for line in re.split(r"[\r\n.;]+", source):
        if re.search(
            r"\b(?:no|not|never|without|aspiring|seeking|desired)\b", line, re.I
        ):
            continue
        if re.search(
            rf"^\s*(?:(?:19|20)\d{{2}}\s*[-–|:]\s*)?"
            rf"(?:(?:senior|executive|head|regional|qualified|professional)\s+)*"
            rf"(?:{pattern})\b(?=\s*(?:$|[|,:–—-]|at\b|with\b|(?:19|20)\d{{2}}))|"
            rf"\b(?:worked|employed|served|qualified|certified) as "
            rf"(?:an? )?(?:{pattern})\b|"
            rf"\b\d+ years? (?:of )?experience as (?:an? )?(?:{pattern})\b",
            line,
            re.I,
        ):
            evidence.append(line.strip())
    return evidence
