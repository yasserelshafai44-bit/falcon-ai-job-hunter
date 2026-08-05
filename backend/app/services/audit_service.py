from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventType, build_audit_record
from app.models.audit_event import AuditEvent


async def record_audit_event(
    *,
    session: AsyncSession,
    event_type: AuditEventType,
    user_id: int | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    """Persist a sanitized audit event.

    This function intentionally commits immediately so security-relevant events
    are not silently lost if a later business operation rolls back.
    """
    record = build_audit_record(
        event_type=event_type,
        user_id=user_id,
        request_id=request_id,
        ip_address=ip_address,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=metadata,
    )

    event = AuditEvent(
        event_type=record.event_type.value,
        user_id=record.user_id,
        request_id=record.request_id,
        ip_address=record.ip_address,
        resource_type=record.resource_type,
        resource_id=record.resource_id,
        metadata_json=record.metadata,
        occurred_at=record.occurred_at,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event
