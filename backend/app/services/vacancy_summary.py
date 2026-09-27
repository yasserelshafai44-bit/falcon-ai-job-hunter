from __future__ import annotations

import re
from typing import Any

from app.models.discovered_job import DiscoveredJob

NOT_STATED = "NOT STATED"

_BOUNDARY = re.compile(
    r"(?<=[.!?])\s+|(?=\b(?:Guide|Champion(?:ing)?|Coach|Mentor|Define|Monitor|"
    r"Collaborate|Drive|Communicate|Support(?:ing)?|Design(?:ing)?|Transform(?:ing)?|"
    r"Deliver(?:ing)?|Partnering|Manage|Lead|Acting|Good organisational|Strong "
    r"written|Proven ability|Strong eye|A self-starter|Exceptional stakeholder|Minimum "
    r"\d|Experience working)\b)"
)
_HEADINGS = re.compile(
    r"\b(?:The Role|The Team|Core Responsibilities|Strategic Planning|"
    r"Stakeholder Engagement & Communication|What You['’]ll Be Doing|"
    r"What You['’]ll Need to Thrive|The required skills include\b:?|"
    r"The desired experiences include\b:?|Why Join Us\??)",
)

_EMPLOYER_OFFERING = re.compile(
    r"\b(?:we offer|what we offer|our benefits|employee benefits?|employee assistance|"
    r"assistance program(?:me)?|virtual gp|wellbeing|wellness|pension|holiday|"
    r"annual leave|staff discount|employee discount|discounts?|perk(?:s)?|"
    r"life assurance|private medical|"
    r"cycle to work|company car|bonus scheme|reward platform|apprenticeship(?:s)?|"
    r"classroom learning|learning and development|learning & development|"
    r"training and development|"
    r"development programme|development program|career development|career progression|"
    r"training provided|full training|ongoing training|we(?:'|’)ll train|"
    r"we will train)\b",
    re.IGNORECASE,
)


def _is_employer_offering(text: str) -> bool:
    return bool(_EMPLOYER_OFFERING.search(text))


def _evidence_chunks(chunks: list[str]) -> list[str]:
    """Exclude employer offerings before classifying candidate-facing evidence."""
    return [chunk for chunk in chunks if not _is_employer_offering(chunk)]


def _is_experience_or_qualification_requirement(text: str) -> bool:
    if _is_employer_offering(text):
        return False
    lowered = text.lower()
    patterns = (
        r"\b(?:minimum|at least|preferably)\s+\d+\s*(?:\+\s*)?years?\b",
        r"\b\d+\s*(?:\+\s*)?years?\s+(?:of\s+)?(?:relevant\s+)?experience\b",
        r"\b(?:previous|prior|proven|demonstrable|relevant|required|preferred|essential)\s+"
        r"(?:[\w/&+.-]+\s+){0,5}experience\b",
        r"\bexperience\s+(?:in|as|within|of|with)\b",
        r"\b(?:degree|professional qualification|qualified|licen[cs]e|"
        r"certification|certificate)\b",
        r"\b(?:must|required|essential)\b.{0,100}\b(?:skill|credential|qualification|"
        r"experience|licen[cs]e|certification)\b",
    )
    return any(re.search(pattern, lowered) for pattern in patterns)


def _clean(value: str) -> str:
    value = _HEADINGS.sub("", value)
    return re.sub(r"\s+", " ", value).strip(" :-–—•").removesuffix(" ?")


def _chunks(description: str) -> list[str]:
    return [
        cleaned for part in _BOUNDARY.split(description) if (cleaned := _clean(part))
    ]


