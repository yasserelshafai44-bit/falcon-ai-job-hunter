from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class AuditEventType(StrEnum):
    USER_REGISTERED = "user_registered"
    LOGIN_FAILED = "login_failed"
    CV_UPLOADED = "cv_uploaded"
    CANDIDATE_ANALYZED = "candidate_analyzed"
    JOB_SYNCED = "job_synced"
    MATCH_CALCULATED = "match_calculated"
    RESUME_GENERATED = "resume_generated"
    COVER_LETTER_GENERATED = "cover_letter_generated"
    DOCUMENT_APPROVED = "document_approved"
    ADMIN_CHANGE = "admin_change"


_SENSITIVE_FIELDS = {
    "password",
    "password_hash",
    "authorization",
    "token",
    "access_token",
    "refresh_token",
    "cv_content",
    "document_content",
}


@dataclass(frozen=True, slots=True)
class AuditRecord:
    event_type: AuditEventType
    occurred_at: datetime
    user_id: int | None
    request_id: str | None
    ip_address: str | None
    resource_type: str | None
    resource_id: str | None
    metadata: dict[str, Any]


def sanitize_audit_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in metadata.items():
        if key.casefold() in _SENSITIVE_FIELDS:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_audit_metadata(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_audit_metadata(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


def build_audit_record(
    *,
    event_type: AuditEventType,
    user_id: int | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditRecord:
    return AuditRecord(
        event_type=event_type,
        occurred_at=datetime.now(UTC),
        user_id=user_id,
        request_id=request_id,
        ip_address=ip_address,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=sanitize_audit_metadata(metadata or {}),
    )
