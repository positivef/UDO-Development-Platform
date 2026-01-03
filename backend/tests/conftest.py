from pathlib import Path
import os
import shutil
import tempfile
import uuid

import pytest
from httpx import AsyncClient
import asyncio
from starlette.testclient import TestClient

# Set test environment variables BEFORE importing app
os.environ["ADMIN_KEY"] = "test-admin-key"
os.environ["DISABLE_AUTH_IN_DEV"] = "false"  # Ensure auth is enabled for tests
os.environ["DISABLE_DEV_AUTH_BYPASS"] = "true"  # Disable DEV mode JWT bypass for proper testing
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-jwt-token-validation-32chars"  # Fixed key for testing

from backend.main import app


# Ensure an event loop is available for legacy asyncio.get_event_loop() usage
@pytest.fixture(autouse=True)
def ensure_event_loop():
    """Create and set a default event loop if none exists.
    This accommodates tests that manually retrieve the loop via
    ``asyncio.get_event_loop()`` which, under ``pytest-asyncio`` strict mode,
    raises a DeprecationWarning because no loop is set as current.
    The fixture runs for every test, providing a fresh loop and cleaning it
    up afterwards.
    """
    try:
        asyncio.get_running_loop()
        yield
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        yield
        loop.close()
        asyncio.set_event_loop(None)


_TEMP_ROOT = Path(__file__).resolve().parents[1] / "_pytest_temp_root"
_TEMP_ROOT.mkdir(exist_ok=True)


class _SafeTemporaryDirectory:
    def __init__(self, suffix=None, prefix=None, dir=None, ignore_cleanup_errors=False):
        base_dir = Path(dir) if dir else _TEMP_ROOT
        name = f"{prefix or 'tmp'}{uuid.uuid4().hex}{suffix or ''}"
        self._path = base_dir / name
        self._path.mkdir(parents=True, exist_ok=False)
        self.name = str(self._path)

    def __enter__(self):
        return self.name

    def __exit__(self, exc_type, exc, tb):
        self.cleanup()
        return False

    def cleanup(self):
        shutil.rmtree(self._path, ignore_errors=True)


def pytest_configure(config):
    tmpdir_plugin = config.pluginmanager.get_plugin("tmpdir")
    if tmpdir_plugin:
        config.pluginmanager.unregister(tmpdir_plugin)
    tempfile.TemporaryDirectory = _SafeTemporaryDirectory


@pytest.fixture
def tmp_path():
    temp_dir = _TEMP_ROOT / f"tmp-{uuid.uuid4().hex}"
    temp_dir.mkdir()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def async_client():
    """Test client for FastAPI integration tests (supports WebSocket)."""
    return TestClient(app)
