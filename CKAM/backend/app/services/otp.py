"""OTP issuing and verification for phone-based login.

Codes are 6 digits, hashed with the app secret before storage, expire after
5 minutes, allow 5 verification attempts, and have a 60s resend cooldown plus
a 5-per-hour cap per phone number.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.phone import mask_phone, normalize_phone
from app.core.security import SECRET_KEY
from app.models.models import OtpCode, User
from app.services import notify

OTP_TTL_SECONDS = 300
RESEND_COOLDOWN_SECONDS = 60
MAX_ATTEMPTS = 5
MAX_PER_HOUR = 5


class OtpError(ValueError):
    """User-facing OTP failure (message is safe to show)."""


def _hash_code(phone: str, code: str) -> str:
    return hashlib.sha256(f"{SECRET_KEY}:{phone}:{code}".encode()).hexdigest()


def _active_codes(db: Session, phone: str) -> list[OtpCode]:
    now = datetime.utcnow()
    return (
        db.query(OtpCode)
        .filter(OtpCode.destination == phone, OtpCode.consumed_at.is_(None), OtpCode.expires_at > now)
        .order_by(OtpCode.created_at.desc())
        .all()
    )


def issue_otp(db: Session, phone_raw: str) -> dict:
    """Create and dispatch a code. Returns a response payload (never the code
    unless no delivery channel exists at all — dev mode, see notify.can_deliver)."""
    phone = normalize_phone(phone_raw)

    recent = (
        db.query(OtpCode)
        .filter(OtpCode.destination == phone)
        .order_by(OtpCode.created_at.desc())
        .first()
    )
    if recent and recent.created_at and datetime.utcnow() - recent.created_at < timedelta(
        seconds=RESEND_COOLDOWN_SECONDS
    ):
        wait = RESEND_COOLDOWN_SECONDS - int((datetime.utcnow() - recent.created_at).total_seconds())
        raise OtpError(f"Please wait {max(wait, 1)} seconds before requesting a new code.")

    hour_ago = datetime.utcnow() - timedelta(hours=1)
    sent_last_hour = (
        db.query(OtpCode)
        .filter(OtpCode.destination == phone, OtpCode.created_at >= hour_ago)
        .count()
    )
    if sent_last_hour >= MAX_PER_HOUR:
        raise OtpError("Too many codes requested for this number. Try again in an hour.")

    code = f"{secrets.randbelow(1000000):06d}"
    db.add(
        OtpCode(
            destination=phone,
            code_hash=_hash_code(phone, code),
            purpose="login",
            expires_at=datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS),
        )
    )
    db.commit()

    user = db.query(User).filter(User.phone == phone).first()
    message = f"MandiWise login code: {code}. Valid for 5 minutes. Never share it with anyone."
    sms_sent = notify.send_sms(phone, message)
    email_sent = False
    if user:
        email_sent = notify.send_email(
            user.email,
            "Your MandiWise login code",
            f"Hi {user.name},\n\nYour one-time login code is {code}\n\n"
            f"It expires in 5 minutes. If you did not request it, ignore this email.",
        )

    payload = {
        "message": "Code sent to your phone",
        "masked_phone": mask_phone(phone),
        "expires_in": OTP_TTL_SECONDS,
        "resend_after": RESEND_COOLDOWN_SECONDS,
    }
    if not notify.can_deliver():
        # Dev mode: nothing can actually deliver this code, so hand it to the
        # UI for local testing. Configure SMTP or an SMS provider to disable.
        payload["message"] = "Dev mode: no SMS/email provider configured"
        payload["dev_code"] = code
    elif user is None:
        payload["message"] = "Code sent (this number is not linked to an account yet)"
    else:
        payload["message"] = "Code sent to your phone and email" if email_sent else "Code sent to your phone"
    return payload


def verify_otp(db: Session, phone_raw: str, code: str) -> User:
    """Check a code and return the matching user, or raise OtpError."""
    phone = normalize_phone(phone_raw)
    code = (code or "").strip()
    if len(code) != 6 or not code.isdigit():
        raise OtpError("Enter the 6-digit code")

    records = _active_codes(db, phone)
    if not records:
        raise OtpError("Code expired or not found — request a new one")

    record = records[0]
    if record.attempts >= MAX_ATTEMPTS:
        raise OtpError("Too many wrong attempts — request a new code")
    if record.code_hash != _hash_code(phone, code):
        record.attempts += 1
        db.commit()
        left = MAX_ATTEMPTS - record.attempts
        raise OtpError(f"Wrong code — {left} attempt{'s' if left != 1 else ''} left")

    record.consumed_at = datetime.utcnow()
    db.commit()  # burn the code even if the steps below fail
    user = db.query(User).filter(User.phone == phone).first()
    if user is None:
        # Verified but no account: caller decides (register link in the UI).
        raise OtpError("No account is linked to this number — please sign up first")
    user.phone_verified = True
    db.commit()
    return user
