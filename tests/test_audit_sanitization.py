from app.core.audit import AuditEventType, build_audit_record


def test_audit_metadata_redacts_sensitive_fields() -> None:
    record = build_audit_record(
        event_type=AuditEventType.LOGIN_FAILED,
        metadata={
            "email": "user@example.com",
            "password": "secret",
            "nested": {"access_token": "token-value"},
        },
    )

    assert record.metadata["email"] == "user@example.com"
    assert record.metadata["password"] == "[REDACTED]"
    assert record.metadata["nested"]["access_token"] == "[REDACTED]"
