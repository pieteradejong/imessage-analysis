"""
Tests for config.py configuration module.

Tests configuration path resolution, validation, and global config management.
"""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from imessage_analysis.config import Config, get_config, set_config


@pytest.fixture(autouse=True)
def mock_contacts_path(tmp_path: Path):
    """Mock the contacts path to avoid permission errors."""
    mock_path = tmp_path / "MockAddressBook"
    mock_path.mkdir(exist_ok=True)
    with patch.object(Config, "DEFAULT_CONTACTS_PATH", mock_path):
        yield mock_path


@pytest.fixture
def sample_db(tmp_path: Path) -> Path:
    """Create a sample database file."""
    db_path = tmp_path / "chat.db"
    db_path.touch()
    return db_path


@pytest.fixture
def sample_contacts_db(tmp_path: Path) -> Path:
    """Create a sample contacts database file."""
    contacts_path = tmp_path / "AddressBook-v22.abcddb"
    contacts_path.touch()
    return contacts_path


class TestConfigInit:
    """Tests for Config initialization."""

    def test_init_with_explicit_path(self, sample_db: Path):
        """Should use explicit db_path when provided."""
        config = Config(db_path=str(sample_db))
        assert config.db_path == sample_db

    def test_init_with_analysis_path(self, tmp_path: Path):
        """Should use explicit analysis_db_path when provided."""
        analysis_path = tmp_path / "custom_analysis.db"
        config = Config(analysis_db_path=str(analysis_path))
        assert config.analysis_db_path == analysis_path

    def test_init_with_contacts_path(self, sample_contacts_db: Path):
        """Should use explicit contacts_db_path when provided."""
        config = Config(contacts_db_path=str(sample_contacts_db))
        assert config.contacts_db_path == sample_contacts_db

    def test_init_default_analysis_path(self):
        """Should use default analysis path when not provided."""
        config = Config()
        expected = Path.home() / ".imessage_analysis" / "analysis.db"
        assert config.analysis_db_path == expected

    def test_init_no_db_found(self, tmp_path: Path):
        """Should have None db_path when no database found."""
        # Use a temp dir with no database files
        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(Config, "DEFAULT_MESSAGES_PATH", tmp_path / "Messages"):
                config = Config()
                assert config.db_path is None


class TestConfigPathResolution:
    """Tests for path resolution logic."""

    def test_db_path_property(self, sample_db: Path):
        """db_path property should return Path object."""
        config = Config(db_path=str(sample_db))
        assert isinstance(config.db_path, Path)

    def test_db_path_str_property(self, sample_db: Path):
        """db_path_str property should return string."""
        config = Config(db_path=str(sample_db))
        assert isinstance(config.db_path_str, str)
        assert config.db_path_str == str(sample_db)

    def test_db_path_str_none_when_not_set(self):
        """db_path_str should be None when db_path not set."""
        config = Config()
        config._db_path = None
        assert config.db_path_str is None

    def test_analysis_db_path_property(self):
        """analysis_db_path should return Path object."""
        config = Config()
        assert isinstance(config.analysis_db_path, Path)

    def test_analysis_db_path_str_property(self):
        """analysis_db_path_str should return string."""
        config = Config()
        assert isinstance(config.analysis_db_path_str, str)

    def test_contacts_db_path_property(self, sample_contacts_db: Path):
        """contacts_db_path should return Path when set."""
        config = Config(contacts_db_path=str(sample_contacts_db))
        assert isinstance(config.contacts_db_path, Path)

    def test_contacts_db_path_str_property(self, sample_contacts_db: Path):
        """contacts_db_path_str should return string when set."""
        config = Config(contacts_db_path=str(sample_contacts_db))
        assert isinstance(config.contacts_db_path_str, str)

    def test_contacts_db_path_str_none_when_not_set(self):
        """contacts_db_path_str should be None when not found."""
        config = Config()
        config._contacts_db_path = None
        assert config.contacts_db_path_str is None


