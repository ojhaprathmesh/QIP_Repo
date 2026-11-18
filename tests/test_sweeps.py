"""Unit tests for noise sweep (EXP-01, EXP-02) and bit-flip study (EXP-03) runners."""

import json
from pathlib import Path
import pytest
import numpy as np

from src.experiments.run_noise_sweep import (
    generate_pattern,
    find_log_crossover,
    run_noise_sweep,
)
from src.experiments.run_bitflip_study import run_bitflip_study


def test_generate_pattern():
    """Verify all synthetic test patterns generate valid 2D normalized arrays."""
    for pat in ["checkerboard", "gradient", "shepp_logan", "point_impulse"]:
        img = generate_pattern(pat, 4)
        assert img.shape == (4, 4)
        assert 0.0 <= img.min() <= img.max() <= 1.0


def test_find_log_crossover():
    """Verify log-space root-finding for crossover threshold."""
    x = [1e-4, 1e-3, 1e-2]
    y = [20.0, 10.0, 5.0]
    # Crossing 10 dB at exact point 1e-3
    crit = find_log_crossover(x, y, threshold=10.0, crossing_direction="down")
    assert crit is not None
    assert pytest.approx(crit, rel=1e-3) == 1e-3


def test_bitflip_study_smoke(tmp_path):
    """Verify EXP-03 executes, validates Theorem 2 scaling, and writes valid JSON."""
    out_file = str(tmp_path / "bitflip_test.json")
    results = run_bitflip_study(
        error_rate=0.01,
        resolution=4,
        color_bits=4,
        pattern="checkerboard",
        shots=3000,
        output_path=out_file,
    )

    assert Path(out_file).exists()
    assert "theorem_2_verification" in results
    assert results["theorem_2_verification"]["empirical_verification"] == "PASS"
    assert len(results["results_by_qubit"]) == 4


def test_noise_sweep_smoke(tmp_path):
    """Verify EXP-01/02 executes depolarizing and relaxation sweeps and produces valid output."""
    out_file = str(tmp_path / "noise_sweep_test.json")
    results = run_noise_sweep(
        representation="both",
        resolution=4,
        pattern="checkerboard",
        num_points=2,
        p_min=1e-4,
        p_max=1e-2,
        shots=500,
        output_path=out_file,
    )

    assert Path(out_file).exists()
    assert "depolarizing_sweep" in results
    assert "thermal_relaxation_sweep" in results
    assert "crossover_analysis" in results
    assert "frqi" in results["depolarizing_sweep"]["representations"]
    assert "neqr" in results["depolarizing_sweep"]["representations"]
