"""
Tests for Context Upload Security Features (P0-2)

Tests:
1. ZIP bomb detection (compression ratio > 100:1)
2. ZIP bomb detection (file count > 10,000)
3. ZIP bomb detection (uncompressed size > 1GB)
4. ZIP bomb detection (deeply nested directories > 10 levels)
5. Virus scanning (optional - requires ClamAV daemon)
"""

import io
import zipfile

import pytest

from backend.app.models.kanban_context import ZipBombDetected
from backend.app.services.kanban_context_service import KanbanContextService


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def context_service():
    """Mock context service for testing (no real DB connection needed)"""
    # We'll test the helper methods directly without DB
    # Note: db_pool=None is acceptable for testing helper methods
    service = KanbanContextService(db_pool=None)
    return service


# ============================================================================
# ZIP Bomb Detection Tests
# ============================================================================


def test_zip_bomb_high_compression_ratio(context_service):
    """
    Test ZIP bomb detection: Compression ratio > 100:1

    Simulates a ZIP file with 1MB compressed → 200MB uncompressed (200:1 ratio)
    """
    compressed_size = 1 * 1024 * 1024  # 1MB
    uncompressed_size = 200 * 1024 * 1024  # 200MB
    file_count = 100

    # Create dummy zip file object (not used in this test)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("test.txt", "dummy content")

    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as zip_file:
        with pytest.raises(ZipBombDetected) as exc_info:
            context_service._detect_zip_bomb(compressed_size, uncompressed_size, file_count, zip_file)

        assert "Suspicious compression ratio: 200.0:1" in str(exc_info.value)


def test_zip_bomb_excessive_file_count(context_service):
    """
    Test ZIP bomb detection: File count > 10,000

    Simulates a ZIP with 15,000 files
    """
    compressed_size = 1 * 1024 * 1024  # 1MB
    uncompressed_size = 10 * 1024 * 1024  # 10MB (safe ratio 10:1)
    file_count = 15000  # Excessive file count

    # Create dummy zip file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("test.txt", "dummy content")

    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as zip_file:
        with pytest.raises(ZipBombDetected) as exc_info:
            context_service._detect_zip_bomb(compressed_size, uncompressed_size, file_count, zip_file)

        assert "Excessive file count: 15000 files" in str(exc_info.value)


def test_zip_bomb_excessive_uncompressed_size(context_service):
    """
    Test ZIP bomb detection: Uncompressed size > 1GB

    Simulates a ZIP with 2GB uncompressed size
    """
    compressed_size = 50 * 1024 * 1024  # 50MB (within 50MB limit)
    uncompressed_size = 2 * 1024 * 1024 * 1024  # 2GB (excessive)
    file_count = 100  # Safe file count

    # Create dummy zip file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("test.txt", "dummy content")

    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as zip_file:
        with pytest.raises(ZipBombDetected) as exc_info:
            context_service._detect_zip_bomb(compressed_size, uncompressed_size, file_count, zip_file)

        assert "Excessive uncompressed size: 2.00GB" in str(exc_info.value)


def test_zip_bomb_deeply_nested_directories(context_service):
    """
    Test ZIP bomb detection: Deeply nested directories > 10 levels

    Creates a ZIP with 12-level deep nesting
    """
    compressed_size = 1 * 1024 * 1024  # 1MB
    uncompressed_size = 5 * 1024 * 1024  # 5MB (safe ratio)
    file_count = 10  # Safe file count

    # Create ZIP with deeply nested path (12 levels)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        # Path with 12 levels: a/b/c/d/e/f/g/h/i/j/k/l/file.txt
        deep_path = "/".join([f"level{i}" for i in range(12)]) + "/file.txt"
        zf.writestr(deep_path, "dummy content")

    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as zip_file:
        with pytest.raises(ZipBombDetected) as exc_info:
            context_service._detect_zip_bomb(compressed_size, uncompressed_size, file_count, zip_file)

        assert "Deeply nested path detected" in str(exc_info.value)
        assert "depth: 12, limit: 10" in str(exc_info.value)


def test_safe_zip_passes_all_checks(context_service):
    """
    Test that a safe ZIP file passes all security checks

    Safe ZIP characteristics:
    - Compression ratio: 2:1 (safe)
    - File count: 100 (safe)
    - Uncompressed size: 10MB (safe)
    - Max depth: 3 levels (safe)
    """
    compressed_size = 5 * 1024 * 1024  # 5MB
    uncompressed_size = 10 * 1024 * 1024  # 10MB (2:1 ratio)
    file_count = 100  # Safe

    # Create safe ZIP with shallow nesting (3 levels)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("folder1/folder2/file.txt", "dummy content")

    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as zip_file:
        # Should not raise any exception
        context_service._detect_zip_bomb(compressed_size, uncompressed_size, file_count, zip_file)


# ============================================================================
# Virus Scanning Tests (Optional - requires ClamAV daemon)
# ============================================================================


@pytest.mark.asyncio
async def test_virus_scan_dev_mode_skip(context_service, monkeypatch):
    """
    Test virus scan in development mode (should skip if ClamAV not available)

    Sets ENVIRONMENT=development and verifies scan is skipped gracefully
    """
    monkeypatch.setenv("ENVIRONMENT", "development")

    # Mock pyclamd import failure (ClamAV not installed)
    import sys

    sys.modules["pyclamd"] = None

    # Should not raise exception in dev mode
    test_content = b"dummy file content"
    await context_service._scan_for_virus(test_content, "test.zip")

    # Cleanup
    if "pyclamd" in sys.modules:
        del sys.modules["pyclamd"]


@pytest.mark.skipif(True, reason="Requires ClamAV daemon running")
@pytest.mark.asyncio
async def test_virus_scan_production_mode_requires_clamd(context_service, monkeypatch):
    """
    Test virus scan in production mode (should fail if ClamAV not available)

    NOTE: Skip this test by default as it requires ClamAV daemon running.
    To run: Install ClamAV, start clamd, and remove @pytest.mark.skipif
    """
    from backend.app.models.kanban_context import VirusDetected

    monkeypatch.setenv("ENVIRONMENT", "production")

    # Mock pyclamd import failure
    import sys

    sys.modules["pyclamd"] = None

    test_content = b"dummy file content"

    with pytest.raises(VirusDetected) as exc_info:
        await context_service._scan_for_virus(test_content, "test.zip")

    assert "Virus scanning library not available" in str(exc_info.value)

    # Cleanup
    if "pyclamd" in sys.modules:
        del sys.modules["pyclamd"]


# ============================================================================
# Integration Test (Optional - requires real ClamAV)
# ============================================================================


@pytest.mark.skipif(True, reason="Requires ClamAV daemon and EICAR test file")
@pytest.mark.asyncio
async def test_virus_scan_detects_eicar(context_service):
    """
    Test virus scan with EICAR test file (industry standard test virus)

    EICAR test file is a harmless file used to test antivirus software.
    See: https://en.wikipedia.org/wiki/EICAR_test_file

    NOTE: Skip by default. To run:
    1. Install ClamAV and start clamd
    2. Remove @pytest.mark.skipif
    3. Ensure ENVIRONMENT=production
    """
    from backend.app.models.kanban_context import VirusDetected

    # EICAR test string (standard antivirus test file)
    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

    with pytest.raises(VirusDetected) as exc_info:
        await context_service._scan_for_virus(eicar, "eicar.com")

    assert "Virus detected" in str(exc_info.value)
    assert "eicar.com" in str(exc_info.value)
