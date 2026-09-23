"""Unit tests for FRQI and NEQR state preparation, simulation, and decoding."""

import pytest
import numpy as np
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from src.encoding.frqi import FRQIEncoder
from src.encoding.neqr import NEQREncoder
from src.metrics.image_metrics import compute_psnr, compute_mse


def test_frqi_initialization():
    """Verify FRQI qubit calculation for 8x8 image (n=3) and 4x4 image (n=2)."""
    enc_8x8 = FRQIEncoder(n_qubits_coord=3)
    assert enc_8x8.total_qubits == 2 * 3 + 1  # 7 qubits

    enc_4x4 = FRQIEncoder(n_qubits_coord=2)
    assert enc_4x4.total_qubits == 2 * 2 + 1  # 5 qubits


def test_neqr_initialization():
    """Verify NEQR qubit calculation for 8x8 image with 8-bit color."""
    enc = NEQREncoder(n_qubits_coord=3, color_bits=8)
    assert enc.total_qubits == 2 * 3 + 8  # 14 qubits


def test_frqi_lossless_roundtrip():
    """Verify FRQI state preparation and statevector decoding achieves PSNR > 60 dB."""
    encoder = FRQIEncoder(n_qubits_coord=1)  # 2x2 image
    test_img = np.array([[0.1, 0.4], [0.7, 0.9]], dtype=np.float64)

    qc = encoder.encode(test_img, add_measurement=False)
    sv = Statevector.from_instruction(qc)
    reconstructed = encoder.decode_statevector(sv)

    psnr = compute_psnr(test_img, reconstructed, data_range=1.0)
    assert psnr > 60.0, f"FRQI roundtrip PSNR {psnr} dB is below 60 dB threshold."


def test_neqr_lossless_roundtrip():
    """Verify NEQR state preparation and statevector decoding achieves perfect recovery."""
    encoder = NEQREncoder(n_qubits_coord=1, color_bits=2)  # 2x2 image, 2-bit color
    # Int values: 0, 1, 2, 3 scaled to [0, 1]
    test_img = np.array([[0.0, 0.33333333], [0.66666667, 1.0]], dtype=np.float64)

    qc = encoder.encode(test_img, add_measurement=False)
    sv = Statevector.from_instruction(qc)
    reconstructed = encoder.decode_statevector(sv)

    mse = compute_mse(test_img, reconstructed)
    assert mse < 1e-6, f"NEQR roundtrip MSE {mse} indicates lossy encoding."


from qiskit import transpile


def test_frqi_shot_sampling_roundtrip():
    """Verify FRQI shot-based measurement sampling produces valid reconstruction."""
    encoder = FRQIEncoder(n_qubits_coord=1)
    test_img = np.array([[0.2, 0.5], [0.8, 1.0]], dtype=np.float64)

    qc = encoder.encode(test_img, add_measurement=True)
    sim = AerSimulator()
    qc_t = transpile(qc, sim)
    job = sim.run(qc_t, shots=50000)
    counts = job.result().get_counts()

    reconstructed = encoder.decode(counts, shots=50000)
    assert reconstructed.shape == (2, 2)
    # With 50,000 shots, MSE is bounded by shot sampling variance
    mse = compute_mse(test_img, reconstructed)
    assert mse < 0.05, f"FRQI sampling MSE {mse} unexpectedly high."


def test_neqr_shot_sampling_roundtrip():
    """Verify NEQR shot-based measurement sampling produces exact modal recovery."""
    encoder = NEQREncoder(n_qubits_coord=1, color_bits=2)
    test_img = np.array([[0.0, 0.33333333], [0.66666667, 1.0]], dtype=np.float64)

    qc = encoder.encode(test_img, add_measurement=True)
    sim = AerSimulator()
    qc_t = transpile(qc, sim)
    job = sim.run(qc_t, shots=5000)
    counts = job.result().get_counts()

    reconstructed = encoder.decode(counts, normalize=True)
    assert reconstructed.shape == (2, 2)
    mse = compute_mse(test_img, reconstructed)
    assert mse < 1e-6, f"NEQR discrete sampling MSE {mse} is non-zero."
