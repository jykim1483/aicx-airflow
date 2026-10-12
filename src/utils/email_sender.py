"""SMTP 이메일 발송 공통 모듈."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Iterable


def send_email(
    *,
    recipients: str | Iterable[str],
    subject: str,
    body: str,
    sender: str | None = None,
    host: str | None = None,
    port: int | None = None,
    username: str | None = None,
    password: str | None = None,
    use_tls: bool = True,
) -> None:

    recipient_list = [recipients] if isinstance(recipients, str) else list(recipients)
    if not recipient_list:
        raise ValueError("recipients must contain at least one address")

    smtp_host = host or os.environ.get("SMTP_HOST")
    smtp_port = port or int(os.environ.get("SMTP_PORT", "587"))
    smtp_sender = sender or os.environ.get("SMTP_SENDER")
    smtp_username = username or os.environ.get("SMTP_USERNAME")
    smtp_password = password or os.environ.get("SMTP_PASSWORD")

    if not smtp_host or not smtp_sender:
        raise ValueError("SMTP_HOST and SMTP_SENDER are required")

    message = EmailMessage()
    message["From"] = smtp_sender
    message["To"] = ", ".join(recipient_list)
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as smtp:
        if use_tls:
            smtp.starttls()
        if smtp_username and smtp_password:
            smtp.login(smtp_username, smtp_password)
        smtp.send_message(message)
