"""Flexible Representation of Quantum Images (FRQI).

Implements FRQI state preparation using continuous rotation amplitudes
on a single auxiliary color qubit entangled with coordinate basis qubits.
"""

from typing import Dict, Optional, Tuple, Union
import math
import numpy as np

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import RYGate
from qiskit.quantum_info import Statevector


class FRQIEncoder:
    """Encoder and decoder for Flexible Representation of Quantum Images (FRQI).

    State formula for a 2^n x 2^n grayscale image:
        |I_FRQI> = (1 / 2^n) * sum_{i=0}^{2^{2n}-1} (cos(theta_i)|0> + sin(theta_i)|1>) |i>
    where theta_i in [0, pi/2] is mapped from normalized pixel intensity.
    """

    def __init__(self, n_qubits_coord: int = 2, angle_mapping: str = "probability"):
        """Initialize FRQI Encoder.

        Args:
            n_qubits_coord: Number of qubits per spatial dimension (e.g., n=2 for 4x4, n=3 for 8x8).
            angle_mapping: "probability" (P = sin^2(theta) => theta = arcsin(sqrt(P)))
                           or "linear" (P = theta / (pi/2) => theta = P * pi/2).
        """
        self.n_qubits_coord = n_qubits_coord
        self.image_size = 1 << n_qubits_coord
        self.total_pixels = self.image_size * self.image_size
        self.n_pos_qubits = 2 * n_qubits_coord
        self.total_qubits = self.n_pos_qubits + 1  # 2n position + 1 color
        self.angle_mapping = angle_mapping

    def _normalize_image(self, image: np.ndarray) -> np.ndarray:
        """Ensure image is a 2D float array in [0, 1] with shape (2^n, 2^n)."""
        img = np.asarray(image, dtype=np.float64)
        expected_shape = (self.image_size, self.image_size)
        if img.shape != expected_shape:
            raise ValueError(
                f"Image shape {img.shape} does not match expected shape {expected_shape} "
                f"for n_qubits_coord={self.n_qubits_coord}."
            )
        if img.max() > 1.0 or img.dtype == np.uint8:
            img = img / 255.0
        return np.clip(img, 0.0, 1.0)

    def _intensity_to_theta(self, intensity: float) -> float:
        """Map normalized pixel intensity in [0, 1] to angle theta in [0, pi/2]."""
        clamped = max(0.0, min(1.0, float(intensity)))
        if self.angle_mapping == "probability":
            return math.asin(math.sqrt(clamped))
        return clamped * (math.pi / 2.0)

    def _theta_to_intensity(self, theta: float) -> float:
        """Map angle theta in [0, pi/2] back to normalized intensity in [0, 1]."""
        clamped_theta = max(0.0, min(math.pi / 2.0, float(theta)))
        if self.angle_mapping == "probability":
            return math.sin(clamped_theta) ** 2
        return clamped_theta / (math.pi / 2.0)

    def encode(self, image: np.ndarray, add_measurement: bool = False) -> QuantumCircuit:
        """Synthesize FRQI state preparation quantum circuit.

        Register layout:
        - Qubit 0: Color qubit (|c>)
        - Qubits 1 .. 2n: Position qubits (|i>)

        Args:
            image: 2D numpy array representing grayscale image with shape (2^n, 2^n).
            add_measurement: Whether to append measurement operations to classical registers.

        Returns:
            QuantumCircuit: Synthesized Qiskit QuantumCircuit.
        """
        img = self._normalize_image(image)
        flat_img = img.flatten()

        color_reg = QuantumRegister(1, name="c")
        pos_reg = QuantumRegister(self.n_pos_qubits, name="pos")

        qc = QuantumCircuit(color_reg, pos_reg, name="FRQI_Circuit")

        # Step 1: Initialize coordinate register into equal superposition
        for q in pos_reg:
            qc.h(q)

        # Step 2: Encode pixel values via multi-controlled Ry rotations
        for i, intensity in enumerate(flat_img):
            theta = self._intensity_to_theta(intensity)
            if abs(theta) < 1e-9:
                # Ry(0) is identity; skip to reduce circuit depth
                continue

            # Identify control qubits that need to be inverted for coordinate i
            # Qubit pos_reg[k] corresponds to bit k (weight 2^k)
            zeros_to_flip = [
                pos_reg[k] for k in range(self.n_pos_qubits) if not ((i >> k) & 1)
            ]
            for q in zeros_to_flip:
                qc.x(q)

            # Apply multi-controlled Ry(2 * theta) targeting color qubit
            ry_gate = RYGate(2.0 * theta).control(self.n_pos_qubits, annotated=False)
            qc.append(ry_gate, [*pos_reg, color_reg[0]])

            # Restore coordinate register by un-flipping X gates
            for q in zeros_to_flip:
                qc.x(q)

        if add_measurement:
            c_reg = ClassicalRegister(self.total_qubits, name="meas")
            qc.add_register(c_reg)
            # Measure color qubit to bit 0, position qubits to bits 1..2n
            qc.measure(color_reg[0], c_reg[0])
            for k in range(self.n_pos_qubits):
                qc.measure(pos_reg[k], c_reg[k + 1])

        return qc

    def decode_statevector(self, statevector: Union[Statevector, np.ndarray]) -> np.ndarray:
        """Lossless exact reconstruction from pure quantum statevector.

        Args:
            statevector: Qiskit Statevector or 1D complex numpy array of size 2^(2n+1).

        Returns:
            np.ndarray: Reconstructed 2D grayscale image matrix in [0, 1].
        """
        if isinstance(statevector, Statevector):
            vec = statevector.data
        else:
            vec = np.asarray(statevector, dtype=np.complex128)

        expected_dim = 1 << self.total_qubits
        if len(vec) != expected_dim:
            raise ValueError(
                f"Statevector dimension {len(vec)} does not match expected {expected_dim}."
            )

        reconstructed_flat = np.zeros(self.total_pixels, dtype=np.float64)

        # In Qiskit, index bit 0 = color_reg[0], bits 1..2n = pos_reg[0..2n-1]
        # For each coordinate index i:
        # basis state with color=0 is: (i << 1) | 0
        # basis state with color=1 is: (i << 1) | 1
        for i in range(self.total_pixels):
            idx_0 = (i << 1) | 0
            idx_1 = (i << 1) | 1

            amp_0 = vec[idx_0]
            amp_1 = vec[idx_1]

            # theta = arctan2(|amp_1|, |amp_0|)
            theta = math.atan2(abs(amp_1), abs(amp_0))
            reconstructed_flat[i] = self._theta_to_intensity(theta)

        return reconstructed_flat.reshape((self.image_size, self.image_size))

    def decode(self, measurement_counts: Dict[str, int], shots: int) -> np.ndarray:
        """Decode measurement counts back into a 2D image matrix.

        In Qiskit count bitstrings, the order is [q_total-1 ... q_1, q_0].
        - Rightmost character (bit 0): color qubit
        - Remaining characters (bits 1..2n): coordinate position register

        Args:
            measurement_counts: Dictionary of bitstring counts from Z-basis measurement.
            shots: Total number of shots sampled.

        Returns:
            np.ndarray: Reconstructed grayscale image matrix in [0, 1].
        """
        reconstructed_flat = np.zeros(self.total_pixels, dtype=np.float64)
        pos_counts_0 = np.zeros(self.total_pixels, dtype=np.float64)
        pos_counts_1 = np.zeros(self.total_pixels, dtype=np.float64)

        for bitstring, count in measurement_counts.items():
            # Clean possible spaces in bitstrings (e.g. from multiple classical registers)
            raw = bitstring.replace(" ", "")
            color_bit = raw[-1]  # bit 0
            pos_bits = raw[:-1]  # bits 1..2n

            pos_idx = int(pos_bits, 2)
            if pos_idx < self.total_pixels:
                if color_bit == "1":
                    pos_counts_1[pos_idx] += count
                else:
                    pos_counts_0[pos_idx] += count

        for i in range(self.total_pixels):
            total_at_i = pos_counts_0[i] + pos_counts_1[i]
            if total_at_i > 0:
                p_1 = pos_counts_1[i] / total_at_i
                theta = math.asin(math.sqrt(min(1.0, max(0.0, p_1))))
                reconstructed_flat[i] = self._theta_to_intensity(theta)
            else:
                reconstructed_flat[i] = 0.0

        return reconstructed_flat.reshape((self.image_size, self.image_size))
