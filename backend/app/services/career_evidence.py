"""Extract stated remit, rather than company scale or generic title keywords."""

from __future__ import annotations

import re
from dataclasses import dataclass


def normalized(text: str) -> str:
    return text.translate(str.maketrans({"’": "'", "‑": "-", "–": "-", "&": " and "}))


def role_description(text: str) -> str:
    """Separate actual responsibilities from employer history and benefits."""
    start = re.search(
        r"about the role|your role at|job description|we are looking for|"
        r"in this role you|what you['’]ll be doing",
        text,
        re.I,
    )
    if start:
        text = text[start.start() :]
    end = re.search(
        r"\b(?:requirements for success|requirements|qualifications|why join us|"
        r"keeping it real|what['’]s in it for you|there are many advantages|"
        r"additional information|all your information)\b",
        text,
        re.I,
    )
    return text[: end.start()] if end else text


def remit_sentences(text: str) -> list[str]:
    sentences = re.split(r"[.!?\n]+", normalized(text))
    return [
        s.strip()
        for s in sentences
        if s.strip()
        and not re.search(
            r"\b(?:previous|prior) experience|\bexperience (?:in|of|with)|"
            r"\b(?:company|business) (?:has|operates|serves|caters)|"
            r"\bwe (?:serve|operate|have|proudly serve)|"
            r"\b(?:benefits|discount|equal opportunity|disability|"
            r"recruitment process)\b",
            s,
            re.I,
        )
    ]


_OWN = (
    r"\b(?:lead|leads|leading|led|manage|manages|managed|managing|direct|directs|"
    r"directed|directing|oversee|oversees|overseeing|own|owns|owned|owning|run|ran|"
    r"held|responsible|responsibility|accountable|accountability|"
    r"support and challenge)\b"
)
_SITES = (
    r"(?:restaurants?|outlets?|sites?|locations?|schools?|hotels?|pubs?|"
    r"stores?|franchisees?)"
)
_MULTI = (
    rf"\b(?:multi[ -](?:site|unit)|multiple (?:\w+ )?{_SITES}|"
    rf"(?:group|portfolio|region|cluster) (?:schools )?of (?:\w+ ){{0,3}}{_SITES}|"
    rf"(?:\d+|five|six|ten|twenty)[ -](?:\w+[ -]){{0,2}}{_SITES}|"
    rf"across (?:\d+ )?{_SITES}|regional (?:\w+ ){{0,2}}(?:operations|portfolio))\b"
)
_PEOPLE = (
    r"\b(?:managers|leaders|gms|rgms|teams|people|employees|colleagues|staff|reports)\b"
)


@dataclass(frozen=True)
class Remit:
    multisite: tuple[str, ...]
    people: tuple[str, ...]
    pnl: tuple[str, ...]
    budget: tuple[str, ...]
    delivery: tuple[str, ...]
    site_count: int | None
    team_count: int | None


def extract_remit(text: str) -> Remit:
    sentences = remit_sentences(text)

    def collect(pattern: str, *, ownership: bool = True) -> tuple[str, ...]:
        return tuple(
            s
            for s in sentences
            if re.search(pattern, s, re.I)
            and (not ownership or re.search(_OWN, s, re.I))
            and not re.search(
                r"\b(?:no|without|not responsible for)\b[^,;]{0,35}" + pattern, s, re.I
            )
        )

    multisite = collect(_MULTI)
    people = collect(
        rf"(?:{_OWN}|\bcoach\w*|\bdevelop\w*|\bmentor\w*)[^.;]{{0,100}}{_PEOPLE}",
        ownership=False,
    )
    pnl = collect(
        r"\b(?:p\s*and\s*l|profit and loss|ebitdar?|full commercial accountability)\b"
    )
    budget = collect(
        r"\b(?:budgets?|commercial performance|profit results|profitability|"
        r"profit|margins?)\b"
    )
    delivery = collect(
        r"\b(?:delivery (?:operations|network|performance|quality)|last[ -]mile|"
        r"courier operations|marketplace operations)\b"
    )

    def count(pattern: str, spans: tuple[str, ...]) -> int | None:
        values = [
            int(m.group(1).replace(",", ""))
            for s in spans
            for m in re.finditer(pattern, s, re.I)
        ]
        return max(values) if values else None

    sites = count(rf"\b(\d[\d,]*)\+?[ -](?:\w+[ -]){{0,2}}{_SITES}\b", multisite)
    team = count(
        r"\b(\d[\d,]*)\+?\s+(?:(?:frontline|management|and)\s+){0,3}(?:staff|people|employees|colleagues|reports)\b",
        people,
    )
    return Remit(multisite, people, pnl, budget, delivery, sites, team)


def required_years(text: str) -> int | None:
    # A company's age or benefits tenure is not an applicant requirement.
    patterns = (
        r"\b(\d{1,2})\+?\s+years?'?\s+(?:of\s+)?experience\b",
        r"\b(?:requires?|minimum|at least)\s+(\d{1,2})\+?\s+years?\b",
        r"\b(\d{1,2})\+?\s+years?\s+of\s+[^.;\n]{0,60}\bexperience\b",
    )
    values = [
        int(m.group(1))
        for pattern in patterns
        for m in re.finditer(pattern, normalized(text), re.I)
    ]
    return max(values) if values else None
