"""
Email Service.

Sends transactional emails via Gmail SMTP using Python's built-in
smtplib and email.message.EmailMessage. Configuration is read from
the project's central Settings object (app.config.settings), the
same source of truth every other part of the app already uses — no
credentials are ever hardcoded here. This file is intentionally
independent of FastAPI; it can be called from any service layer
without importing routers or request objects.
"""

import smtplib
from email.message import EmailMessage

from app.config.settings import settings


def _get_smtp_config() -> dict:
    """
    Read SMTP configuration from the app's Settings object. Settings
    already validates these fields as required at startup (via
    pydantic-settings), so no missing-variable check is needed here.
    """
    return {
        "server": settings.SMTP_SERVER,
        "port": settings.SMTP_PORT,
        "email": settings.SMTP_EMAIL,
        "password": settings.SMTP_PASSWORD,
    }


def send_email(
    recipient_email: str,
    subject: str,
    body: str,
) -> None:
    """
    Send a plain-text email via Gmail SMTP.

    Exceptions from smtplib are never caught here — a send failure
    must propagate to the caller rather than fail silently. A 20
    second timeout is set so a hung SMTP connection can't hang the
    calling request indefinitely.
    """
    config = _get_smtp_config()

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config["email"]
    message["To"] = recipient_email
    message.set_content(body)

    with smtplib.SMTP(config["server"], config["port"], timeout=20) as server:
        server.starttls()
        server.login(config["email"], config["password"])
        server.send_message(message)


def send_auction_live_email(
    recipient_email: str,
    company_name: str,
    auction_title: str,
    material_name: str,
    quantity,
    unit,
) -> None:
    """
    Notify a vendor that an auction they've been invited to is now LIVE.
    """
    subject = f"New Live Auction: {auction_title}"

    body = (
        f"Dear {company_name},\n\n"
        f"A new reverse auction is now live on ProcureAI and you have been "
        f"invited to participate.\n\n"
        f"Auction Title: {auction_title}\n"
        f"Material: {material_name}\n"
        f"Quantity: {quantity} {unit}\n\n"
        f"Please log in to ProcureAI to view the auction details and submit "
        f"your bid before it closes.\n\n"
        f"Regards,\n"
        f"ProcureAI Team"
    )

    send_email(recipient_email, subject, body)


def send_award_email(
    recipient_email: str,
    company_name: str,
    auction_title: str,
) -> None:
    """
    Notify a vendor that they have won an auction.
    """
    subject = f"Congratulations! You Won: {auction_title}"

    body = (
        f"Dear {company_name},\n\n"
        f"Congratulations! You have been awarded the auction '{auction_title}' "
        f"on ProcureAI.\n\n"
        f"Please log in to ProcureAI and reach out to the buyer to proceed "
        f"with the next steps.\n\n"
        f"Regards,\n"
        f"ProcureAI Team"
    )

    send_email(recipient_email, subject, body)