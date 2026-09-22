"""Unit tests for FRQI and NEQR state preparation and decoding."""

import pytest
from src.encoding.frqi import FRQIEncoder
from src.encoding.neqr import NEQREncoder


def test_frqi_initialization():
    """Verify FRQI qubit calculation for 8x8 image (n=3)."""
    encoder = FRQIEncoder(n_qubits_coord=3)
    assert encoder.total_qubits == 2 * 3 + 1  # 7 qubits


def test_neqr_initialization():
    """Verify NEQR qubit calculation for 8x8 image with 8-bit color."""
    encoder = NEQREncoder(n_qubits_coord=3, color_bits=8)
    assert encoder.total_qubits == 2 * 3 + 8  # 14 qubits
