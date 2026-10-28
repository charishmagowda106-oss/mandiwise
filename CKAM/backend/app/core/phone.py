"""Indian mobile number normalization and masking helpers.

Accepted inputs: "9876543210", "98765 43210", "+91 98765-43210", "09876543210".
Stored form is always E.164-like: "+91" + 10 digits starting 6-9.
"""

import re

INDIAN_MOBILE = re.compile(r"^(?:\+?91[-\s]?)?(0)?([6-9]\d{9})$")


class InvalidPhone(ValueError):
    pass


def normalize_phone(raw: str) -> str:
    """Return the canonical +91XXXXXXXXXX form or raise InvalidPhone."""
    if raw is None:
        raise InvalidPhone("Enter a valid 10-digit mobile number")
    digits = re.sub(r"[\s\-().]", "", str(raw).strip())
    match = INDIAN_MOBILE.match(digits)
    if not match:
        raise InvalidPhone("Enter a valid 10-digit Indian mobile number (starts with 6-9)")
    return f"+91{match.group(2)}"


def mask_phone(phone: str) -> str:
    """"+919876543210" -> "+91 98•••••210" for safe display."""
    tail = phone[-10:] if len(phone) >= 10 else phone
    return f"+91 {tail[:2]}•••••{tail[-3:]}"