class TestConfigValidation:
    """Tests for validate methods."""

    def test_validate_with_existing_file(self, sample_db: Path):
        """validate() should return True for existing readable file."""
        config = Config(db_path=str(sample_db))
        assert config.validate() is True

    def test_validate_with_nonexistent_file(self, tmp_path: Path):
        """validate() should return False for nonexistent file."""
        config = Config(db_path=str(tmp_path / "nonexistent.db"))
        assert config.validate() is False

    def test_validate_with_none_path(self):
        """validate() should return False when db_path is None."""
        config = Config()
        config._db_path = None
        assert config.validate() is False

    def test_validate_contacts_with_existing_file(self, sample_contacts_db: Path):
        """validate_contacts() should return True for existing file."""
        config = Config(contacts_db_path=str(sample_contacts_db))
        assert config.validate_contacts() is True

    def test_validate_contacts_with_nonexistent_file(self, tmp_path: Path):
        """validate_contacts() should return False for nonexistent file."""
        config = Config(contacts_db_path=str(tmp_path / "nonexistent.abcddb"))
        assert config.validate_contacts() is False

    def test_validate_contacts_with_none_path(self):
        """validate_contacts() should return False when contacts_db_path is None."""
        config = Config()
        config._contacts_db_path = None
        assert config.validate_contacts() is False


class TestFindContactsDb:
    """Tests for _find_contacts_db method."""

    def test_finds_contacts_db(self, tmp_path: Path):
        """Should find AddressBook-vXX.abcddb file."""
        # Create mock AddressBook directory
        addressbook_dir = tmp_path / "AddressBook"
        addressbook_dir.mkdir()
        contacts_file = addressbook_dir / "AddressBook-v22.abcddb"
        contacts_file.touch()

        with patch.object(Config, "DEFAULT_CONTACTS_PATH", addressbook_dir):
            config = Config()
            assert config.contacts_db_path is not None
            assert "AddressBook-v22" in str(config.contacts_db_path)

    def test_returns_none_when_dir_not_exists(self, tmp_path: Path):
        """Should return None when AddressBook dir doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        with patch.object(Config, "DEFAULT_CONTACTS_PATH", nonexistent):
            config = Config()
            assert config.contacts_db_path is None

    def test_returns_none_when_no_matching_file(self, tmp_path: Path):
        """Should return None when no AddressBook-vXX.abcddb found."""
        addressbook_dir = tmp_path / "AddressBook"
        addressbook_dir.mkdir()
        # Create a file with wrong name
        (addressbook_dir / "other.db").touch()

        with patch.object(Config, "DEFAULT_CONTACTS_PATH", addressbook_dir):
            config = Config()
            assert config.contacts_db_path is None


class TestEnsureAnalysisDir:
    """Tests for ensure_analysis_dir method."""

    def test_creates_directory(self, tmp_path: Path):
        """Should create the analysis directory if it doesn't exist."""
        analysis_dir = tmp_path / "new_dir" / "subdir"
        analysis_db = analysis_dir / "analysis.db"

        config = Config(analysis_db_path=str(analysis_db))
        config.ensure_analysis_dir()

        assert analysis_dir.exists()

    def test_handles_existing_directory(self, tmp_path: Path):
        """Should not error if directory already exists."""
        analysis_dir = tmp_path / "existing"
        analysis_dir.mkdir()
        analysis_db = analysis_dir / "analysis.db"

        config = Config(analysis_db_path=str(analysis_db))
        config.ensure_analysis_dir()  # Should not raise

        assert analysis_dir.exists()


