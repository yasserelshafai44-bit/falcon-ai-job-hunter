from app.integrations.email_notifier import EmailNotifier, SMTPSettings


def test_email_notifier_builds_expected_settings() -> None:
    settings = SMTPSettings(
        host="smtp.example.com",
        port=587,
        username="user",
        password="secret",
        sender="falcon@example.com",
    )
    notifier = EmailNotifier(settings)
    assert notifier.settings.host == "smtp.example.com"
    assert notifier.settings.sender == "falcon@example.com"
