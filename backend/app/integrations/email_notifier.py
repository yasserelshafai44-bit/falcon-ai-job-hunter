import asyncio
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage


@dataclass(slots=True)
class SMTPSettings:
    host: str
    port: int = 587
    username: str | None = None
    password: str | None = None
    sender: str = "falcon@example.com"
    use_tls: bool = True


class EmailNotifier:
    def __init__(self, settings: SMTPSettings) -> None:
        self.settings = settings

    async def send(self, *, recipient: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.settings.sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        await asyncio.to_thread(self._send_sync, message)

    def _send_sync(self, message: EmailMessage) -> None:
        with smtplib.SMTP(self.settings.host, self.settings.port, timeout=20) as smtp:
            if self.settings.use_tls:
                smtp.starttls()
            if self.settings.username:
                smtp.login(self.settings.username, self.settings.password or "")
            smtp.send_message(message)
