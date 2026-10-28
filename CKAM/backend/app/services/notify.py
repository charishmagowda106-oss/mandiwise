"""Delivery channels for OTPs and price alerts.

Design (per project decision): **in-app + email first, SMS-ready**.

- Email: sent with smtplib when SMTP_HOST is configured.
- SMS:  pluggable via env vars — set SMS_PROVIDER=twilio (+ Twilio credentials)
        and messages go out over Twilio's HTTP API using only the stdlib, so no
        new dependency is required. With no provider configured, SMS is a no-op.
- Dev fallback: when *neither* channel is configured the message is printed to
  the backend console so the whole flow can be exercised locally. That same
  "no channel available" state is what lets OTP responses expose the code to
  the UI (see app.services.otp.can_deliver) — configure SMTP or an SMS
  provider in production and the code is never returned to the client.
"""

import os
import smtplib
import urllib.error
import urllib.parse
import urllib.request
from email.mime.text import MIMEText

import logging

log = logging.getLogger("mandiwise.notify")


def smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST"))


def sms_configured() -> bool:
    """Twilio today; add other providers here without touching callers."""
    if os.getenv("SMS_PROVIDER", "").strip().lower() != "twilio":
        return False
    return bool(os.getenv("TWILIO_ACCOUNT_SID")) and bool(os.getenv("TWILIO_AUTH_TOKEN")) and bool(
        os.getenv("TWILIO_FROM_NUMBER")
    )


def can_deliver() -> bool:
    """True when messages can actually leave this machine."""
    return smtp_configured() or sms_configured()


def send_email(to: str, subject: str, body: str) -> bool:
    if not smtp_configured():
        log.info("[email:dev] to=%s subject=%s\n%s", to, subject, body)
        return False
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    use_tls = os.getenv("SMTP_TLS", "true").lower() != "false"
    sender = os.getenv("SMTP_FROM", user or "no-reply@mandiwise.local")
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to
        with smtplib.SMTP(host, port, timeout=15) as server:
            if use_tls:
                server.starttls()
            if user and password:
                server.login(user, password)
            server.sendmail(sender, [to], msg.as_string())
        log.info("[email] sent to %s", to)
        return True
    except Exception as exc:  # delivery must never crash a request
        log.warning("[email] failed to %s: %s", to, exc)
        return False


def _send_twilio_sms(phone: str, message: str) -> bool:
    sid = os.environ["TWILIO_ACCOUNT_SID"]
    token = os.environ["TWILIO_AUTH_TOKEN"]
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    data = urllib.parse.urlencode(
        {"To": phone, "From": os.environ["TWILIO_FROM_NUMBER"], "Body": message}
    ).encode()
    request = urllib.request.Request(url, data=data, method="POST")
    credentials = f"{sid}:{token}".encode()
    import base64

    request.add_header("Authorization", "Basic " + base64.b64encode(credentials).decode())
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(request, timeout=15) as response:
        return 200 <= response.status < 300


def send_sms(phone: str, message: str) -> bool:
    if not sms_configured():
        log.info("[sms:dev] to=%s (no SMS provider configured)\n  %s", phone, message)
        return False
    try:
        if os.getenv("SMS_PROVIDER", "").strip().lower() == "twilio":
            return _send_twilio_sms(phone, message)
        log.warning("[sms] unknown SMS_PROVIDER=%s", os.getenv("SMS_PROVIDER"))
        return False
    except (urllib.error.URLError, OSError, ValueError) as exc:
        log.warning("[sms] failed to %s: %s", phone, exc)
        return False
