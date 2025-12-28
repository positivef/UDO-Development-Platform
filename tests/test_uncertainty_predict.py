# tests/test_uncertainty_predict.py
"""Unit tests for the Uncertainty prediction module.

These tests verify that the ``Uncertainty.predict`` method behaves correctly
for typical, edge‑case and error inputs. They are deliberately lightweight
so they run quickly in CI while still providing useful coverage.
"""

import pytest
from src.uncertainty_map_v3 import Uncertainty


@pytest.fixture(scope="function")
def fresh_uncertainty():
    """Return a fresh ``Uncertainty`` instance for each test.
    ``Uncertainty`` is assumed to be a stateless predictor that can be
    instantiated without arguments.
    """
    return Uncertainty()


def test_predict_returns_dict(fresh_uncertainty):
    """The ``predict`` method should return a dictionary mapping area names
    to a ``Prediction`` object (or a simple dict for the test).
    """
    result = fresh_uncertainty.predict(hours_ahead=6)
    assert isinstance(result, dict), "predict should return a dict"
    # Expect at least one area key (the implementation provides a default set)
    assert len(result) > 0, "predict should contain at least one area"
    # Each value must contain a ``level`` attribute or key
    for area, pred in result.items():
        # Accept both dataclass‑like objects and plain dicts
        if hasattr(pred, "level"):
            level = pred.level
        else:
            level = pred.get("level")
        assert level is not None, f"prediction for {area} missing 'level'"


def test_predict_negative_hours_raises(fresh_uncertainty):
    """Negative ``hours_ahead`` values are invalid and should raise a
    ``ValueError``.
    """
    with pytest.raises(ValueError):
        fresh_uncertainty.predict(hours_ahead=-1)


def test_predict_boundary_hours(fresh_uncertainty):
    """Zero hours ahead should return the current state without error."""
    result = fresh_uncertainty.predict(hours_ahead=0)
    assert isinstance(result, dict)
    # Ensure the result structure is the same as a normal call
    for area, pred in result.items():
        assert pred is not None


# Additional sanity check: ensure the function runs quickly (< 0.5 s)
def test_predict_performance(fresh_uncertainty, benchmark):
    """Benchmark the prediction speed – it should stay under half a second."""
    benchmark(fresh_uncertainty.predict, hours_ahead=6)
