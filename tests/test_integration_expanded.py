"""
Expanded integration tests with comprehensive logging.

These tests provide deeper coverage of the ETL pipeline with real data,
including performance benchmarks, data quality checks, and edge case detection.

IMPORTANT: Snapshot-First Strategy
    All integration tests work from snapshots of chat.db, NEVER the original.
    This ensures:
    - Safety: Original database is never touched
    - Consistency: Tests run against a stable point-in-time copy
    - Reproducibility: Same snapshot yields same results
"""

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pytest

from imessage_analysis.etl.pipeline import run_etl, run_etl_with_snapshot, get_etl_status
from imessage_analysis.etl.validation import validate_etl
from imessage_analysis.etl.schema import verify_schema
from imessage_analysis.etl.loaders import (
    get_loaded_handle_count,
    get_loaded_message_count,
    get_loaded_person_count,
)

from tests.integration_logging import get_test_logger, reset_test_logger


@pytest.fixture(scope="module")
def test_logger():
    """Get a test logger for the module."""
    reset_test_logger()
    logger = get_test_logger()
    yield logger
    # Write report at end of module
    logger.write_session_report()


@pytest.mark.integration
class TestRealDatabaseExpanded:
    """
    Expanded integration tests with real chat.db.

    These tests provide more detailed coverage and logging.
    All tests use snapshots via real_chat_db_snapshot fixture.
    """

    def test_etl_with_logging(
        self, real_chat_db_snapshot: Path, real_analysis_db: Path, test_logger
    ):
        """ETL with comprehensive logging of all stages."""
        start = test_logger.log_test_start("test_etl_with_logging", self.__class__.__name__)

        # Log source database stats (using snapshot)
        db_stats = test_logger.log_database_stats(
            chat_db=real_chat_db_snapshot,
            analysis_db=real_analysis_db,
        )

        # Run ETL against snapshot
        result = run_etl(real_chat_db_snapshot, real_analysis_db)
        etl_dict = test_logger.log_etl_result(result)

        # Log post-ETL stats
        db_stats_after = test_logger.log_database_stats(analysis_db=real_analysis_db)
        db_stats["analysis_after"] = db_stats_after.get("analysis")

        # Run validation against snapshot
        validation = validate_etl(real_chat_db_snapshot, real_analysis_db)
        val_dict = test_logger.log_validation_result(validation)

        # Record results
        test_logger.log_test_end(
            "test_etl_with_logging",
            self.__class__.__name__,
            start,
            passed=result.success and validation.passed,
            db_stats=db_stats,
            etl_result=etl_dict,
            validation_result=val_dict,
        )

        assert result.success, f"ETL failed: {result.error}"
        assert validation.passed, f"Validation failed: {validation.summary}"

    def test_performance_benchmark(self, real_chat_db_snapshot: Path, tmp_path: Path, test_logger):
        """Benchmark ETL performance with timing metrics."""
        start = test_logger.log_test_start("test_performance_benchmark", self.__class__.__name__)

        analysis_db = tmp_path / "benchmark_analysis.db"

        # Get source counts for context (using snapshot)
        db_stats = test_logger.log_database_stats(chat_db=real_chat_db_snapshot)

        # Time the ETL against snapshot
        etl_start = time.perf_counter()
        result = run_etl(real_chat_db_snapshot, analysis_db)
        etl_duration = time.perf_counter() - etl_start

        etl_dict = test_logger.log_etl_result(result)

        # Calculate throughput metrics
        notes = []
        if result.success and result.messages_extracted > 0:
            msgs_per_sec = result.messages_extracted / etl_duration
            notes.append(f"Throughput: {msgs_per_sec:.0f} messages/sec")
            notes.append(f"Total ETL time: {etl_duration:.2f}s")

        test_logger.log_test_end(
            "test_performance_benchmark",
            self.__class__.__name__,
            start,
            passed=result.success,
            db_stats=db_stats,
            etl_result=etl_dict,
            notes=notes,
        )

        assert result.success
        # Performance assertion: should process at least 100 msg/sec
        if result.messages_extracted > 1000:
            msgs_per_sec = result.messages_extracted / etl_duration
            assert msgs_per_sec > 100, f"Performance too slow: {msgs_per_sec:.0f} msg/s"

    def test_data_quality_profile(
        self, real_chat_db_snapshot: Path, real_analysis_db: Path, test_logger
    ):
        """Profile data quality metrics after ETL."""
        start = test_logger.log_test_start("test_data_quality_profile", self.__class__.__name__)

        # Run ETL first (using snapshot)
        result = run_etl(real_chat_db_snapshot, real_analysis_db)
        if not result.success:
            test_logger.log_test_end(
                "test_data_quality_profile",
                self.__class__.__name__,
                start,
                passed=False,
                error=result.error,
            )
            pytest.fail(f"ETL failed: {result.error}")

        etl_dict = test_logger.log_etl_result(result)

        # Collect quality metrics
        conn = sqlite3.connect(str(real_analysis_db))
        notes = []

        try:
            # Message text statistics
            cursor = conn.execute(
                """SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN text IS NULL THEN 1 ELSE 0 END) as null_text,
                    SUM(CASE WHEN text = '' THEN 1 ELSE 0 END) as empty_text,
                    AVG(LENGTH(text)) as avg_length
                FROM fact_message;"""
            )
            row = cursor.fetchone()
            total, null_text, empty_text, avg_len = row
            notes.append(f"Messages: {total:,} total")
            notes.append(f"  Null text: {null_text:,} ({100*null_text/total:.1f}%)")
            notes.append(f"  Empty text: {empty_text:,} ({100*empty_text/total:.1f}%)")
            notes.append(f"  Avg length: {avg_len:.0f} chars")

            # Handle type distribution
            cursor = conn.execute(
                """SELECT handle_type, COUNT(*) 
                   FROM dim_handle 
                   GROUP BY handle_type;"""
            )
            handle_types = dict(cursor.fetchall())
            notes.append(f"Handle types: {handle_types}")

            # Phone normalization quality
            cursor = conn.execute(
                """SELECT 
                    SUM(CASE WHEN value_normalized LIKE '+%' THEN 1 ELSE 0 END) as e164,
                    COUNT(*) as total
                FROM dim_handle WHERE handle_type = 'phone';"""
            )
            e164, total_phones = cursor.fetchone()
            if total_phones > 0:
                notes.append(f"E.164 compliance: {100*e164/total_phones:.1f}% of phones")

            # Person resolution rate
            cursor = conn.execute(
                """SELECT 
                    SUM(CASE WHEN person_id IS NOT NULL THEN 1 ELSE 0 END) as resolved,
                    COUNT(*) as total
                FROM dim_handle;"""
            )
            resolved, total_handles = cursor.fetchone()
            notes.append(f"Handle resolution: {100*resolved/total_handles:.1f}% resolved")

            # Date range
            cursor = conn.execute("""SELECT MIN(date_utc), MAX(date_utc) FROM fact_message;""")
            min_date, max_date = cursor.fetchone()
            notes.append(f"Date range: {min_date[:10]} to {max_date[:10]}")

        finally:
            conn.close()

        db_stats = test_logger.log_database_stats(analysis_db=real_analysis_db)

        test_logger.log_test_end(
            "test_data_quality_profile",
            self.__class__.__name__,
            start,
            passed=True,
            db_stats=db_stats,
            etl_result=etl_dict,
            notes=notes,
        )

    def test_incremental_consistency(
        self, real_chat_db_snapshot: Path, tmp_path: Path, test_logger
    ):
        """Verify incremental ETL produces consistent results."""
        start = test_logger.log_test_start("test_incremental_consistency", self.__class__.__name__)

        analysis_db = tmp_path / "incremental_test.db"
        notes = []

        # First run (using snapshot)
        result1 = run_etl(real_chat_db_snapshot, analysis_db)
        notes.append(f"Run 1: {result1.messages_loaded} messages loaded")

        if not result1.success:
            test_logger.log_test_end(
                "test_incremental_consistency",
                self.__class__.__name__,
                start,
                passed=False,
                error=result1.error,
            )
            pytest.fail(f"First ETL failed: {result1.error}")

        conn = sqlite3.connect(str(analysis_db))
        count1 = get_loaded_message_count(conn)
        handles1 = get_loaded_handle_count(conn)
        conn.close()

        # Second run (should be incremental, using same snapshot)
        result2 = run_etl(real_chat_db_snapshot, analysis_db)
        notes.append(f"Run 2: {result2.messages_loaded} messages loaded (incremental)")

        conn = sqlite3.connect(str(analysis_db))
        count2 = get_loaded_message_count(conn)
        handles2 = get_loaded_handle_count(conn)
        conn.close()

        # Third run (verify stability, using same snapshot)
        result3 = run_etl(real_chat_db_snapshot, analysis_db)
        notes.append(f"Run 3: {result3.messages_loaded} messages loaded")

        conn = sqlite3.connect(str(analysis_db))
        count3 = get_loaded_message_count(conn)
        conn.close()

        # Check consistency
        notes.append(f"Message counts: {count1} → {count2} → {count3}")
        notes.append(f"Handle counts: {handles1} → {handles2}")

        test_logger.log_test_end(
            "test_incremental_consistency",
            self.__class__.__name__,
            start,
            passed=result1.success and result2.success and result3.success,
            notes=notes,
        )

        assert result2.is_incremental, "Second run should be incremental"
        assert result3.is_incremental, "Third run should be incremental"
        assert count2 >= count1, "Message count should not decrease"
        assert count3 == count2, "Third run should add no new messages"
        assert handles2 == handles1, "Handle count should be stable"

    def test_edge_case_detection(
        self, real_chat_db_snapshot: Path, real_analysis_db: Path, test_logger
    ):
        """Detect and log edge cases in real data."""
        start = test_logger.log_test_start("test_edge_case_detection", self.__class__.__name__)

        # Run ETL using snapshot
        result = run_etl(real_chat_db_snapshot, real_analysis_db)
        if not result.success:
            test_logger.log_test_end(
                "test_edge_case_detection",
                self.__class__.__name__,
                start,
                passed=False,
                error=result.error,
            )
            pytest.fail(f"ETL failed: {result.error}")

        notes = []
        conn = sqlite3.connect(str(real_analysis_db))

        try:
            # Check for very long messages
            cursor = conn.execute(
                """SELECT COUNT(*), MAX(LENGTH(text)) 
                   FROM fact_message WHERE LENGTH(text) > 10000;"""
            )
            long_count, max_len = cursor.fetchone()
            if long_count > 0:
                notes.append(f"Long messages (>10k chars): {long_count}, max: {max_len}")

            # Check for future dates (data corruption indicator)
            future_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            cursor = conn.execute(
                "SELECT COUNT(*) FROM fact_message WHERE date_utc > ?;",
                (future_date,),
            )
            future_count = cursor.fetchone()[0]
            if future_count > 0:
                notes.append(f"⚠️ Future dates detected: {future_count}")

            # Check for very old dates (pre-iMessage)
            cursor = conn.execute(
                """SELECT COUNT(*) FROM fact_message 
                   WHERE date_utc < '2011-10-01';"""
            )
            old_count = cursor.fetchone()[0]
            if old_count > 0:
                notes.append(f"⚠️ Pre-iMessage dates: {old_count}")

            # Check for unusual handle patterns
            cursor = conn.execute(
                """SELECT value_normalized, handle_type 
                   FROM dim_handle 
                   WHERE handle_type = 'unknown' 
                   LIMIT 5;"""
            )
            unknown_handles = cursor.fetchall()
            if unknown_handles:
                notes.append(f"Unknown handle types: {len(unknown_handles)} found")
                for val, _ in unknown_handles[:3]:
                    notes.append(f"  Example: {val[:30]}...")

            # Check for handles with no messages
            cursor = conn.execute(
                """SELECT COUNT(*) FROM dim_handle h
                   WHERE NOT EXISTS (
                       SELECT 1 FROM fact_message m WHERE m.handle_id = h.handle_id
                   );"""
            )
            orphan_handles = cursor.fetchone()[0]
            notes.append(f"Handles with no messages: {orphan_handles}")

            # Check for messages with no handle (from_me only)
            cursor = conn.execute(
                """SELECT 
                    SUM(CASE WHEN handle_id IS NULL AND is_from_me = 1 THEN 1 ELSE 0 END),
                    SUM(CASE WHEN handle_id IS NULL AND is_from_me = 0 THEN 1 ELSE 0 END)
                FROM fact_message;"""
            )
            null_from_me, null_not_from_me = cursor.fetchone()
            notes.append(
                f"Messages with NULL handle: from_me={null_from_me}, other={null_not_from_me}"
            )

        finally:
            conn.close()

        test_logger.log_test_end(
            "test_edge_case_detection",
            self.__class__.__name__,
            start,
            passed=True,
            notes=notes,
        )


