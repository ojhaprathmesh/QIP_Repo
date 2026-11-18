"""Unit tests for EXP-04 / EXP-05 Denoising Benchmark and Runner."""

import json
from pathlib import Path
import pytest
import numpy as np

from src.experiments.run_denoising_benchmark import (
    generate_pattern,
    get_noise_model,
    run_benchmark,
    main as denoise_main,
)


def test_generate_patterns():
    """Verify synthetic pattern generation across supported shapes."""
    for pattern in ["checkerboard", "gradient", "shepp_logan", "point_impulse"]:
        img = generate_pattern(pattern, size=4)
        assert img.shape == (4, 4)
        assert img.min() >= 0.0
        assert img.max() <= 1.0


def test_get_noise_model():
    """Verify noise model instantiation across channels."""
    for channel in ["depolarizing", "thermal", "composite"]:
        model = get_noise_model(channel, noise_rate=0.005)
        assert model is not None


def test_run_benchmark_execution(tmp_path: Path):
    """Verify end-to-end benchmark run producing valid structured JSON."""
    out_file = str(tmp_path / "test_benchmark_results.json")
    results = run_benchmark(
        image="shepp_logan",
        resolution=4,
        noise_rate=0.005,
        noise_channel="depolarizing",
        shots=1000,
        output_path=out_file,
        run_sweep=True,
        quick=True,
    )

    assert Path(out_file).exists()
    with open(out_file, "r") as f:
        data = json.load(f)

    # Validate high-level schema
    assert data["experiment_id"] == "EXP-04-05-DENOISING-BENCHMARK"
    assert "configuration" in data
    assert "circuits" in data
    assert "scorecard" in data
    assert "breakeven_analysis" in data
    assert "depth_breakdown_boundary" in data

    # Validate scorecard items
    scorecard = data["scorecard"]
    assert len(scorecard) >= 10
    methods = [row["method"] for row in scorecard]
    assert any("QHWT" in m for m in methods)
    assert any("Spatial Adder" in m for m in methods)
    assert any("Bilateral" in m for m in methods)
    assert any("BM3D" in m for m in methods)

    for row in scorecard:
        assert "psnr" in row
        assert "ssim" in row
        assert "mse" in row
        assert "circuit_depth" in row
        assert "cnot_count" in row

    # Validate EXP-05 Breakeven & Depth Boundary
    assert "p_breakeven" in data["breakeven_analysis"]
    assert "critical_depth_D_crit" in data["depth_breakdown_boundary"]


def test_main_cli_dispatch(tmp_path: Path):
    """Verify main entrypoint with CLI argv."""
    out_file = str(tmp_path / "cli_out.json")
    argv = [
        "--image", "checkerboard",
        "--resolution", "4",
        "--noise-rate", "0.005",
        "--shots", "500",
        "--output", out_file,
        "--skip-sweep",
    ]
    denoise_main(argv)
    assert Path(out_file).exists()
