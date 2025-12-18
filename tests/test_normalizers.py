"""
Tests for ETL normalizers module.

Tests phone normalization, email normalization, and contact type detection
with various formats and edge cases.
"""

import pytest

from imessage_analysis.etl.normalizers import (
    normalize_phone,
    normalize_email,
    detect_contact_type,
    normalize_handle,
)


class TestNormalizePhone:
    """Tests for phone number normalization."""

    def test_already_e164_format(self):
        """Phone already in E.164 format should be unchanged."""
        assert normalize_phone("+14155551234") == "+14155551234"

    def test_us_10_digit_adds_country_code(self):
        """10-digit US number should get +1 prefix."""
        assert normalize_phone("4155551234") == "+14155551234"

    def test_us_with_parentheses(self):
        """US format with parentheses should normalize."""
        assert normalize_phone("(415) 555-1234") == "+14155551234"

    def test_us_with_dashes(self):
        """US format with dashes should normalize."""
        assert normalize_phone("415-555-1234") == "+14155551234"

    def test_us_with_dots(self):
        """US format with dots should normalize."""
        assert normalize_phone("415.555.1234") == "+14155551234"

    def test_us_with_spaces(self):
        """US format with spaces should normalize."""
        assert normalize_phone("415 555 1234") == "+14155551234"

    def test_us_11_digit_with_1_prefix(self):
        """11-digit US number starting with 1 should normalize."""
        assert normalize_phone("14155551234") == "+14155551234"

    def test_international_with_plus(self):
        """International number with + should preserve country code."""
        assert normalize_phone("+442079460958") == "+442079460958"

    def test_international_with_spaces(self):
        """International number with spaces should normalize."""
        assert normalize_phone("+44 20 7946 0958") == "+442079460958"

    def test_international_mixed_format(self):
        """International number with mixed formatting."""
        assert normalize_phone("+44 (20) 7946-0958") == "+442079460958"

    def test_empty_string_returns_empty(self):
        """Empty string should return empty."""
        assert normalize_phone("") == ""

    def test_none_input_returns_none(self):
        """None input should return None (handled gracefully)."""
        assert normalize_phone(None) is None  # type: ignore

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace should be stripped."""
        assert normalize_phone("  +14155551234  ") == "+14155551234"

    def test_short_number_returns_original(self):
        """Very short numbers should return original."""
        assert normalize_phone("12345") == "12345"

    def test_letters_in_number_returns_original(self):
        """Numbers with letters that can't be fully parsed return original."""
        # "1-800-FLOWERS" only has 4 digits (1800) after stripping letters
        # Since 4 digits is too short for a valid phone, it returns the original
        result = normalize_phone("1-800-FLOWERS")
        assert result == "1-800-FLOWERS"


class TestNormalizeEmail:
    """Tests for email normalization."""

    def test_already_lowercase(self):
        """Lowercase email should be unchanged."""
        assert normalize_email("user@example.com") == "user@example.com"

    def test_uppercase_to_lowercase(self):
        """Uppercase email should be lowercased."""
        assert normalize_email("USER@EXAMPLE.COM") == "user@example.com"

    def test_mixed_case(self):
        """Mixed case email should be lowercased."""
        assert normalize_email("User@Example.Com") == "user@example.com"

    def test_whitespace_stripped(self):
        """Whitespace should be stripped."""
        assert normalize_email("  user@example.com  ") == "user@example.com"

    def test_empty_string_returns_empty(self):
        """Empty string should return empty."""
        assert normalize_email("") == ""

    def test_none_input_returns_none(self):
        """None input should return None."""
        assert normalize_email(None) is None  # type: ignore

    def test_no_at_sign_returns_original(self):
        """String without @ should return original."""
        assert normalize_email("notanemail") == "notanemail"

    def test_preserves_plus_addressing(self):
        """Plus addressing should be preserved."""
        assert normalize_email("user+tag@example.com") == "user+tag@example.com"

    def test_preserves_dots_in_local_part(self):
        """Dots in local part should be preserved."""
        assert normalize_email("first.last@example.com") == "first.last@example.com"


class TestDetectContactType:
    """Tests for contact type detection."""

    def test_email_with_at_sign(self):
        """String with @ should be detected as email."""
        assert detect_contact_type("user@example.com") == "email"

    def test_email_with_subdomain(self):
        """Email with subdomain should be detected."""
        assert detect_contact_type("user@mail.example.com") == "email"

    def test_phone_e164_format(self):
        """E.164 phone should be detected as phone."""
        assert detect_contact_type("+14155551234") == "phone"

    def test_phone_with_dashes(self):
        """Phone with dashes should be detected as phone."""
        assert detect_contact_type("415-555-1234") == "phone"

    def test_phone_with_parentheses(self):
        """Phone with parentheses should be detected as phone."""
        assert detect_contact_type("(415) 555-1234") == "phone"

    def test_phone_digits_only(self):
        """Digits-only phone should be detected as phone."""
        assert detect_contact_type("4155551234") == "phone"

    def test_short_string_unknown(self):
        """Very short string should be unknown."""
        assert detect_contact_type("abc") == "unknown"

    def test_empty_string_unknown(self):
        """Empty string should be unknown."""
        assert detect_contact_type("") == "unknown"

    def test_none_unknown(self):
        """None should be unknown."""
        assert detect_contact_type(None) == "unknown"  # type: ignore

    def test_international_phone(self):
        """International phone should be detected."""
        assert detect_contact_type("+442079460958") == "phone"


class TestNormalizeHandle:
    """Tests for the combined normalize_handle function."""

    def test_phone_normalization(self):
        """Phone handles should be normalized and typed correctly."""
        normalized, contact_type = normalize_handle("(415) 555-1234")
        assert normalized == "+14155551234"
        assert contact_type == "phone"

    def test_email_normalization(self):
        """Email handles should be normalized and typed correctly."""
        normalized, contact_type = normalize_handle("User@Example.COM")
        assert normalized == "user@example.com"
        assert contact_type == "email"

    def test_unknown_type(self):
        """Unknown types should be stripped but preserved."""
        normalized, contact_type = normalize_handle("  abc123  ")
        assert normalized == "abc123"
        assert contact_type == "unknown"

    def test_empty_string(self):
        """Empty string should return empty and unknown."""
        normalized, contact_type = normalize_handle("")
        assert normalized == ""
        assert contact_type == "unknown"


class TestNormalizationWithFixtures:
    """Tests using fixtures for comprehensive validation."""

    def test_phone_normalization_samples(self, sample_phones):
        """Test phone normalization with sample data."""
        for raw, expected in sample_phones:
            result = normalize_phone(raw)
            assert result == expected, f"Failed for {raw}: got {result}, expected {expected}"

    def test_email_normalization_samples(self, sample_emails):
        """Test email normalization with sample data."""
        for raw, expected in sample_emails:
            result = normalize_email(raw)
            assert result == expected, f"Failed for {raw}: got {result}, expected {expected}"

    def test_handle_normalization_samples(self, sample_handles):
        """Test handle normalization with sample data."""
        for raw, expected_normalized, expected_type in sample_handles:
            normalized, contact_type = normalize_handle(raw)
            assert normalized == expected_normalized, f"Normalization failed for {raw}"
            assert contact_type == expected_type, f"Type detection failed for {raw}"
