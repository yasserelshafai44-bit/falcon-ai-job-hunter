from __future__ import annotations

from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventType
from app.core.rate_limit import client_ip
from app.models.audit_event import AuditEvent
from app.services.audit_service import record_audit_event


async def audit_from_request(
    *,
    session: AsyncSession,
    request: Request,
    event_type: AuditEventType,
    user_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    """Persist an audit event using safe request context."""
    return await record_audit_event(
        session=session,
        event_type=event_type,
        user_id=user_id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=client_ip(request),
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=metadata,
    )
