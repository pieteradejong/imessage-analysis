"""
Integration test logging framework.

Provides structured logging for integration tests to capture:
- ETL execution metrics
- Database statistics
- Validation results
- Performance timing

Logs are written to both console (summary) and file (detailed JSON).
"""

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Create integration test logger
logger = logging.getLogger("integration_tests")


@dataclass
class DatabaseStats:
    """Statistics about a database."""

    path: str
    size_bytes: int
    table_counts: Dict[str, int]
    timestamp: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())

    @classmethod
    def from_path(cls, db_path: Path, tables: Optional[List[str]] = None) -> "DatabaseStats":
        """Create stats from a database path."""
        if not db_path.exists():
            return cls(path=str(db_path), size_bytes=0, table_counts={})

        size = db_path.stat().st_size
        table_counts = {}

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            )
            all_tables = [row[0] for row in cursor.fetchall()]

            target_tables = tables if tables else all_tables
            for table in target_tables:
                if table in all_tables:
                    try:
                        cursor = conn.execute(f"SELECT COUNT(*) FROM `{table}`;")
                        table_counts[table] = cursor.fetchone()[0]
                    except sqlite3.Error:
                        table_counts[table] = -1
            conn.close()
        except sqlite3.Error:
            pass

        return cls(path=str(db_path), size_bytes=size, table_counts=table_counts)


@dataclass
class IntegrationTestResult:
    """Result of an integration test run."""

    test_name: str
    test_class: str
    passed: bool
    duration_seconds: float
    timestamp: str
    chat_db_stats: Optional[DatabaseStats] = None
    analysis_db_stats: Optional[DatabaseStats] = None
    contacts_db_stats: Optional[DatabaseStats] = None
    etl_result: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "test_name": self.test_name,
            "test_class": self.test_class,
            "passed": self.passed,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp,
            "error": self.error,
            "notes": self.notes,
        }
        if self.chat_db_stats:
            result["chat_db_stats"] = asdict(self.chat_db_stats)
        if self.analysis_db_stats:
            result["analysis_db_stats"] = asdict(self.analysis_db_stats)
        if self.contacts_db_stats:
            result["contacts_db_stats"] = asdict(self.contacts_db_stats)
        if self.etl_result:
            result["etl_result"] = self.etl_result
        if self.validation_result:
            result["validation_result"] = self.validation_result
        return result