def _unique(items: list[str], limit: int = 5) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        item = _clean(item)
        if not item:
            continue
        if len(item) > 280:
            item = item[:277].rsplit(" ", 1)[0] + "…"
        key = re.sub(r"\W+", " ", item.lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
        if len(result) == limit:
            break
    return result


def _select_by_categories(
    chunks: list[str], categories: list[tuple[str, ...]]
) -> list[str]:
    selected: list[str] = []
    used: set[int] = set()
    for terms in categories:
        match: tuple[int, str] | None = None
        for term in terms:
            match = next(
                (
                    (index, chunk)
                    for index, chunk in enumerate(chunks)
                    if index not in used and term in chunk.lower()
                ),
                None,
            )
            if match:
                break
        if match:
            index, chunk = match
            selected.append(chunk)
            used.add(index)
    return _unique(selected)


def _salary(job: DiscoveredJob | None) -> str:
    if job is None or (job.salary_min is None and job.salary_max is None):
        return NOT_STATED
    currency = job.currency or ""
    if job.salary_min is not None and job.salary_max is not None:
        return f"{currency} {job.salary_min:,}–{job.salary_max:,}".strip()
    value = job.salary_min if job.salary_min is not None else job.salary_max
    qualifier = "from" if job.salary_min is not None else "up to"
    return f"{qualifier} {currency} {value:,}".strip()


def build_human_review_summary(
    vacancy: dict[str, Any], job: DiscoveredJob | None = None
) -> dict[str, Any]:
    """Summarise employer-stated vacancy evidence without match or candidate data."""
    description = str(vacancy.get("description") or "")
    chunks = _chunks(description)
    evidence_chunks = _evidence_chunks(chunks)
    purpose_source = description
    for marker in ("The Team", "Core Responsibilities", "What You’ll Be Doing"):
        purpose_source = purpose_source.split(marker, 1)[0]
    purpose = _unique(_evidence_chunks(_chunks(purpose_source)), limit=2)

    responsibilities = _select_by_categories(
        evidence_chunks,
        [
            ("day-to-day contact centre", "contact centre", "contact-center"),
            ("commercial objectives", "commercial performance", "strategic"),
            ("kpi", "financial metrics"),
            ("transformation", "continuous improvement", "change"),
            ("communicate strategic plans", "stakeholder engagement"),
        ],
    )
    if not responsibilities:
        responsibilities = _unique(
            [
                chunk
                for chunk in evidence_chunks
                if re.match(
                    r"^(?:Lead|Manage|Guide|Deliver|Drive|Develop|Support|Design|"
                    r"Monitor|Collaborate|Coordinate|Oversee|Own|Ensure)",
                    chunk,
                    re.IGNORECASE,
                )
            ]
        )

    explicit_requirements = [
        str(item)
        for item in vacancy.get("requirements") or []
        if not _is_employer_offering(str(item))
    ]
    requirement_chunks = [
        chunk
        for chunk in evidence_chunks
        if any(
            term in chunk.lower()
            for term in (
                "required",
                "must ",
                "proven ability",
                "strong written",
                "good organisational",
                "exceptional stakeholder",
                "minimum ",
                "experience working",
                "qualification",
                "degree",
                "licence",
                "license",
            )
        )
    ]
    mandatory = _unique(
        explicit_requirements
        + _select_by_categories(
            requirement_chunks,
            [
                ("stakeholder",),
                ("organisational", "organizational"),
                ("communication",),
                ("proven ability",),
                ("detail",),
                ("minimum ", "experience working"),
            ],
        )
    )
    leadership = _unique(
        [
            chunk
            for chunk in evidence_chunks
            if any(
                term in chunk.lower()
                for term in (
                    "manage a team",
                    "team members",
                    "team leads",
                    "people leadership",
                    "coach",
                    "mentor",
                    "p&l",
                    "profit and loss",
                    "regional",
                    "across sites",
                    "multi-site",
                    "geographic",
                )
            )
        ]
    )
    experience = _unique(
        [
            chunk
            for chunk in evidence_chunks
            if _is_experience_or_qualification_requirement(chunk)
        ]
    )
    constraints = _unique(
        [
            chunk
            for chunk in evidence_chunks
            if any(
                term in chunk.lower()
                for term in (
                    "based in ",
                    "travel",
                    "shift",
                    "office attendance",
                    "days in the office",
                    "on-site",
                    "onsite",
                    "weekend",
                    "driving licence",
                    "driving license",
                )
            )
        ]
    )
    workplace = job.workplace_type if job and job.workplace_type else "unknown"
    return {
        "source": "EMPLOYER-STATED VACANCY DATA ONLY",
        "title": vacancy.get("title") or NOT_STATED,
        "employer": vacancy.get("company") or NOT_STATED,
        "location": vacancy.get("location") or NOT_STATED,
        "workplace_type": workplace.upper() if workplace != "unknown" else NOT_STATED,
        "role_purpose": purpose,
        "main_responsibilities": responsibilities,
        "mandatory_requirements": mandatory,
        "leadership_scope": leadership,
        "experience_qualifications": experience,
        "salary": _salary(job),
        "practical_constraints": constraints,
    }
