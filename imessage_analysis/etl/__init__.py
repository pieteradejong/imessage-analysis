"""
ETL (Extract, Transform, Load) module for iMessage Analysis.

This module implements the data architecture described in DATA_ARCHITECTURE.md,
providing a translation layer between Apple's databases (chat.db, AddressBook)
and a stable analytical database (analysis.db) that you control.

Architecture Overview:
    Apple DBs (read-only)     Your DB (read-write)
    ├── chat.db          →    analysis.db
    └── AddressBook      →    ├── dim_person
                              ├── dim_handle
                              ├── dim_contact_method
                              ├── fact_message
                              └── etl_state

Key Design Decisions:
    1. Apple DBs are treated as unstable external APIs (read-only)
    2. All data is normalized before loading (phones → E.164, emails → lowercase)
    3. Identity resolution is a process, not a simple join
    4. Incremental sync via etl_state tracking

See LEARNINGS.md for detailed rationale.
"""

from imessage_analysis.etl.schema import create_schema, SCHEMA_VERSION
from imessage_analysis.etl.normalizers import (
    normalize_phone,
    normalize_email,
    detect_contact_type,
)
from imessage_analysis.etl.extractors import (
    extract_handles,
    extract_messages,
    extract_contacts,
    extract_contact_phones,
    extract_contact_emails,
    Handle,
    Message,
    Contact,
    ContactPhone,
    ContactEmail,
)
from imessage_analysis.etl.loaders import (
    load_handles,
    load_messages,
    load_persons_from_contacts,
    load_contact_methods,
    update_etl_state,
    get_etl_state,
)
from imessage_analysis.etl.identity import (
    resolve_handle_to_person,
    create_unknown_person,
    resolve_all_handles,
)
from imessage_analysis.etl.pipeline import run_etl, get_etl_status, ETLResult
from imessage_analysis.etl.validation import validate_etl, ValidationResult

__all__ = [
    # Schema
    "create_schema",
    "SCHEMA_VERSION",
    # Normalizers
    "normalize_phone",
    "normalize_email",
    "detect_contact_type",
    # Extractors - chat.db
    "extract_handles",
    "extract_messages",
    "Handle",
    "Message",
    # Extractors - contacts
    "extract_contacts",
    "extract_contact_phones",
    "extract_contact_emails",
    "Contact",
    "ContactPhone",
    "ContactEmail",
    # Loaders - chat.db
    "load_handles",
    "load_messages",
    "update_etl_state",
    "get_etl_state",
    # Loaders - contacts
    "load_persons_from_contacts",
    "load_contact_methods",
    # Identity
    "resolve_handle_to_person",
    "create_unknown_person",
    "resolve_all_handles",
    # Pipeline
    "run_etl",
    "get_etl_status",
    "ETLResult",
    # Validation
    "validate_etl",
    "ValidationResult",
]
