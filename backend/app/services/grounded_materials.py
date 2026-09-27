"""Polished application drafting from complete, source-linked career statements.

The renderer uses a closed set of meaning-preserving edits and evidence-gated
connecting sentences. Employer wording never becomes candidate experience.
"""

import re
from typing import Any


class MaterialEvidenceError(ValueError):
    pass


PLACEHOLDERS = (
    "tailored to the target role", "verified achievement included",
    "your vacancy states:", "my relevant experience includes:",
    "evidence-based operations leader tailored",
)
ACTIONS = (
    "Led", "Managed", "Directed", "Reduced", "Cut", "Improved", "Increased",
    "Grew", "Hired", "Recruited", "Developed", "Launched", "Founded",
    "Controlled", "Implemented", "Exceeded", "Reactivated", "Coordinated",
    "Supervised", "Delivered", "Oversaw", "Oversee", "Monitored", "Built",
    "Trained", "Established", "Negotiated", "Drove", "Own", "Manage", "Held",
)
HEADINGS = re.compile(
    r"^(?:PROFESSIONAL SUMMARY|PROFILE|SUMMARY|CORE SKILLS|KEY SKILLS|"
    r"SELECTED PERFORMANCE ACHIEVEMENTS|SELECTED ACHIEVEMENTS|KEY ACHIEVEMENTS|"
    r"WORK HISTORY|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EMPLOYMENT HISTORY|"
    r"CAREER HISTORY|EXPERIENCE|EDUCATION|QUALIFICATIONS|CERTIFICATIONS|"
    r"LANGUAGES|REFERENCES)$", re.I,
)


def clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"^(?:[•·]\s*|[-*]\s+)", "", text)


def sentences(text: str) -> list[str]:
    # A PDF line break is not a sentence boundary.
    return [clean(part) for part in re.split(r"(?<=[.!?])\s+", clean(text)) if clean(part)]


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z][a-z&]+", text.casefold())) - {
        "the", "and", "with", "for", "from", "that", "this", "our", "your",
        "you", "are", "will", "have", "has", "was", "were", "their", "of",
        "to", "in", "on", "at", "as", "an", "be", "by", "or", "is",
    }


def complete(text: str) -> bool:
    if not text or not re.search(r"[.!?]$", text) or len(text.split()) < 5:
        return False
    if re.search(r"\b(?:and|or|with|for|to|the|in|across|of|from|by|through|"
                 r"including|approximately|monthly|P&L|while)\W*[.!?]$", text, re.I):
        return False
    return text.count("(") == text.count(")") and not re.search(r"\w-\s*[.!?]$", text)


def starts_action(text: str) -> bool:
    return bool(re.match(r"^(?:" + "|".join(ACTIONS) + r")\b", text))


def source_units(source: str) -> list[dict[str, str]]:
    """Join soft-wrapped bullets; stop at new bullets/headings, not column widths."""
    units = []
    buffer: list[str] = []
    section = ""
    is_bullet = False

    def flush() -> None:
        if buffer:
            text = clean(" ".join(buffer))
            for sentence in sentences(text):
                units.append({"text": sentence, "section": section,
                              "bullet": "yes" if is_bullet else "no"})
            buffer.clear()

    for raw in source.splitlines():
        line = raw.strip()
        if not line:
            if buffer and re.search(r"[.!?]$", buffer[-1]):
                flush()
            continue
        if HEADINGS.fullmatch(line):
            flush()
            section = line.upper()
            is_bullet = False
            continue
        if re.match(r"^(?:[•·]|[-*]\s)", line):
            flush()
            is_bullet = True
            buffer.append(clean(line))
            continue
        # Do not append a new role/date header to an incomplete previous bullet.
        if buffer and (re.search(r"[.!?]$", buffer[-1]) or " — " in line or " | " in line):
            flush()
            is_bullet = False
        buffer.append(line)
    flush()
    return units


