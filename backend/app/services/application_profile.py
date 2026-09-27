"""Reusable factual data, with source evidence and explicit conflict handling."""

import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select

from app.models.application_assistant import CandidateApplicationProfile
from app.models.candidate import Candidate
from app.models.candidate_analysis import CandidateAnalysis

APPLICATION_FIELDS = {
    "first_name": "First name",
    "application_surname": "Legal/application surname",
    "email": "Email",
    "phone": "Phone",
    "city": "City",
    "address": "Address",
    "postcode": "Postcode",
    "country": "Country",
    "right_to_work": "Right to work",
    "linkedin_url": "LinkedIn/profile URL",
    "notice_period": "Notice period",
    "salary_expectations": "Salary expectations",
    "driving_licence": "Driving licence",
    "relocation_preferences": "Relocation preferences",
    "travel_preferences": "Travel preferences",
    "skills": "Skills",
}


class ApplicationFactUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    value: str = Field(min_length=1, max_length=2000)


async def save_application_fact(session, user_id, field, value):
    if field not in APPLICATION_FIELDS or not value.strip():
        raise ValueError("Choose a supported field and enter your confirmed answer")
    if field == "application_surname":
        return await save_application_surname(session, user_id, value)
    try:
        data = dict(await get_application_profile(session, user_id))
    except ValueError:
        data = {}
    data[field] = value.strip()
    data["evidence"] = {**data.get("evidence", {}), field: "Explicit user answer"}
    record = await session.get(CandidateApplicationProfile, user_id)
    if record:
        record.data = data
        record.revision += 1
    else:
        session.add(CandidateApplicationProfile(user_id=user_id, data=data))
    await session.commit()
    return data


def enrich_application_facts(data, analysis):
    """Only literal source evidence; never default eligibility/search booleans."""
    result = dict(data)
    evidence = dict(data.get("evidence", {}))
    source = " ".join(analysis.extracted_text.split())
    literals = {
        "right_to_work": "Full right to work in the UK",
        "driving_licence": "Full UK Driving Licence",
    }
    for key, literal in literals.items():
        if not result.get(key) and literal.casefold() in source.casefold():
            result[key] = literal
            evidence[key] = f"Source CV: {literal}"
    if not result.get("country") and re.search(
        r",\s*(UK|United Kingdom)$", data.get("city", "")
    ):
        result["country"] = "United Kingdom"
        evidence["country"] = "Source CV location: " + data["city"]
    skills = [
        item["value"]
        for item in (analysis.analysis_data or {}).get("skills", [])
        if item.get("value")
        and item.get("source_text")
        and " ".join(item["source_text"].split()).casefold() in source.casefold()
    ]
    if not result.get("skills") and skills:
        result["skills"] = "; ".join(dict.fromkeys(skills))
        evidence["skills"] = "Source CV evidence for each stored skill"
    result["evidence"] = evidence
    return result


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    phone: str = Field(default="", max_length=50)
    city: str = Field(default="", max_length=255)
    name_confirmed: bool = False
    application_surname: str | None = Field(default=None, min_length=1, max_length=150)


async def save_application_surname(session, user_id, surname):
    surname = surname.strip()
    if not surname:
        raise ValueError("Enter your legal/application surname")
    data = dict(await get_application_profile(session, user_id))
    data.update(
        application_surname=surname,
        last_name=surname,
        name_confirmed=True,
        name_conflict=False,
    )
    record = await session.get(CandidateApplicationProfile, user_id)
    if record:
        record.data = data
        record.revision += 1
    else:
        session.add(CandidateApplicationProfile(user_id=user_id, data=data))
    await session.commit()
    return data


def extract_reusable_facts(candidate, analysis):
    text = analysis.extracted_text
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = candidate.full_name.strip().split(maxsplit=1)
    cv_name = lines[0] if lines else ""
    contacts = [part.strip() for line in lines[:6] for part in line.split("|")]
    phone = next((p for p in contacts if re.fullmatch(r"\+?[\d ()-]{10,25}", p)), "")
    location = next((p for p in contacts if "," in p and "@" not in p), "")
    work = []
    if "WORK HISTORY" in lines:
        section = lines[lines.index("WORK HISTORY") + 1 :]
        section = (
            section[: section.index("EDUCATION")] if "EDUCATION" in section else section
        )
        # Parse only explicit title/company + dated location records; keep source.
        for index, line in enumerate(section):
            if "|" not in line or not re.search(r"\b(?:19|20)\d{2}\b", line):
                continue
            previous = section[index - 1] if index else ""
            if " — " not in previous and index > 1:
                previous = section[index - 2] + " " + previous
            if " — " not in previous:
                continue
            title, company = previous.split(" — ", 1)
            place, dates = line.split("|", 1)
            work.append(
                {
                    "title": title,
                    "company": company,
                    "location": place.strip(),
                    "dates": dates.strip(),
                    "source_text": previous + "\n" + line,
                }
            )
    education = []
    if "EDUCATION" in lines:
        for line in lines[lines.index("EDUCATION") + 1 :]:
            if line == "LANGUAGES":
                break
            education.append({"description": line.lstrip("• "), "source_text": line})
    return {
        "first_name": name[0],
        "last_name": name[1] if len(name) > 1 else "",
        "email": candidate.email,
        "phone": candidate.phone or phone,
        "city": candidate.location or location,
        "work_history": work,
        "education": education,
        "name_confirmed": False,
        "name_conflict": cv_name.casefold() != candidate.full_name.casefold(),
        "source_cv_name": cv_name,
        "source_profile_name": candidate.full_name,
        "source_analysis_id": analysis.id,
        "evidence": {"phone": phone, "city": location},
    }


async def get_application_profile(session, user_id):
    stored = await session.get(CandidateApplicationProfile, user_id)
    if stored:
        analysis = (
            await session.get(CandidateAnalysis, stored.data.get("source_analysis_id"))
            if stored.data.get("source_analysis_id")
            else None
        )
        if analysis and analysis.user_id == user_id:
            return enrich_application_facts(stored.data, analysis)
        return stored.data
    candidate = await session.scalar(
        select(Candidate).where(Candidate.user_id == user_id)
    )
    selected_id = (
        (candidate.profile_data or {}).get("cv_analysis_id") if candidate else None
    )
    analysis = await session.scalar(
        select(CandidateAnalysis)
        .where(
            CandidateAnalysis.user_id == user_id,
            CandidateAnalysis.id == selected_id if selected_id else True,
        )
        .order_by(CandidateAnalysis.id.desc())
    )
    if not candidate or not analysis:
        raise ValueError("Save a candidate profile and analyse your CV first")
    return enrich_application_facts(
        extract_reusable_facts(candidate, analysis), analysis
    )


async def save_application_profile(session, user_id, payload):
    data = await get_application_profile(session, user_id)
    data = {**data, **payload.model_dump(mode="json")}
    if not payload.name_confirmed:
        raise ValueError("Confirm the first and last name once before saving")
    data["application_surname"] = (
        payload.application_surname or payload.last_name
    ).strip()
    data["last_name"] = data["application_surname"]
    data["name_conflict"] = (
        data.get("name_conflict", False) and not payload.name_confirmed
    )
    record = await session.get(CandidateApplicationProfile, user_id)
    if record:
        record.data = data
        record.revision += 1
    else:
        session.add(CandidateApplicationProfile(user_id=user_id, data=data))
    await session.commit()
    return data
