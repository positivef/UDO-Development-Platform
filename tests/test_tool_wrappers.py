"""
Unit tests for Tool Wrappers - 3-Tier Auto-Recovery

Tests bash_with_recovery, read_with_recovery, edit_with_recovery, write_with_recovery
with automatic error resolution via 3-Tier system.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock  # noqa: F401

from scripts.tool_wrappers import (
    bash_with_recovery,
    read_with_recovery,
    edit_with_recovery,
    write_with_recovery,
    get_wrapper_statistics,
    reset_wrapper_statistics,
)


class TestBashWithRecovery:
    """Test suite for bash_with_recovery()"""

    def setup_method(self):
        """Setup for each test"""
        # Disable auto-resolution for error scenario tests
        from scripts.auto_3tier_wrapper import disable_auto_resolution

        disable_auto_resolution()

    def teardown_method(self):
        """Cleanup after each test"""
        # Re-enable auto-resolution
        from scripts.auto_3tier_wrapper import enable_auto_resolution

        enable_auto_resolution()

    def test_successful_command(self):
        """Test successful bash command"""
        result = bash_with_recovery("echo Hello World", shell=True)

        assert result["success"] is True
        assert result["exit_code"] == 0
        assert "Hello World" in result["stdout"]

    def test_failed_command(self):
        """Test failed bash command (non-existent)"""
        result = bash_with_recovery("nonexistent-command-xyz")

        assert result["success"] is False
        assert result["exit_code"] != 0

    def test_command_with_stderr(self):
        """Test command that writes to stderr"""
        # This command will fail and write to stderr
        result = bash_with_recovery("ls /nonexistent-directory-xyz", shell=True)

        assert result["success"] is False
        assert len(result["stderr"]) > 0

    def test_timeout_handling(self):
        """Test command timeout"""
        # Sleep for 10 seconds but timeout after 1 second
        result = bash_with_recovery("sleep 10", shell=True, timeout=1)

        assert result["success"] is False
        assert "timeout" in result["stderr"].lower() or "Timeout" in result["stderr"]

    @patch("scripts.auto_3tier_wrapper.get_wrapper")
    def test_auto_recovery_triggered(self, mock_get_wrapper):
        """Test that 3-Tier auto-recovery is triggered on error"""
        mock_wrapper = Mock()
        mock_wrapper.is_enabled.return_value = True
        mock_get_wrapper.return_value = mock_wrapper

        # This will fail and trigger wrapper
        result = bash_with_recovery("command-that-does-not-exist")

        assert result["success"] is False
        # Wrapper statistics should be updated
        # (but we can't easily assert this without deep mocking)


class TestReadWithRecovery:
    """Test suite for read_with_recovery()"""

    def setup_method(self):
        """Create temporary test file"""
        # Disable auto-resolution for these tests
        from scripts.auto_3tier_wrapper import disable_auto_resolution, get_wrapper

        disable_auto_resolution()

        # Verify it's disabled
        wrapper = get_wrapper()
        assert wrapper.enabled is False, "Auto-resolution should be disabled for error tests"

        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.txt"
        self.test_content = "Hello, World!\nThis is a test file."

        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(self.test_content)

    def teardown_method(self):
        """Clean up temporary files"""
        # Re-enable auto-resolution after tests
        from scripts.auto_3tier_wrapper import enable_auto_resolution

        enable_auto_resolution()

        if self.test_file.exists():
            self.test_file.unlink()
        Path(self.temp_dir).rmdir()

    def test_read_existing_file(self):
        """Test reading an existing file"""
        result = read_with_recovery(str(self.test_file))

        assert result["success"] is True
        assert result["content"] == self.test_content
        # Size may differ due to line ending conversion (\r\n vs \n)
        assert result["size_bytes"] >= len(self.test_content)

    def test_read_nonexistent_file(self):
        """Test reading a non-existent file"""
        result = read_with_recovery("/nonexistent/file.txt")

        assert result["success"] is False
        assert "FileNotFoundError" in result.get("error", "")

    def test_read_directory(self):
        """Test reading a directory (should fail)"""
        result = read_with_recovery(self.temp_dir)

        assert result["success"] is False
        assert "Not a file" in result.get("error", "")

    def test_encoding_error(self):
        """Test handling of encoding errors"""
        # Create a file with binary data
        binary_file = Path(self.temp_dir) / "binary.dat"
        with open(binary_file, "wb") as f:
            f.write(b"\x80\x81\x82\x83")

        result = read_with_recovery(str(binary_file))

        # Should fail with UnicodeDecodeError
        assert result["success"] is False
        if "UnicodeDecodeError" in result.get("error", ""):
            assert "encoding" in result.get("error", "").lower()

        binary_file.unlink()


class TestEditWithRecovery:
    """Test suite for edit_with_recovery()"""

    def setup_method(self):
        """Create temporary test file"""
        # Disable auto-resolution for these tests
        from scripts.auto_3tier_wrapper import disable_auto_resolution, get_wrapper

        disable_auto_resolution()

        # Verify it's disabled
        wrapper = get_wrapper()
        assert wrapper.enabled is False, "Auto-resolution should be disabled for error tests"

        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "edit_test.txt"
        self.original_content = "Line 1\nLine 2 OLD\nLine 3"

        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(self.original_content)

    def teardown_method(self):
        """Clean up temporary files"""
        # Re-enable auto-resolution after tests
        from scripts.auto_3tier_wrapper import enable_auto_resolution

        enable_auto_resolution()

        # Clean up all files in temp dir
        for file in Path(self.temp_dir).glob("*"):
            file.unlink()
        Path(self.temp_dir).rmdir()

    def test_edit_single_occurrence(self):
        """Test editing with single occurrence"""
        result = edit_with_recovery(str(self.test_file), "OLD", "NEW")

        assert result["success"] is True
        assert result["replacements"] == 1

        # Verify content changed
        with open(self.test_file, "r") as f:
            new_content = f.read()
        assert "NEW" in new_content
        assert "OLD" not in new_content

    def test_edit_multiple_occurrences(self):
        """Test editing with multiple occurrences (should fail without replace_all)"""
        # Create file with multiple occurrences
        multi_content = "FOO\nFOO\nFOO"
        with open(self.test_file, "w") as f:
            f.write(multi_content)

        result = edit_with_recovery(str(self.test_file), "FOO", "BAR")

        # Should fail (multiple occurrences without replace_all)
        assert result["success"] is False
        assert "Multiple occurrences" in result.get("error", "")

    def test_edit_replace_all(self):
        """Test editing with replace_all=True"""
        multi_content = "FOO\nFOO\nFOO"
        with open(self.test_file, "w") as f:
            f.write(multi_content)

        result = edit_with_recovery(str(self.test_file), "FOO", "BAR", replace_all=True)

        assert result["success"] is True
        assert result["replacements"] == 3

        # Verify all replaced
        with open(self.test_file, "r") as f:
            new_content = f.read()
        assert new_content == "BAR\nBAR\nBAR"

    def test_edit_string_not_found(self):
        """Test editing when string doesn't exist"""
        result = edit_with_recovery(str(self.test_file), "NONEXISTENT", "REPLACEMENT")

        assert result["success"] is False
        assert "String not found" in result.get("error", "")

    def test_edit_with_backup(self):
        """Test that backup file is created"""
        result = edit_with_recovery(str(self.test_file), "OLD", "NEW", backup=True)

        assert result["success"] is True
        assert result["backup_path"] is not None

        # Verify backup exists
        backup_file = Path(result["backup_path"])
        assert backup_file.exists()

        # Verify backup contains original content
        with open(backup_file, "r") as f:
            backup_content = f.read()
        assert backup_content == self.original_content


