"""Offline capability routing. Never probe an employer to decide a route."""

from enum import StrEnum
from urllib.parse import urlsplit


class ApplicationMethod(StrEnum):
    SUPPORTED_API = "SUPPORTED_API"
    SAFE_AUTOFILL = "SAFE_AUTOFILL"
    ASSISTED_APPLY = "ASSISTED_APPLY"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"
    UNAVAILABLE = "UNAVAILABLE"


def application_route(job):
    url = urlsplit(job.url or "")
    method = ApplicationMethod.ASSISTED_APPLY
    reason = (
        "No authorised application integration is available for this vacancy. "
        "Use the prepared files and reusable details on the official employer site."
    )
    if url.hostname and (
        url.hostname == "smartrecruiters.com"
        or url.hostname.endswith(".smartrecruiters.com")
    ):
        reason = (
            "SmartRecruiters blocked browser automation. Falcon will not launch, "
            "retry or control its browser form. Complete the official application "
            "yourself when access is available; security, consent and employer "
            "questions require your action."
        )
    if not getattr(job, "is_active", True) or getattr(job, "is_demo", False):
        method = ApplicationMethod.UNAVAILABLE
        reason = (
            "This vacancy is inactive or a demo; external application is unavailable."
        )
    elif url.scheme not in {"http", "https"} or not url.hostname or url.username:
        method = ApplicationMethod.UNAVAILABLE
        reason = "No valid official employer application link is stored."
    # No live application executor is authorised/implemented. A configured vacancy
    # feed or configuration-only ATS token is NOT a submission capability.
    return {
        "method": method.value,
        "reason": reason,
        "official_url": job.url if method != ApplicationMethod.UNAVAILABLE else None,
        "automated_submission_supported": False,
        "browser_automation_enabled": False,
    }