@pytest.mark.integration
class TestRealDatabaseWithContacts:
    """Integration tests combining real chat.db with contacts."""

    def test_full_pipeline_with_contacts(
        self,
        real_chat_db_snapshot: Path,
        tmp_path: Path,
        real_contacts_db: Optional[Path],
        test_logger,
    ):
        """Full ETL with both chat.db and contacts."""
        start = test_logger.log_test_start(
            "test_full_pipeline_with_contacts", self.__class__.__name__
        )

        analysis_db = tmp_path / "full_analysis.db"

        db_stats = test_logger.log_database_stats(
            chat_db=real_chat_db_snapshot,
            contacts_db=real_contacts_db,
        )

        # Run ETL using snapshot
        result = run_etl(
            real_chat_db_snapshot,
            analysis_db,
            contacts_db_path=real_contacts_db,
        )
        etl_dict = test_logger.log_etl_result(result)

        notes = []
        if result.contacts_synced:
            notes.append(f"Contacts synced: {result.contacts_extracted}")
            notes.append(f"Contact methods: {result.contact_methods_loaded}")

        # Check resolution improvement
        conn = sqlite3.connect(str(analysis_db))
        try:
            cursor = conn.execute(
                """SELECT 
                    SUM(CASE WHEN p.source = 'contacts' THEN 1 ELSE 0 END) as from_contacts,
                    SUM(CASE WHEN p.source = 'inferred' THEN 1 ELSE 0 END) as inferred,
                    COUNT(*) as total
                FROM dim_handle h
                JOIN dim_person p ON h.person_id = p.person_id;"""
            )
            from_contacts, inferred, total = cursor.fetchone()
            if total > 0:
                notes.append(f"Resolution: {from_contacts} from contacts, {inferred} inferred")
        finally:
            conn.close()

        test_logger.log_test_end(
            "test_full_pipeline_with_contacts",
            self.__class__.__name__,
            start,
            passed=result.success,
            db_stats=db_stats,
            etl_result=etl_dict,
            notes=notes,
        )

        assert result.success


