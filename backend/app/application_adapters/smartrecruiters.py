"""Official Application API adapter. No private endpoints or browser bypasses.

API staging is local: SmartRecruiters accepts the CV with final submission, not
through a separate draft-upload endpoint. Never report a staged file as uploaded.
"""

import re
from urllib.parse import urlsplit
from uuid import UUID

import httpx

from app.core.config import get_settings


class SmartRecruitersAdapter:
    name = "smartrecruiters"

    async def inspect(self, url):
        path = urlsplit(url).path.strip("/").split("/")
        if len(path) != 2 or not re.fullmatch(r"[A-Za-z0-9_-]+", path[0]):
            raise ValueError("Unsupported SmartRecruiters posting URL")
        posting_id = path[1].split("-", 1)[0]
        if not posting_id.isdigit():
            raise ValueError("Invalid SmartRecruiters posting identifier")
        settings = get_settings()
        token = settings.smartrecruiters_application_token
        if not token or settings.smartrecruiters_application_company != path[0]:
            return {
                "status": "blocked",
                "questions": None,
                "blocker": "No authorised SmartRecruiters Application API credential "
                "for this employer. Browser form automation requires a connected "
                "browser; "
                "the public vacancies feed cannot retrieve application questions.",
            }
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            detail = await client.get(
                f"https://api.smartrecruiters.com/v1/companies/{path[0]}/postings/{posting_id}"
            )
            detail.raise_for_status()
            posting_uuid = str(UUID(detail.json()["uuid"]))
            response = await client.get(
                f"https://api.smartrecruiters.com/postings/{posting_uuid}/configuration",
                headers={
                    "X-SmartToken": token.get_secret_value(),
                    "Accept-Language": "en",
                },
                params={"conditionalsIncluded": "true"},
            )
            if response.status_code in {401, 403, 429}:
                return {
                    "status": "blocked",
                    "questions": None,
                    "blocker": f"SmartRecruiters refused application configuration "
                    f"(HTTP {response.status_code}); no retry or bypass attempted.",
                }
            response.raise_for_status()
            configuration = response.json()
            if not isinstance(configuration.get("questions"), list):
                raise ValueError(
                    "SmartRecruiters did not return a valid question configuration"
                )
            return {
                **configuration,
                "status": "retrieved",
                "posting_uuid": posting_uuid,
            }

    def populate(self, profile, configuration):
        fields = {}
        for source, destination in (
            ("first_name", "firstName"),
            ("last_name", "lastName"),
            ("email", "email"),
            ("phone", "phoneNumber"),
        ):
            if profile.get(source) and not (
                source in {"first_name", "last_name"} and profile.get("name_conflict")
            ):
                fields[destination] = profile[source]
        if profile.get("city"):
            fields["location"] = {"city": profile["city"]}
        # Preserve month-only dates as evidence instead of inventing a day.
        fields["experience"] = [
            {key: row[key] for key in ("title", "company", "location") if row.get(key)}
            | {"description": row["source_text"]}
            for row in profile.get("work_history", [])
        ]
        fields["education"] = [
            {"description": row["description"]} for row in profile.get("education", [])
        ]
        unresolved = []
        if profile.get("name_conflict"):
            unresolved.append(
                "Confirm application name: saved profile and source CV differ"
            )
        for key in ("firstName", "lastName", "email"):
            if not fields.get(key):
                unresolved.append(f"Missing confirmed {key}")
        questions = configuration.get("questions")
        if questions is None:
            unresolved.append(
                "Employer questions and consent requirements have not been retrieved"
            )
        answer_review = []
        # Exact routine-field aliases only. No fuzzy matching or inferred eligibility.
        aliases = {
            "first name": "first_name",
            "last name": "last_name",
            "email address": "email",
            "phone number": "phone",
        }
        for question in questions or []:
            for field in question.get("fields", []):
                label = question.get("label", "")
                key = aliases.get(label.casefold().strip())
                safe = (
                    key
                    and not question.get("repeatable")
                    and len(question.get("fields", [])) == 1
                    and field.get("type") == "INPUT_TEXT"
                    and not field.get("complianceType")
                    and not profile.get("name_conflict")
                )
                answer = profile.get(key) if safe else None
                item = {
                    "question_id": question.get("id"),
                    "field_id": field.get("id"),
                    "label": label,
                    "field_label": field.get("label", ""),
                    "type": field.get("type"),
                    "options": field.get("values", []),
                    "required": field.get("required", False),
                    "sensitive": bool(field.get("complianceType")),
                    "answer": answer,
                    "source": f"candidate profile: {key}" if answer else None,
                }
                answer_review.append(item)
                if answer is None and field.get("type") != "INFORMATION":
                    unresolved.append(
                        label + (" / " + field["label"] if field.get("label") else "")
                    )
        if configuration.get("privacyPolicies") or configuration.get("consent"):
            unresolved.append(
                "Review employer privacy policies and make consent decisions"
            )
        return {
            "fields": fields,
            "questions": answer_review,
            "unresolved": unresolved,
            "population_target": "local_api_draft",
            "employer_form_populated": False,
            "resume_uploaded": False,
        }
