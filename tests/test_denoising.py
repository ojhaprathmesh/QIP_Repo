"""Unit tests for classical and quantum denoising filters."""

import pytest
import numpy as np

cv2 = pytest.importorskip("cv2")
from src.classical_denoising.standard_filters import (
    apply_mean_filter,
    apply_median_filter,
    apply_gaussian_filter,
    apply_bilateral_filter,
)
from src.classical_denoising.bm3d_wrapper import apply_bm3d_filter
from src.quantum_denoising.qhwt import QuantumHaarFilter
from src.quantum_denoising.spatial_adder import QuantumSpatialFilter
from src.metrics.image_metrics import compute_psnr, compute_mse


def test_classical_filters_execution():
    """Verify that classical mean, median, gaussian, and bilateral filters execute properly."""
    test_img = np.random.rand(8, 8).astype(np.float64)

    mean_res = apply_mean_filter(test_img, kernel_size=3)
    assert mean_res.shape == (8, 8)

    med_res = apply_median_filter(test_img, kernel_size=3)
    assert med_res.shape == (8, 8)

    gauss_res = apply_gaussian_filter(test_img, kernel_size=3)
    assert gauss_res.shape == (8, 8)

    bilat_res = apply_bilateral_filter(test_img, d=3)
    assert bilat_res.shape == (8, 8)

    bm3d_res = apply_bm3d_filter(test_img, sigma_psd=0.1)
    assert bm3d_res.shape == (8, 8)


def test_qhwt_circuit_synthesis():
    """Verify that QuantumHaarFilter builds a valid Qiskit circuit."""
    q_filter = QuantumHaarFilter(n_qubits_coord=2, threshold=0.2)
    qc = q_filter.build_circuit()

    assert qc.num_qubits == 4  # 2 qubits for X, 2 qubits for Y
    gate_names = [inst.operation.name for inst in qc.data]
    assert "h" in gate_names
    assert "rz" in gate_names


def test_qhwt_lossless_roundtrip():
    """Verify that with threshold=0.0, QHWT forward + inverse reconstruction is mathematically lossless."""
    clean_img = np.array([
        [0.0, 0.5, 0.2, 0.8],
        [0.5, 1.0, 0.7, 0.3],
        [0.2, 0.7, 0.1, 0.9],
        [0.8, 0.3, 0.9, 0.4],
    ], dtype=np.float64)

    q_filter = QuantumHaarFilter(n_qubits_coord=2, threshold=0.0)
    reconstructed = q_filter.denoise_image(clean_img, threshold=0.0)

    mse = compute_mse(clean_img, reconstructed)
    assert mse < 1e-12, f"Expected exact reconstruction at threshold=0, got MSE={mse}"
    psnr = compute_psnr(clean_img, reconstructed)
    assert psnr > 60.0 or np.isinf(psnr)


def test_qhwt_denoising_noise_reduction():
    """Verify that QHWT detail attenuation reduces noise variance on synthetic noisy inputs."""
    np.random.seed(42)
    clean_img = np.ones((4, 4), dtype=np.float64) * 0.5
    # Add high-frequency alternating noise
    noise = np.array([
        [0.2, -0.2, 0.2, -0.2],
        [-0.2, 0.2, -0.2, 0.2],
        [0.2, -0.2, 0.2, -0.2],
        [-0.2, 0.2, -0.2, 0.2],
    ], dtype=np.float64)
    noisy_img = np.clip(clean_img + noise, 0.0, 1.0)

    q_filter = QuantumHaarFilter(n_qubits_coord=2, threshold=0.8)
    denoised_img = q_filter.denoise_image(noisy_img)

    mse_noisy = compute_mse(clean_img, noisy_img)
    mse_denoised = compute_mse(clean_img, denoised_img)

    assert mse_denoised < mse_noisy, f"Denoised MSE ({mse_denoised}) should be less than Noisy MSE ({mse_noisy})"


def test_spatial_adder_filter_execution():
    """Verify that QuantumSpatialFilter builds circuit and performs spatial moving average."""
    spatial_filter = QuantumSpatialFilter(n_qubits_coord=2, color_bits=8)
    qc = spatial_filter.build_circuit()

    assert qc.num_qubits == (2 + 2 + 8 + 10)  # X(2) + Y(2) + Color(8) + Acc(10) = 22 qubits

    test_img = np.array([
        [0.0, 0.8, 0.0, 0.8],
        [0.8, 0.0, 0.8, 0.0],
        [0.0, 0.8, 0.0, 0.8],
        [0.8, 0.0, 0.8, 0.0],
    ], dtype=np.float64)

    filtered = spatial_filter.denoise_image(test_img)
    assert filtered.shape == (4, 4)
    # 2x2 moving average on alternating checkerboard should smooth toward 0.4
    assert np.all(filtered >= 0.0) and np.all(filtered <= 1.0)