@pytest.mark.integration
class TestDataConsistency:
    """Tests for data consistency across ETL runs."""

    def test_idempotent_etl(self, real_chat_db_snapshot: Path, tmp_path: Path, test_logger):
        """Multiple ETL runs should be idempotent."""
        start = test_logger.log_test_start("test_idempotent_etl", self.__class__.__name__)

        analysis_db = tmp_path / "idempotent_test.db"
        notes = []

        # Run ETL 5 times against the same snapshot
        counts = []
        for i in range(5):
            result = run_etl(real_chat_db_snapshot, analysis_db)
            if not result.success:
                test_logger.log_test_end(
                    "test_idempotent_etl",
                    self.__class__.__name__,
                    start,
                    passed=False,
                    error=f"Run {i+1} failed: {result.error}",
                )
                pytest.fail(f"Run {i+1} failed")

            conn = sqlite3.connect(str(analysis_db))
            msg_count = get_loaded_message_count(conn)
            handle_count = get_loaded_handle_count(conn)
            person_count = get_loaded_person_count(conn)
            conn.close()

            counts.append((msg_count, handle_count, person_count))
            notes.append(
                f"Run {i+1}: {msg_count} msgs, {handle_count} handles, {person_count} persons"
            )

        # All runs should produce same counts
        first = counts[0]
        all_same = all(c == first for c in counts)

        test_logger.log_test_end(
            "test_idempotent_etl",
            self.__class__.__name__,
            start,
            passed=all_same,
            notes=notes,
        )

        assert all_same, f"Counts varied across runs: {counts}"
