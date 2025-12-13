"""Resilience tests for QualityMetricsService command execution."""

from types import SimpleNamespace
from pathlib import Path

import pytest

from backend.app.services.quality_service import QualityMetricsService


def _make_service(tmp_path: Path) -> QualityMetricsService:
    """Create a service instance with temp paths for isolation."""
    service = QualityMetricsService(project_root=tmp_path)
    service.backend_dir = tmp_path
    service.frontend_dir = tmp_path
    return service


def test_pylint_nonzero_exit_parses_metrics(monkeypatch, tmp_path):
    """Ensure pylint metrics are parsed even when exit code is non-zero."""
    target = tmp_path / "app"
    target.mkdir()
    service = _make_service(tmp_path)

    def fake_run_command(cmd, cwd, use_shell_on_windows=False):
        return SimpleNamespace(
            stdout='[{"type": "warning"}]',
            stderr="Your code has been rated at 7.50/10",
            returncode=16,
        )

    monkeypatch.setattr(service, "_run_command", fake_run_command)

    metrics = service.get_pylint_metrics(target)

    assert metrics["score"] == 7.5
    assert metrics["total_issues"] == 1
    assert "error" not in metrics


def test_pylint_missing_binary(monkeypatch, tmp_path):
    """Missing pylint binary returns explicit error message."""
    target = tmp_path / "app"
    target.mkdir()
    service = _make_service(tmp_path)

    def fake_run_command(cmd, cwd):
        raise FileNotFoundError

    monkeypatch.setattr(service, "_run_command", fake_run_command)

    metrics = service.get_pylint_metrics(target)

    assert metrics["error"].startswith("Pylint not installed")


def test_eslint_no_output_reports_error(monkeypatch, tmp_path):
    """ESLint without output surfaces diagnostic instead of crashing."""
    target = tmp_path / "web-dashboard"
    target.mkdir()
    service = _make_service(tmp_path)

    def fake_run_command(cmd, cwd, use_shell_on_windows=False):
        return SimpleNamespace(stdout="", stderr="command not found", returncode=2)

    monkeypatch.setattr(service, "_run_command", fake_run_command)

    metrics = service.get_eslint_metrics(target)

    assert metrics["error"].startswith("ESLint produced no output")
    assert metrics["score"] == 0.0


def test_pytest_failure_with_no_results(monkeypatch, tmp_path):
    """Pytest failure without coverage results is reported clearly."""
    backend_dir = tmp_path / "backend"
    backend_dir.mkdir()
    service = QualityMetricsService(project_root=tmp_path)
    service.backend_dir = backend_dir

    def fake_run_command(cmd, cwd, use_shell_on_windows=False):
        # Return no test results (tests_total=0) with non-zero exit code
        return SimpleNamespace(stdout="", stderr="boom", returncode=1)

    monkeypatch.setattr(service, "_run_command", fake_run_command)

    metrics = service.get_test_coverage_metrics()

    assert metrics["coverage_percentage"] == 0.0
    assert metrics["tests_total"] == 0  # No tests parsed
    assert metrics["error"].startswith("Pytest exited with 1")