def polish(text: str) -> str:
    text = clean(text)
    text = re.sub(r"^Full P&L accountability", "Held full P&L accountability", text)
    text = re.sub(r"^Consistently exceeded", "Exceeded", text)
    text = re.sub(
        r"^Led a (\d[\d,]*)-outlet, multi-brand portfolio generating (.+?) "
        r"in monthly sales, with full P&L accountability\.$",
        r"Led a multi-brand portfolio of \1 outlets with full P&L accountability "
        r"for \2 in monthly sales.", text,
    )
    text = re.sub(
        r"^Exceeded profit targets by (\d+(?:\.\d+)?%) while scaling responsibility "
        r"from (\d+) to (\d+) outlets over a (\d+)-year career\.$",
        r"Exceeded profit targets by \1 while progressing from responsibility for "
        r"\2 to \3 outlets over \4 years.", text,
    )
    text = re.sub(r"^Hired, trained and developed", "Recruited, trained and developed", text)
    text = text.replace(
        "staff across multiple market entries and promotions.",
        "staff, supporting market entries and staff promotions.",
    )
    text = re.sub(r"^Reduced operating costs", "Cut operating costs", text)
    text = re.sub(
        r"^Grew sales (\d+(?:\.\d+)?%) year-on-year through a delivery zone expansion strategy\.$",
        r"Increased sales by \1 year on year by expanding delivery zones.", text,
    )
    text = text.replace(
        "via delivery hub consolidation and operational redesign",
        "by consolidating delivery hubs and redesigning operations",
    )
    text = text.replace(
        "through delivery hub consolidation and operational redesign",
        "by consolidating delivery hubs and redesigning operations",
    )
    return text


def category(text: str) -> str:
    low = text.casefold()
    if "profit targets" in low or "net margins" in low:
        return "profit"
    if re.search(r"\b(?:led|managed|held)\b", low) and re.search(r"\b(?:portfolio|locations|outlets|restaurants)\b", low):
        return "scale"
    if re.search(r"\b(?:hired|recruited|trained|developed)\b", low) and re.search(r"\b(?:staff|colleagues|teams|managers)\b", low):
        return "people"
    if re.search(r"\b(?:grew|increased) sales\b", low):
        return "sales"
    if re.search(r"\b(?:reduced|cut|controlled)\b", low) and "cost" in low:
        return "cost"
    if "orders" in low and "delivery" in low:
        return "delivery"
    if "service speed" in low or "productivity" in low:
        return "performance"
    if "compliance" in low or "food safety" in low or "brand standards" in low:
        return "compliance"
    return "other"


def metric_tokens(text: str) -> set[str]:
    return {part.casefold().replace(",", "") for part in re.findall(
        r"(?<!\w)(?:£|\$|€)?\d[\d,]*(?:\.\d+)?(?:\+|%|m|bn)?", text
    )}


def verified_material_context(candidate: dict[str, Any]) -> dict[str, Any]:
    source = str(candidate.get("source_text") or "")
    if not source.strip():
        raise MaterialEvidenceError("The original CV text is unavailable")
    units = source_units(source)
    claims = []
    for unit in units:
        original = unit["text"]
        rewritten = polish(original)
        if complete(original) and starts_action(rewritten):
            if not complete(rewritten) or metric_tokens(rewritten) != metric_tokens(original):
                raise MaterialEvidenceError("A rewritten claim changed its source metrics")
            claims.append({**unit, "source": original, "text": rewritten,
                           "category": category(rewritten)})
    name = str(candidate.get("profile_full_name") or "").strip()
    if not name:
        item = candidate.get("full_name") or {}
        quoted = clean(str(item.get("source_text") or ""))
        if quoted and quoted.casefold() in clean(source).casefold():
            name = quoted.title()
    summary = [unit["text"] for unit in units
               if unit["section"] in {"PROFESSIONAL SUMMARY", "PROFILE", "SUMMARY"}
               and complete(unit["text"])]
    return {"name": name, "source_text": source, "claims": claims, "summary": summary}