class IntegrationTestLogger:
    """
    Logger for integration tests.

    Captures detailed metrics and writes to both console and file.
    """

    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize the logger."""
        self.log_dir = log_dir or Path.home() / ".imessage_analysis" / "test_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[IntegrationTestResult] = []
        self.session_start = datetime.now(tz=timezone.utc)
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")

        # Configure logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up file and console logging."""
        log_file = self.log_dir / f"integration_{self.session_id}.log"

        # File handler for detailed logs
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

        # Console handler for summary
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(message)s"))

        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        logger.info(f"Integration test session started: {self.session_id}")
        logger.debug(f"Log file: {log_file}")

    def log_test_start(self, test_name: str, test_class: str) -> datetime:
        """Log the start of a test."""
        start_time = datetime.now(tz=timezone.utc)
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting: {test_class}::{test_name}")
        logger.debug(f"Start time: {start_time.isoformat()}")
        return start_time

    def log_database_stats(
        self,
        chat_db: Optional[Path] = None,
        analysis_db: Optional[Path] = None,
        contacts_db: Optional[Path] = None,
    ) -> Dict[str, DatabaseStats]:
        """Log database statistics."""
        stats = {}

        if chat_db:
            stats["chat"] = DatabaseStats.from_path(chat_db, tables=["message", "handle", "chat"])
            logger.debug(f"chat.db: {stats['chat'].size_bytes:,} bytes")
            for table, count in stats["chat"].table_counts.items():
                logger.debug(f"  {table}: {count:,} rows")

        if analysis_db:
            stats["analysis"] = DatabaseStats.from_path(
                analysis_db,
                tables=["fact_message", "dim_handle", "dim_person", "dim_contact_method"],
            )
            logger.debug(f"analysis.db: {stats['analysis'].size_bytes:,} bytes")
            for table, count in stats["analysis"].table_counts.items():
                logger.debug(f"  {table}: {count:,} rows")

        if contacts_db:
            stats["contacts"] = DatabaseStats.from_path(
                contacts_db, tables=["ZABCDRECORD", "ZABCDPHONENUMBER", "ZABCDEMAILADDRESS"]
            )
            logger.debug(f"AddressBook: {stats['contacts'].size_bytes:,} bytes")
            for table, count in stats["contacts"].table_counts.items():
                logger.debug(f"  {table}: {count:,} rows")

        return stats

    def log_etl_result(self, result: Any) -> Dict[str, Any]:
        """Log ETL result metrics."""
        result_dict = {
            "success": result.success,
            "handles_extracted": result.handles_extracted,
            "handles_loaded": result.handles_loaded,
            "messages_extracted": result.messages_extracted,
            "messages_loaded": result.messages_loaded,
            "handles_resolved": result.handles_resolved,
            "messages_linked": result.messages_linked,
            "is_incremental": result.is_incremental,
            "contacts_extracted": result.contacts_extracted,
            "contact_methods_loaded": result.contact_methods_loaded,
            "contacts_synced": result.contacts_synced,
            "duration_seconds": result.duration_seconds,
            "error": result.error,
        }

        logger.info(f"ETL Result: {'SUCCESS' if result.success else 'FAILED'}")
        logger.debug(f"  Handles: {result.handles_extracted} → {result.handles_loaded}")
        logger.debug(f"  Messages: {result.messages_extracted} → {result.messages_loaded}")
        logger.debug(f"  Duration: {result.duration_seconds:.2f}s")
        if result.contacts_synced:
            logger.debug(f"  Contacts: {result.contacts_extracted} extracted")
        if result.error:
            logger.error(f"  Error: {result.error}")

        return result_dict

    def log_validation_result(self, result: Any) -> Dict[str, Any]:
        """Log validation result."""
        result_dict = {
            "passed": result.passed,
            "summary": result.summary,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                }
                for c in result.checks
            ],
        }

        logger.info(f"Validation: {'PASSED' if result.passed else 'FAILED'}")
        for check in result.checks:
            symbol = "✓" if check.passed else "✗"
            logger.debug(f"  {symbol} {check.name}: {check.message}")

        return result_dict

    def log_test_end(
        self,
        test_name: str,
        test_class: str,
        start_time: datetime,
        passed: bool,
        db_stats: Optional[Dict[str, DatabaseStats]] = None,
        etl_result: Optional[Dict[str, Any]] = None,
        validation_result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        notes: Optional[List[str]] = None,
    ) -> IntegrationTestResult:
        """Log the end of a test and record results."""
        end_time = datetime.now(tz=timezone.utc)
        duration = (end_time - start_time).total_seconds()

        result = IntegrationTestResult(
            test_name=test_name,
            test_class=test_class,
            passed=passed,
            duration_seconds=duration,
            timestamp=end_time.isoformat(),
            chat_db_stats=db_stats.get("chat") if db_stats else None,
            analysis_db_stats=db_stats.get("analysis") if db_stats else None,
            contacts_db_stats=db_stats.get("contacts") if db_stats else None,
            etl_result=etl_result,
            validation_result=validation_result,
            error=error,
            notes=notes or [],
        )

        self.results.append(result)

        status = "PASSED" if passed else "FAILED"
        logger.info(f"Result: {status} ({duration:.2f}s)")

        return result

    def write_session_report(self) -> Path:
        """Write the full session report to JSON."""
        report_file = self.log_dir / f"integration_{self.session_id}.json"

        session_end = datetime.now(tz=timezone.utc)
        total_duration = (session_end - self.session_start).total_seconds()

        report = {
            "session_id": self.session_id,
            "start_time": self.session_start.isoformat(),
            "end_time": session_end.isoformat(),
            "duration_seconds": total_duration,
            "total_tests": len(self.results),
            "passed_tests": sum(1 for r in self.results if r.passed),
            "failed_tests": sum(1 for r in self.results if not r.passed),
            "results": [r.to_dict() for r in self.results],
        }

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"\n{'='*60}")
        logger.info(f"Session Report: {report_file}")
        logger.info(
            f"Total: {report['total_tests']} tests, "
            f"{report['passed_tests']} passed, "
            f"{report['failed_tests']} failed"
        )

        return report_file

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of test results."""
        return {
            "session_id": self.session_id,
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "total_duration": sum(r.duration_seconds for r in self.results),
        }


# Global logger instance
_test_logger: Optional[IntegrationTestLogger] = None


def get_test_logger() -> IntegrationTestLogger:
    """Get or create the global test logger."""
    global _test_logger
    if _test_logger is None:
        _test_logger = IntegrationTestLogger()
    return _test_logger


def reset_test_logger() -> None:
    """Reset the global test logger (for testing)."""
    global _test_logger
    _test_logger = None
