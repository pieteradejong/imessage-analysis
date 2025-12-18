"""
Property-based tests using Hypothesis.

These tests verify invariant properties across a wide range of inputs,
helping to find edge cases that might be missed by example-based tests.
"""

import pytest

from hypothesis import given, settings, strategies as st, assume

from imessage_analysis.etl.normalizers import (
    normalize_phone,
    normalize_email,
    normalize_handle,
    detect_contact_type,
)
from imessage_analysis.utils import format_message_count, format_timestamp


# =============================================================================
# Phone Normalization Properties
# =============================================================================


@pytest.mark.property
class TestNormalizePhoneProperties:
    """Property-based tests for phone normalization."""

    @given(st.text(max_size=100))
    def test_normalize_phone_never_crashes(self, raw_phone: str):
        """Normalization should handle any string input without crashing."""
        result = normalize_phone(raw_phone)
        assert isinstance(result, str)

    @given(st.text(max_size=100))
    def test_normalize_phone_returns_non_empty_for_non_empty(self, raw_phone: str):
        """Non-empty input should return non-empty output."""
        assume(len(raw_phone.strip()) > 0)
        result = normalize_phone(raw_phone)
        assert len(result) > 0

    @given(st.from_regex(r"\+1[2-9]\d{9}", fullmatch=True))
    def test_e164_us_phones_unchanged(self, e164_phone: str):
        """Valid US E.164 phones should normalize to themselves."""
        result = normalize_phone(e164_phone)
        assert result == e164_phone

    @given(st.from_regex(r"\+44\d{10}", fullmatch=True))
    def test_e164_uk_phones_unchanged(self, e164_phone: str):
        """Valid UK E.164 phones should normalize to themselves."""
        result = normalize_phone(e164_phone)
        assert result == e164_phone

    @given(st.from_regex(r"[2-9]\d{9}", fullmatch=True))
    def test_10_digit_us_phones_get_country_code(self, phone: str):
        """10-digit US phones should get +1 prefix."""
        result = normalize_phone(phone)
        assert result.startswith("+1")
        assert result[2:] == phone

    @given(st.integers(min_value=1000000, max_value=9999999999))
    def test_numeric_input_produces_string(self, number: int):
        """Numeric input (as string) should produce a string."""
        result = normalize_phone(str(number))
        assert isinstance(result, str)


# =============================================================================
# Email Normalization Properties
# =============================================================================


@pytest.mark.property
class TestNormalizeEmailProperties:
    """Property-based tests for email normalization."""

    @given(st.text(max_size=100))
    def test_normalize_email_never_crashes(self, raw_email: str):
        """Normalization should handle any string input without crashing."""
        result = normalize_email(raw_email)
        assert isinstance(result, str)

    @given(st.emails())
    def test_normalize_email_always_lowercase(self, email: str):
        """Emails should always be lowercase after normalization."""
        result = normalize_email(email)
        assert result == result.lower()

    @given(st.emails())
    def test_normalize_email_strips_whitespace(self, email: str):
        """Emails should have whitespace stripped."""
        padded = f"  {email}  "
        result = normalize_email(padded)
        assert result == result.strip()

    @given(st.emails())
    def test_normalize_email_idempotent(self, email: str):
        """Normalizing twice should give same result."""
        result1 = normalize_email(email)
        result2 = normalize_email(result1)
        assert result1 == result2


# =============================================================================
# Handle Detection Properties
# =============================================================================


@pytest.mark.property
class TestDetectContactTypeProperties:
    """Property-based tests for contact type detection."""

    @given(st.text(max_size=100))
    def test_detect_type_never_crashes(self, value: str):
        """Detection should handle any string input without crashing."""
        result = detect_contact_type(value)
        assert result in ("phone", "email", "unknown")

    @given(st.emails())
    def test_emails_detected_as_email(self, email: str):
        """Valid emails should be detected as email type."""
        result = detect_contact_type(email)
        assert result == "email"

    @given(st.from_regex(r"\+1[2-9]\d{9}", fullmatch=True))
    def test_e164_phones_detected_as_phone(self, phone: str):
        """E.164 phones should be detected as phone type."""
        result = detect_contact_type(phone)
        assert result == "phone"


# =============================================================================
# Normalize Handle Properties
# =============================================================================