def _join(items: list[str]) -> str:
    if len(items) < 2:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def plan_material(payload: dict[str, Any]) -> dict[str, Any]:
    candidate = verified_material_context(payload["candidate"])
    source = candidate["source_text"].casefold()
    vacancy = clean(payload["job"]["description"] + " " + " ".join(payload["job"].get("requirements") or []))
    terms = tokens(vacancy)
    ordered = sorted(candidate["claims"], key=lambda item: (
        "ACHIEVEMENTS" in item["section"], bool(metric_tokens(item["text"])),
        len(tokens(item["text"]) & terms),
    ), reverse=True)
    chosen = []
    for group in ("scale", "profit", "people", "sales", "cost", "delivery", "performance", "compliance"):
        match = next((item for item in ordered if item["category"] == group), None)
        if match:
            chosen.append(match)
    for item in ordered:
        if len(chosen) >= 8:
            break
        if item["category"] == "other" and item["text"] not in {v["text"] for v in chosen}:
            chosen.append(item)
    if not chosen:
        raise MaterialEvidenceError("No complete, source-supported career statements were found")
    # A sparse CV is never padded with invented achievements.
    chosen = chosen[:8]
    lead = next((item for item in candidate["summary"] if "experience" in item.casefold()), "")
    if lead:
        lead = re.sub(r"(\d+\+?) years of experience", r"\1 years' experience", lead)
        lead = lead.replace("across QSR, franchise and delivery-led environments in the",
                            "in QSR, franchise and delivery-led operations across the")
        lead = lead.replace(" markets.", ".")
    else:
        lead = chosen[0]["text"]
    summary = [lead]
    scope = []
    if "multi-brand" in source and any(item["category"] == "scale" for item in chosen):
        scope.append("multi-brand portfolios")
    if "full p&l" in source:
        scope.append("full P&L accountability")
    if "owner-operator" in source or "independently operate" in source:
        scope.append("independent business ownership")
    if scope:
        summary.append("Experience spans " + _join(scope) + ".")
    skills = []
    for phrase, label in (
        ("staff development", "people development"),
        ("kpi governance", "KPI governance"),
        ("labour cost optimisation", "labour cost optimisation"),
        ("inventory control", "stock control"),
        ("franchise compliance", "franchise compliance"),
    ):
        if phrase in clean(source):
            skills.append(label)
    if skills:
        summary.append("Strengths include " + _join(skills) + ".")
    groups = {item["category"] for item in chosen}
    if {"delivery", "performance"} <= groups:
        if "day-to-day restaurant operations" in clean(source):
            summary.append("Delivery leadership complements experience in day-to-day restaurant operations and service improvement.")
        else:
            summary.append("Delivery leadership is supported by experience in service improvement.")
    elif {"people", "compliance"} <= groups:
        summary.append("People leadership is supported by experience in operational compliance.")
    if len(summary) < 4:
        for item in chosen:
            if item["text"] not in summary:
                summary.append(item["text"])
            if len(summary) >= 4:
                break
    return {"candidate": candidate, "claims": chosen, "summary": summary[:4], "vacancy": vacancy}


def _first_person(text: str) -> str:
    return "I " + text[0].lower() + text[1:]


