from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

import aiosmtplib

from app.core.config import Settings, get_settings
from app.core.enums import EmailDeliveryStatus


@dataclass(frozen=True)
class EmailSendResult:
    status: EmailDeliveryStatus
    error: str | None = None


class EmailSender(Protocol):
    async def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        body: str,
    ) -> EmailSendResult: ...


class SmtpEmailSender:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        body: str,
    ) -> EmailSendResult:
        if not self.settings.smtp_host:
            return EmailSendResult(
                status=EmailDeliveryStatus.FAILED,
                error="SMTP is not configured",
            )

        from_email = self.settings.smtp_from_email or self.settings.admin_notification_email
        message = EmailMessage()
        message["From"] = f"{self.settings.smtp_from_name} <{from_email}>"
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        try:
            await aiosmtplib.send(
                message,
                hostname=self.settings.smtp_host,
                port=self.settings.smtp_port,
                username=self.settings.smtp_username,
                password=self.settings.smtp_password,
                start_tls=self.settings.smtp_use_tls,
                timeout=self.settings.smtp_timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            return EmailSendResult(status=EmailDeliveryStatus.FAILED, error=str(exc))

        return EmailSendResult(status=EmailDeliveryStatus.SENT)


class FakeEmailSender:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, str]] = []
        self.fail_next = False
        self.failure_error = "simulated email failure"

    async def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        body: str,
    ) -> EmailSendResult:
        if self.fail_next:
            self.fail_next = False
            return EmailSendResult(status=EmailDeliveryStatus.FAILED, error=self.failure_error)

        self.sent_messages.append(
            {
                "to_email": to_email,
                "subject": subject,
                "body": body,
            }
        )
        return EmailSendResult(status=EmailDeliveryStatus.SENT)


_fake_email_sender: FakeEmailSender | None = None


def get_email_sender(settings: Settings | None = None) -> EmailSender:
    global _fake_email_sender
    if _fake_email_sender is not None:
        return _fake_email_sender
    return SmtpEmailSender(settings)


def set_fake_email_sender(sender: FakeEmailSender | None) -> None:
    global _fake_email_sender
    _fake_email_sender = sender