@pytest.mark.property
class TestNormalizeHandleProperties:
    """Property-based tests for handle normalization."""

    @given(st.text(max_size=100))
    def test_normalize_handle_never_crashes(self, value: str):
        """Handle normalization should handle any input without crashing."""
        result = normalize_handle(value)
        assert isinstance(result, tuple)
        assert len(result) == 2

    @given(st.text(max_size=100))
    def test_normalize_handle_returns_string_and_type(self, value: str):
        """Should return (normalized_value, type) tuple."""
        normalized, handle_type = normalize_handle(value)
        assert isinstance(normalized, str)
        assert handle_type in ("phone", "email", "unknown")

    @given(st.emails())
    def test_emails_normalized_correctly(self, email: str):
        """Emails should be normalized and typed correctly."""
        normalized, handle_type = normalize_handle(email)
        assert handle_type == "email"
        assert normalized == normalize_email(email)


# =============================================================================
# Format Message Count Properties
# =============================================================================


@pytest.mark.property
class TestFormatMessageCountProperties:
    """Property-based tests for message count formatting."""

    @given(st.integers(min_value=0, max_value=10**12))
    def test_format_count_never_crashes(self, count: int):
        """Formatting should handle any non-negative integer."""
        result = format_message_count(count)
        assert isinstance(result, str)

    @given(st.integers(min_value=0, max_value=999))
    def test_small_numbers_no_suffix(self, count: int):
        """Numbers under 1000 should have no K/M suffix."""
        result = format_message_count(count)
        assert "K" not in result
        assert "M" not in result

    @given(st.integers(min_value=1000, max_value=999999))
    def test_thousands_have_k_suffix(self, count: int):
        """Numbers 1000-999999 should have K suffix."""
        result = format_message_count(count)
        assert "K" in result

    @given(st.integers(min_value=1000000, max_value=10**12))
    def test_millions_have_m_suffix(self, count: int):
        """Numbers >= 1000000 should have M suffix."""
        result = format_message_count(count)
        assert "M" in result


# =============================================================================
# Format Timestamp Properties
# =============================================================================


@pytest.mark.property
class TestFormatTimestampProperties:
    """Property-based tests for timestamp formatting."""

    @given(st.integers(min_value=0, max_value=10**18))
    def test_format_timestamp_never_crashes(self, timestamp: int):
        """Formatting should handle any non-negative timestamp."""
        result = format_timestamp(timestamp)
        assert isinstance(result, str)

    @given(st.integers(min_value=0, max_value=10**18))
    def test_format_timestamp_has_correct_format(self, timestamp: int):
        """Result should be in YYYY-MM-DD HH:MM:SS format."""
        result = format_timestamp(timestamp)
        # Check basic structure
        assert len(result) == 19
        assert result[4] == "-"
        assert result[7] == "-"
        assert result[10] == " "
        assert result[13] == ":"
        assert result[16] == ":"


# =============================================================================
# Fuzz-like Tests (Extended Hypothesis)
# =============================================================================


@pytest.mark.fuzz
class TestFuzzNormalizers:
    """Fuzz-style tests with aggressive settings."""

    @settings(max_examples=1000)
    @given(st.binary(max_size=200))
    def test_fuzz_normalize_phone_binary(self, raw_bytes: bytes):
        """Fuzz test phone normalization with random binary data."""
        try:
            input_str = raw_bytes.decode("utf-8", errors="replace")
        except Exception:
            return
        result = normalize_phone(input_str)
        assert isinstance(result, str)

    @settings(max_examples=1000)
    @given(st.binary(max_size=200))
    def test_fuzz_normalize_email_binary(self, raw_bytes: bytes):
        """Fuzz test email normalization with random binary data."""
        try:
            input_str = raw_bytes.decode("utf-8", errors="replace")
        except Exception:
            return
        result = normalize_email(input_str)
        assert isinstance(result, str)

    @settings(max_examples=1000)
    @given(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "S", "Z"),
                max_codepoint=0xFFFF,
            ),
            max_size=100,
        )
    )
    def test_fuzz_normalize_handle_unicode(self, value: str):
        """Fuzz test handle normalization with unicode characters."""
        normalized, handle_type = normalize_handle(value)
        assert isinstance(normalized, str)
        assert handle_type in ("phone", "email", "unknown")
