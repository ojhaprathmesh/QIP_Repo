"""Unit tests for noise channel definitions and parameters."""

import pytest
from src.noise.channels import build_depolarizing_model


def test_depolarizing_placeholder():
    """Verify build_depolarizing_model raises NotImplementedError before Phase 1."""
    with pytest.raises(NotImplementedError):
        build_depolarizing_model(p_1q=0.01)
