"""
Quality Metrics API Integration Tests

Tests for the quality metrics service and API endpoints
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.quality_metrics import QualityMetricsResponse
from app.services.quality_service import QualityMetricsService


def test_quality_service_initialization():
    """Test QualityMetricsService initialization"""
    print("\n[TEST] Testing Quality Service Initialization...")

    service = QualityMetricsService()

    assert service.project_root is not None, "Project root should be set"
    assert service.backend_dir is not None, "Backend directory should be set"
    assert service.frontend_dir is not None, "Frontend directory should be set"

    print(f"[PASS] Quality Service initialized successfully")
    print(f"  - Project Root: {service.project_root}")
    print(f"  - Backend Dir: {service.backend_dir}")
    print(f"  - Frontend Dir: {service.frontend_dir}")


def test_get_all_metrics():
    """Test collecting all quality metrics"""
    print("\n[TEST] Testing Get All Metrics...")

    service = QualityMetricsService()
    metrics = service.get_all_metrics()

    # Verify structure
    assert "overall_score" in metrics, "Should have overall_score"
    assert "code_quality" in metrics, "Should have code_quality"
    assert "test_metrics" in metrics, "Should have test_metrics"
    assert "collected_at" in metrics, "Should have collected_at timestamp"

    # Verify code quality structure
    assert "python" in metrics["code_quality"], "Should have Python metrics"
    assert "typescript" in metrics["code_quality"], "Should have TypeScript metrics"

    # Verify score ranges
    assert (
        0.0 <= metrics["overall_score"] <= 10.0
    ), "Overall score should be between 0-10"

    print(f"[PASS] Overall Quality Score: {metrics['overall_score']:.2f}/10")
    print(f"  - Python (Pylint): {metrics['code_quality']['python']['score']:.2f}/10")
    print(
        f"  - TypeScript (ESLint): {metrics['code_quality']['typescript']['score']:.2f}/10"
    )
    print(f"  - Test Coverage: {metrics['test_metrics']['coverage_percentage']:.2f}%")


def test_pylint_metrics():
    """Test Pylint metrics collection"""
    print("\n[TEST] Testing Pylint Metrics...")

    service = QualityMetricsService()
    metrics = service.get_pylint_metrics()

    # Verify structure
    assert "score" in metrics, "Should have score"
    assert "total_issues" in metrics, "Should have total_issues"
    assert "issues_by_type" in metrics, "Should have issues_by_type"
    assert "analyzed_at" in metrics, "Should have analyzed_at timestamp"

    # If Pylint is installed, verify score range
    if "error" not in metrics:
        assert 0.0 <= metrics["score"] <= 10.0, "Pylint score should be between 0-10"
        print(f"[PASS] Pylint Score: {metrics['score']:.2f}/10")
        print(f"  - Total Issues: {metrics['total_issues']}")
    else:
        print(f"[SKIP] Pylint not available: {metrics['error']}")


def test_eslint_metrics():
    """Test ESLint metrics collection"""
    print("\n[TEST] Testing ESLint Metrics...")

    service = QualityMetricsService()
    metrics = service.get_eslint_metrics()

    # Verify structure
    assert "score" in metrics, "Should have score"
    assert "total_files" in metrics, "Should have total_files"
    assert "total_errors" in metrics, "Should have total_errors"
    assert "total_warnings" in metrics, "Should have total_warnings"
    assert "analyzed_at" in metrics, "Should have analyzed_at timestamp"

    # If ESLint is installed, verify score range
    if "error" not in metrics:
        assert 0.0 <= metrics["score"] <= 10.0, "ESLint score should be between 0-10"
        print(f"[PASS] ESLint Score: {metrics['score']:.2f}/10")
        print(f"  - Files Analyzed: {metrics['total_files']}")
        print(f"  - Errors: {metrics['total_errors']}")
        print(f"  - Warnings: {metrics['total_warnings']}")
    else:
        print(f"[SKIP] ESLint not available: {metrics['error']}")


def test_coverage_metrics():
    """Test test coverage metrics collection"""
    print("\n[TEST] Testing Coverage Metrics...")

    service = QualityMetricsService()
    metrics = service.get_test_coverage_metrics()

    # Verify structure
    assert "coverage_percentage" in metrics, "Should have coverage_percentage"
    assert "tests_total" in metrics, "Should have tests_total"
    assert "tests_passed" in metrics, "Should have tests_passed"
    assert "tests_failed" in metrics, "Should have tests_failed"
    assert "success_rate" in metrics, "Should have success_rate"
    assert "analyzed_at" in metrics, "Should have analyzed_at timestamp"

    # If pytest is installed, verify ranges
    if "error" not in metrics:
        assert (
            0.0 <= metrics["coverage_percentage"] <= 100.0
        ), "Coverage should be 0-100%"
        assert 0.0 <= metrics["success_rate"] <= 100.0, "Success rate should be 0-100%"
        print(f"[PASS] Test Coverage: {metrics['coverage_percentage']:.2f}%")
        print(f"  - Tests Passed: {metrics['tests_passed']}/{metrics['tests_total']}")
        print(f"  - Success Rate: {metrics['success_rate']:.2f}%")
    else:
        print(f"[SKIP] pytest not available: {metrics['error']}")


def test_pydantic_model():
    """Test QualityMetricsResponse Pydantic model"""
    print("\n[TEST] Testing Pydantic Model Validation...")

    service = QualityMetricsService()
    metrics_dict = service.get_all_metrics()

    # Validate with Pydantic model
    try:
        response = QualityMetricsResponse(**metrics_dict)

        assert response.overall_score >= 0.0, "Overall score should be >= 0"
        assert response.overall_score <= 10.0, "Overall score should be <= 10"
        assert response.code_quality is not None, "Code quality should not be None"
        assert response.test_metrics is not None, "Test metrics should not be None"

        print("[PASS] Pydantic model validation successful")
        print(f"  - Model Overall Score: {response.overall_score:.2f}/10")

    except Exception as e:
        print(f"[FAIL] Pydantic validation failed: {e}")
        raise


def run_all_tests():
    """Run all quality metrics tests"""
    print("\n" + "=" * 60)
    print("[TEST] Quality Metrics API Integration Tests")
    print("=" * 60)

    tests = [
        ("Service Initialization", test_quality_service_initialization),
        ("Get All Metrics", test_get_all_metrics),
        ("Pylint Metrics", test_pylint_metrics),
        ("ESLint Metrics", test_eslint_metrics),
        ("Coverage Metrics", test_coverage_metrics),
        ("Pydantic Model", test_pydantic_model),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n[FAIL] {test_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"\n[ERROR] {test_name}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"[SUMMARY] Tests Passed: {passed}/{len(tests)}")
    if failed > 0:
        print(f"[SUMMARY] Tests Failed: {failed}/{len(tests)}")
    print("=" * 60)

    if failed == 0:
        print("\n[SUCCESS] All tests passed successfully!\n")
    else:
        print("\n[FAILURE] Some tests failed!\n")
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