def _render(payload: dict[str, Any], plan: dict[str, Any]) -> str:
    job = payload["job"]
    name = plan["candidate"]["name"]
    title, company = clean(job["title"]), clean(job["company"])
    if payload["document_type"] == "resume":
        used = set(plan["summary"])
        bullets = [item["text"] for item in plan["claims"] if item["text"] not in used]
        return "\n\n".join([
            name, f"Application for {title} | {company}",
            "Professional Summary\n" + "\n".join(plan["summary"]),
            "Selected Achievements\n" + "\n".join("- " + item for item in bullets),
        ]).strip()
    by_group = {item["category"]: item["text"] for item in plan["claims"]}
    vacancy = plan["vacancy"].casefold()
    opening = f"I am applying for the {title} role at {company}."
    priorities = []
    if "multiple restaurants" in vacancy or "multi-unit" in vacancy:
        priorities.append("lead an area of restaurants")
    if "development" in vacancy or "training" in vacancy:
        priorities.append("develop its managers")
    if "growth" in vacancy:
        priorities.append("support restaurant growth")
    if priorities:
        opening += " The opportunity to " + _join(priorities) + " is a strong match for my background."
    identity = plan["summary"][0]
    years = re.search(r"(\d+\+?) years' experience (.+)\.$", identity)
    if years:
        identity = f"My {years.group(1)} years' experience spans " + re.sub(r"^(?:in|across) ", "", years.group(2)) + "."
    else:
        identity = "My background is reflected in the following experience."
    leadership = [identity]
    for group in ("scale", "people", "delivery"):
        if group in by_group:
            leadership.append(_first_person(by_group[group]))
    cv_text = clean(plan["candidate"]["source_text"]).casefold()
    if "independent food business in the uk" in cv_text:
        leadership.append(
            "I also bring experience as an independent UK food-business owner, "
            "combining regional leadership with direct responsibility for the "
            "day-to-day operation of a business."
        )
    if "people" in by_group and "managers" in vacancy:
        leadership.append("This experience is relevant to supporting restaurant managers while retaining accountability for the performance of the wider area.")
    financial = []
    for group in ("profit", "sales", "cost", "performance"):
        if group in by_group:
            if group == "cost" and "sales" in by_group:
                financial[-1] = financial[-1].rstrip(".") + " and " + by_group[group][0].lower() + by_group[group][1:]
                continue
            financial.append(_first_person(by_group[group]))
    if not financial:
        financial = [_first_person(item["text"]) for item in plan["claims"]
                     if item["category"] not in {"scale", "people"}][:3]
    if "financial" in vacancy and "full p&l" in plan["candidate"]["source_text"].casefold():
        financial.append("I would bring the same attention to financial results, operating standards and practical improvements to this role.")
    closing = f"I would welcome the opportunity to discuss how my experience could contribute to {company}."
    if "area" in vacancy and "managers" in vacancy:
        closing += " I am particularly interested in combining area-level responsibility with practical support for restaurant managers."
    closing += " Thank you for considering my application."
    return "\n\n".join([
        "Dear Hiring Team,", opening, " ".join(leadership), " ".join(financial),
        closing, "Yours sincerely,\n" + name,
    ])


def validate_material(content: str, payload: dict[str, Any]) -> None:
    plan = plan_material(payload)
    if any(phrase in content.casefold() for phrase in PLACEHOLDERS):
        raise MaterialEvidenceError("Placeholder or copied-vacancy template wording was rejected")
    if content != _render(payload, plan):
        raise MaterialEvidenceError("Generated content includes unsupported or malformed claims")
    bullets = [line[2:] for line in content.splitlines() if line.startswith("- ")]
    if len(bullets) != len(set(item.casefold() for item in bullets)):
        raise MaterialEvidenceError("Duplicate achievement bullets were rejected")
    if any(not complete(item) or not starts_action(item) for item in bullets):
        raise MaterialEvidenceError("Incomplete achievement bullet was rejected")
    if len(bullets) > 8:
        raise MaterialEvidenceError("Too many achievement bullets")
    if any(not complete(line) for line in plan["summary"]):
        raise MaterialEvidenceError("Incomplete professional summary was rejected")
    if payload["document_type"] == "cover_letter":
        if len(plan["claims"]) >= 5 and int(payload["max_words"]) >= 350 and len(content.split()) < 250:
            raise MaterialEvidenceError(
                f"The cover letter has {len(content.split())} words and needs "
                "more relevant, source-supported detail"
            )
        prose = content.split("\n\n")[1:-1]
        if any(not complete(sentence) for paragraph in prose for sentence in sentences(paragraph)):
            raise MaterialEvidenceError("Incomplete cover-letter paragraph was rejected")
        # Remove necessary identifiers before comparing consecutive employer wording.
        comparison = content.casefold()
        for identifier in (payload["job"]["title"], payload["job"]["company"]):
            comparison = comparison.replace(identifier.casefold(), "")
        words = re.findall(r"\w+", comparison)
        vacancy_words = " ".join(re.findall(r"\w+", plan["vacancy"].casefold()))
        if any(" ".join(words[i:i+12]) in vacancy_words for i in range(len(words)-11)):
            raise MaterialEvidenceError("Long copied vacancy text was rejected")
    maximum = int(payload["max_words"])
    if len(content.split()) > maximum:
        raise MaterialEvidenceError("Complete material exceeds the requested word limit; increase it rather than truncate")


def render_material(payload: dict[str, Any]) -> str:
    content = _render(payload, plan_material(payload))
    validate_material(content, payload)
    return content
