"""Local-only application pack. Reading/continuing never contacts an ATS."""

from datetime import UTC, datetime

from app.models.application_assistant import CandidateApplicationProfile
from app.services.application_profile import APPLICATION_FIELDS, get_application_profile
from app.services.application_workflow import _get_record, get_application_review


async def assisted_pack(session, user_id, workflow_id, *, continue_application=False):
    review = await get_application_review(
        session=session, user_id=user_id, workflow_id=workflow_id
    )
    if review.workflow.status != "approved":
        raise ValueError("Review and approve the current materials before Continue")
    route = review.application_route
    if continue_application and not route["official_url"]:
        raise ValueError(route["reason"])
    try:
        profile = await get_application_profile(session, user_id)
    except ValueError:
        profile = {}  # Missing facts are shown explicitly, never invented.
    if continue_application:
        record = await _get_record(
            session=session, user_id=user_id, workflow_id=workflow_id
        )
        record.application_method = route["method"]
        record.continued_at = record.continued_at or datetime.now(UTC)
        stored = await session.get(CandidateApplicationProfile, user_id)
        if stored is None:
            session.add(CandidateApplicationProfile(user_id=user_id, data=profile))
        elif stored.data != profile:
            stored.data = profile
            stored.revision += 1
        await session.commit()
    fields = [
        {
            "key": key,
            "label": label,
            "value": profile.get(key),
            "status": "KNOWN" if profile.get(key) else "NEEDS USER INPUT",
            "evidence": profile.get("evidence", {}).get(key),
        }
        for key, label in APPLICATION_FIELDS.items()
    ]
    return {
        "workflow_id": workflow_id,
        "state": "assisted_apply_required",
        "status": "ASSISTED APPLY REQUIRED" if route["official_url"] else "BLOCKED",
        "message": "Prepared — employer site completion required",
        "employer": review.job.company,
        "role": review.job.title,
        "location": review.job.location,
        "route": route,
        "materials_approved": True,
        "external_submission_performed": False,
        "fields": fields,
        "work_history": profile.get("work_history", []),
        "education": profile.get("education", []),
        "cover_letter": review.cover_letter.content,
        "resume_document_id": review.resume.id,
        "resume_filename": (
            f"Falcon-application-{workflow_id}-resume-{review.resume.id}.docx"
        ),
        "questions": review.unanswered_employer_questions,
        "questions_status": review.employer_questions_status,
        "questions_note": review.employer_questions_note,
        "missing_fields": [
            f["label"] for f in fields if f["status"] == "NEEDS USER INPUT"
        ],
        "human_actions": [
            "Upload the tailored CV and paste prepared details into the employer form.",
            "Answer new employer questions and make your own security, login "
            "and consent decisions.",
            "Review the completed employer form and press its final Submit "
            "only when you approve.",
        ],
    }
