"""
Data normalization utilities for ETL.

This module provides functions to normalize contact information (phones, emails)
into consistent formats suitable for identity resolution and matching.

Design Decisions:
    1. Phone normalization targets E.164 format (+14155551234)
    2. Email normalization: lowercase, stripped whitespace
    3. Detection uses heuristics (@ for email, digits for phone)
    4. Normalization is best-effort - invalid inputs return original value

Phone Normalization Strategy:
    - Remove all non-digit characters except leading +
    - Assume US country code (+1) if 10 digits and no country code
    - Preserve international numbers as-is
    - Handle common formats: (415) 555-1234, 415-555-1234, +1 415 555 1234

See LEARNINGS.md for edge cases and limitations.
"""

import re
from typing import Literal

# Type alias for contact types
ContactType = Literal["phone", "email", "unknown"]

# Regex patterns
EMAIL_PATTERN = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
DIGITS_ONLY_PATTERN = re.compile(r"[^\d]")
US_PHONE_PATTERN = re.compile(r"^\d{10}$")
INTL_PHONE_PATTERN = re.compile(r"^\+\d{10,15}$")


def normalize_phone(raw: str) -> str:
    """
    Normalize a phone number to E.164 format.

    E.164 format: +[country code][number], e.g., +14155551234

    Args:
        raw: Raw phone number in any format.

    Returns:
        Normalized phone number in E.164 format, or original if unparseable.

    Examples:
        >>> normalize_phone("(415) 555-1234")
        '+14155551234'
        >>> normalize_phone("+1 415 555 1234")
        '+14155551234'
        >>> normalize_phone("415-555-1234")
        '+14155551234'
        >>> normalize_phone("+44 20 7946 0958")
        '+442079460958'
    """
    if not raw:
        return raw

    # Strip whitespace
    cleaned = raw.strip()

    # Check if it starts with + (international format)
    has_plus = cleaned.startswith("+")

    # Remove all non-digit characters (including +)
    digits = DIGITS_ONLY_PATTERN.sub("", cleaned)

    if not digits:
        return raw  # Return original if no digits found

    # If it had a +, preserve it (already has country code)
    if has_plus:
        return f"+{digits}"

    # Check for 10-digit US number (no country code)
    if US_PHONE_PATTERN.match(digits):
        return f"+1{digits}"

    # Check for 11-digit number starting with 1 (US with country code)
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"

    # For other formats, return with + prefix if it looks like a phone
    if len(digits) >= 7:
        return f"+{digits}"

    # Return original if we can't normalize
    return raw


def normalize_email(raw: str) -> str:
    """
    Normalize an email address.

    Normalization:
        - Lowercase the entire address
        - Strip leading/trailing whitespace
        - Preserve the original if invalid

    Args:
        raw: Raw email address.

    Returns:
        Normalized email address.

    Examples:
        >>> normalize_email("John.Doe@Example.COM")
        'john.doe@example.com'
        >>> normalize_email("  user@domain.org  ")
        'user@domain.org'
    """
    if not raw:
        return raw

    normalized = raw.strip().lower()

    # Basic validation - return original if clearly invalid
    if "@" not in normalized:
        return raw

    return normalized


def detect_contact_type(value: str) -> ContactType:
    """
    Detect whether a contact value is a phone number or email address.

    Uses heuristics:
        - Contains @ → email
        - Mostly digits → phone
        - Otherwise → unknown

    Args:
        value: Contact value (phone or email).

    Returns:
        'phone', 'email', or 'unknown'.

    Examples:
        >>> detect_contact_type("user@example.com")
        'email'
        >>> detect_contact_type("+14155551234")
        'phone'
        >>> detect_contact_type("(415) 555-1234")
        'phone'
    """
    if not value:
        return "unknown"

    cleaned = value.strip()

    # Email detection: contains @
    if "@" in cleaned:
        return "email"

    # Phone detection: extract digits and check count
    digits = re.sub(r"\D", "", cleaned)

    # Phone numbers typically have 7-15 digits
    if len(digits) >= 7 and len(digits) <= 15:
        # Check that digits make up a significant portion of the string
        digit_ratio = len(digits) / len(cleaned.replace(" ", "").replace("-", ""))
        if digit_ratio >= 0.5:
            return "phone"

    return "unknown"


def normalize_handle(value: str) -> tuple[str, ContactType]:
    """
    Normalize a handle value and detect its type.

    Convenience function that combines detection and normalization.

    Args:
        value: Raw handle value from chat.db.

    Returns:
        Tuple of (normalized_value, contact_type).

    Examples:
        >>> normalize_handle("user@example.com")
        ('user@example.com', 'email')
        >>> normalize_handle("+1 (415) 555-1234")
        ('+14155551234', 'phone')
    """
    contact_type = detect_contact_type(value)

    if contact_type == "email":
        return normalize_email(value), contact_type
    elif contact_type == "phone":
        return normalize_phone(value), contact_type
    else:
        return value.strip() if value else value, contact_type
