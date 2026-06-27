"""
payments/phone_utils.py

SINGLE SOURCE OF TRUTH for Kenyan phone number validation and
normalization. Every place that needs to accept or validate a
phone number for M-Pesa imports from here — never re-implement
the check locally.

Accepts all real-world formats a user might type or paste:
    0712345678      (legacy Safaricom / local format, 07 prefix)
    0112345678      (newer Safaricom/Airtel range, 01 prefix)
    254712345678    (international, no plus)
    +254712345678   (international, with plus)
"""

import re


class InvalidPhoneNumberError(ValueError):
    """Raised when a phone number cannot be normalized to a valid format."""
    pass


def normalize_phone(raw_phone: str) -> str:
    """
    Returns a normalized 254[71]XXXXXXXX string — the format
    Safaricom's STK Push API requires. Raises
    InvalidPhoneNumberError if the input doesn't match any
    recognized Kenyan mobile pattern.
    """
    if not raw_phone:
        raise InvalidPhoneNumberError("Phone number is required.")

    phone = raw_phone.strip()
    phone = re.sub(r'[\s\-()]', '', phone)

    if phone.startswith('+'):
        phone = phone[1:]

    # International format: 254 7/1 XXXXXXXX
    if re.fullmatch(r'254[71]\d{8}', phone):
        return phone

    # Local format with leading 0: 07XXXXXXXX / 01XXXXXXXX
    if re.fullmatch(r'0[71]\d{8}', phone):
        return '254' + phone[1:]

    # Missing leading 0, just 9 digits: 7XXXXXXXX / 1XXXXXXXX
    if re.fullmatch(r'[71]\d{8}', phone):
        return '254' + phone

    raise InvalidPhoneNumberError(
        "Enter a valid Kenyan phone number, e.g. 0712345678 or 0112345678."
    )


def is_valid_phone(raw_phone: str) -> bool:
    try:
        normalize_phone(raw_phone)
        return True
    except InvalidPhoneNumberError:
        return False


def to_local_format(raw_phone: str) -> str:
    normalized = normalize_phone(raw_phone)
    return '0' + normalized[3:]