"""Quantum Haar Wavelet Transform (QHWT) Denoising Circuit Synthesizer.

Implements 2D Quantum Haar Wavelet decomposition into sub-bands (|LL>, |LH>, |HL>, |HH>),
frequency-band detail attenuation, and inverse reconstruction.
"""

from typing import Optional, Tuple
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister


class QuantumHaarFilter:
    """Quantum Haar Wavelet Transform (QHWT) frequency sub-band thresholding filter.

    Applies forward QHWT to split image into approximation (|LL>) and detail (|LH>, |HL>, |HH>)
    sub-bands, attenuates high-frequency noise detail amplitudes, and applies inverse QHWT (IQHWT).
    """

    def __init__(self, n_qubits_coord: int = 2, threshold: float = 0.2):
        """Initialize Quantum Haar Filter.

        Args:
            n_qubits_coord: Number of coordinate qubits per dimension (e.g. 2 for 4x4 image).
            threshold: Detail coefficient attenuation factor in [0.0, 1.0].
        """
        self.n_qubits_coord = n_qubits_coord
        self.threshold = float(np.clip(threshold, 0.0, 1.0))

    def build_circuit(self) -> QuantumCircuit:
        """Synthesize forward QHWT + detail thresholding placeholder + inverse QHWT circuit.

        In 2D quantum representation, 1-level 2D Haar wavelet corresponds to Hadamard gates
        applied to the lowest significant coordinate qubits (x_0, y_0).

        Returns:
            QuantumCircuit: The synthesized unitary filtering circuit.
        """
        reg_x = QuantumRegister(self.n_qubits_coord, name="x")
        reg_y = QuantumRegister(self.n_qubits_coord, name="y")
        qc = QuantumCircuit(reg_x, reg_y, name="QHWT_Filter")

        # Forward QHWT: Hadamard on LSB coordinate qubits
        qc.h(reg_x[0])
        qc.h(reg_y[0])
        qc.barrier(label="SubBands_Separated")

        # Detail attenuation stage (controlled phase/rotation attenuation)
        if self.threshold > 0:
            theta_att = (1.0 - self.threshold) * np.pi
            qc.rz(theta_att, reg_x[0])
            qc.rz(theta_att, reg_y[0])

        qc.barrier(label="Thresholding_Complete")

        # Inverse QHWT: Hadamard on LSB coordinate qubits (H^dagger = H)
        qc.h(reg_y[0])
        qc.h(reg_x[0])

        return qc

    def decompose_subbands(
        self, image: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Decompose 2D image into 4 Haar wavelet frequency sub-bands.

        Args:
            image: 2D numpy array of shape (H, W).

        Returns:
            Tuple of (LL, LH, HL, HH) sub-band coefficient matrices.
        """
        assert image.ndim == 2, "Image must be 2D array"
        h, w = image.shape
        assert h % 2 == 0 and w % 2 == 0, "Dimensions must be even for Haar decomposition"

        p00 = image[0::2, 0::2]
        p10 = image[1::2, 0::2]
        p01 = image[0::2, 1::2]
        p11 = image[1::2, 1::2]

        ll = (p00 + p10 + p01 + p11) / 2.0
        lh = (p00 - p10 + p01 - p11) / 2.0
        hl = (p00 + p10 - p01 - p11) / 2.0
        hh = (p00 - p10 - p01 + p11) / 2.0

        return ll, lh, hl, hh

    def denoise_image(self, image: np.ndarray, threshold: Optional[float] = None) -> np.ndarray:
        """Apply 2D Quantum Haar Wavelet Denoising to a 2D image.

        Args:
            image: 2D numpy array normalized in [0, 1].
            threshold: Optional override for detail attenuation factor in [0.0, 1.0].

        Returns:
            np.ndarray: Denoised image array of identical shape.
        """
        t = self.threshold if threshold is None else float(np.clip(threshold, 0.0, 1.0))
        ll, lh, hl, hh = self.decompose_subbands(image)

        # Attenuate high-frequency detail bands
        attenuation = 1.0 - t
        lh_filtered = lh * attenuation
        hl_filtered = hl * attenuation
        hh_filtered = hh * attenuation

        # Inverse 2D Haar wavelet synthesis
        reconstructed = np.zeros_like(image, dtype=np.float64)
        reconstructed[0::2, 0::2] = (ll + lh_filtered + hl_filtered + hh_filtered) / 2.0
        reconstructed[1::2, 0::2] = (ll - lh_filtered + hl_filtered - hh_filtered) / 2.0
        reconstructed[0::2, 1::2] = (ll + lh_filtered - hl_filtered - hh_filtered) / 2.0
        reconstructed[1::2, 1::2] = (ll - lh_filtered - hl_filtered + hh_filtered) / 2.0

        return np.clip(reconstructed, 0.0, 1.0)