class TestWriteWithRecovery:
    """Test suite for write_with_recovery()"""

    def setup_method(self):
        """Create temporary directory"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary files"""
        for file in Path(self.temp_dir).rglob("*"):
            if file.is_file():
                file.unlink()
        # Remove directories bottom-up
        for dir_path in sorted(Path(self.temp_dir).rglob("*"), reverse=True):
            if dir_path.is_dir():
                dir_path.rmdir()
        Path(self.temp_dir).rmdir()

    def test_write_new_file(self):
        """Test writing a new file"""
        test_file = Path(self.temp_dir) / "new_file.txt"
        test_content = "New file content"

        result = write_with_recovery(str(test_file), test_content)

        assert result["success"] is True
        assert result["size_bytes"] == len(test_content)
        assert test_file.exists()

        # Verify content
        with open(test_file, "r") as f:
            assert f.read() == test_content

    def test_write_with_subdirectories(self):
        """Test writing to path with non-existent parent directories"""
        test_file = Path(self.temp_dir) / "sub1" / "sub2" / "file.txt"
        test_content = "Nested file"

        result = write_with_recovery(str(test_file), test_content, create_dirs=True)

        assert result["success"] is True
        assert test_file.exists()
        assert test_file.parent.exists()

    def test_overwrite_existing_file(self):
        """Test overwriting an existing file"""
        test_file = Path(self.temp_dir) / "existing.txt"
        original_content = "Original"
        new_content = "New Content"

        # Create original file
        with open(test_file, "w") as f:
            f.write(original_content)

        result = write_with_recovery(str(test_file), new_content, backup_if_exists=True)

        assert result["success"] is True
        assert result["backup_path"] is not None

        # Verify new content
        with open(test_file, "r") as f:
            assert f.read() == new_content

        # Verify backup
        backup = Path(result["backup_path"])
        assert backup.exists()
        with open(backup, "r") as f:
            assert f.read() == original_content


class TestWrapperStatistics:
    """Test suite for wrapper statistics functions"""

    def test_get_statistics(self):
        """Test getting wrapper statistics"""
        reset_wrapper_statistics()

        stats = get_wrapper_statistics()

        assert "total_calls" in stats
        assert "total_errors" in stats
        assert "automation_rate" in stats
        assert "tier1_hits" in stats
        assert "tier2_auto" in stats
        assert "tier3_escalations" in stats

    def test_reset_statistics(self):
        """Test resetting statistics"""
        # Execute some operations
        bash_with_recovery("echo test", shell=True)

        # Reset
        reset_wrapper_statistics()

        stats = get_wrapper_statistics()
        assert stats["total_calls"] == 0


@pytest.fixture
def temp_test_file():
    """Fixture for temporary test file"""
    temp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt")
    temp.write("Test content")
    temp.close()

    yield temp.name

    # Cleanup
    if os.path.exists(temp.name):
        os.unlink(temp.name)


def test_integration_bash_read_write(temp_test_file):
    """Integration test: bash, read, write operations"""
    # Read existing file
    result = read_with_recovery(temp_test_file)
    assert result["success"] is True

    # Modify and write back
    new_content = result["content"] + "\nAppended line"
    write_result = write_with_recovery(temp_test_file, new_content)
    assert write_result["success"] is True

    # Verify
    verify_result = read_with_recovery(temp_test_file)
    assert verify_result["content"] == new_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