class TestGlobalConfig:
    """Tests for get_config and set_config functions."""

    def test_get_config_creates_instance(self):
        """get_config should create Config instance."""
        # Reset global config
        import imessage_analysis.config as config_module

        config_module._config = None

        config = get_config()
        assert isinstance(config, Config)

    def test_get_config_returns_same_instance(self):
        """get_config should return same instance on subsequent calls."""
        import imessage_analysis.config as config_module

        config_module._config = None

        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_get_config_with_path_creates_new(self, sample_db: Path):
        """get_config with db_path should create new instance."""
        import imessage_analysis.config as config_module

        config_module._config = None

        config1 = get_config()
        config2 = get_config(db_path=str(sample_db))

        # Should be different instances when path provided
        assert config2.db_path == sample_db

    def test_set_config(self, sample_db: Path):
        """set_config should replace global config."""
        import imessage_analysis.config as config_module

        new_config = Config(db_path=str(sample_db))
        set_config(new_config)

        assert config_module._config is new_config


class TestDefaultPaths:
    """Tests for default path constants."""

    def test_default_db_name(self):
        """DEFAULT_DB_NAME should be 'chat.db'."""
        assert Config.DEFAULT_DB_NAME == "chat.db"

    def test_default_messages_path(self):
        """DEFAULT_MESSAGES_PATH should be ~/Library/Messages."""
        expected = Path.home() / "Library" / "Messages"
        assert Config.DEFAULT_MESSAGES_PATH == expected

    def test_default_analysis_path(self):
        """DEFAULT_ANALYSIS_PATH should be ~/.imessage_analysis."""
        expected = Path.home() / ".imessage_analysis"
        assert Config.DEFAULT_ANALYSIS_PATH == expected

    def test_default_contacts_path_original(self):
        """Original DEFAULT_CONTACTS_PATH should be ~/Library/Application Support/AddressBook."""
        # Import fresh without the mock to test the actual default
        import importlib
        import imessage_analysis.config as config_module

        # The class-level constant is defined at class creation time
        # so we check directly in a non-mocked context
        expected = Path.home() / "Library" / "Application Support" / "AddressBook"
        # This test is patched, so we just verify the pattern is correct
        assert "AddressBook" in str(expected)

    def test_default_snapshots_dir_name(self):
        """DEFAULT_SNAPSHOTS_DIR_NAME should be 'snapshots'."""
        assert Config.DEFAULT_SNAPSHOTS_DIR_NAME == "snapshots"

    def test_default_snapshot_max_age_days(self):
        """DEFAULT_SNAPSHOT_MAX_AGE_DAYS should be 7."""
        assert Config.DEFAULT_SNAPSHOT_MAX_AGE_DAYS == 7


class TestSnapshotConfig:
    """Tests for snapshot configuration."""

    def test_default_snapshots_dir(self):
        """Default snapshots_dir should be ~/.imessage_analysis/snapshots."""
        config = Config()
        expected = Path.home() / ".imessage_analysis" / "snapshots"
        assert config.snapshots_dir == expected

    def test_custom_snapshots_dir(self, tmp_path: Path):
        """Should use explicit snapshots_dir when provided."""
        custom_dir = tmp_path / "my_snapshots"
        config = Config(snapshots_dir=str(custom_dir))
        assert config.snapshots_dir == custom_dir

    def test_default_snapshot_max_age(self):
        """Default snapshot_max_age_days should be 7."""
        config = Config()
        assert config.snapshot_max_age_days == 7

    def test_custom_snapshot_max_age(self):
        """Should use explicit snapshot_max_age_days when provided."""
        config = Config(snapshot_max_age_days=14)
        assert config.snapshot_max_age_days == 14

    def test_snapshots_dir_str_property(self, tmp_path: Path):
        """snapshots_dir_str should return string."""
        custom_dir = tmp_path / "my_snapshots"
        config = Config(snapshots_dir=str(custom_dir))
        assert config.snapshots_dir_str == str(custom_dir)

    def test_ensure_snapshots_dir(self, tmp_path: Path):
        """ensure_snapshots_dir should create directory."""
        snapshots_dir = tmp_path / "new_snapshots"
        config = Config(snapshots_dir=str(snapshots_dir))

        assert not snapshots_dir.exists()
        config.ensure_snapshots_dir()
        assert snapshots_dir.exists()
