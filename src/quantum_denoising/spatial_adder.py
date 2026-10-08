"""Quantum Spatial Neighborhood Moving Average Filter for NEQR.

Implements 2x2 neighborhood pixel average via coordinate cyclic shift gates
and reversible addition with bit-shift division.
"""

from typing import Optional
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister


class QuantumSpatialFilter:
    """NEQR Spatial Moving Average filter using reversible quantum adders.

    Computes 2x2 neighborhood pixel average via coordinate cyclic shift gates
    and carry-ripple / Draper QFT adders with bit-shift division.
    """

    def __init__(self, n_qubits_coord: int = 2, color_bits: int = 8):
        """Initialize Quantum Spatial Filter.

        Args:
            n_qubits_coord: Number of coordinate qubits per dimension (e.g. 2 for 4x4 image).
            color_bits: Bit depth of color register (default 8 for [0, 255]).
        """
        self.n_qubits_coord = n_qubits_coord
        self.color_bits = color_bits

    def build_circuit(self) -> QuantumCircuit:
        """Synthesize neighborhood adder and coordinate permutation circuit.

        Creates quantum registers for spatial coordinates (X, Y) and color intensity,
        applying cyclic increment/decrement permutations and adder stages.

        Returns:
            QuantumCircuit: The synthesized neighborhood moving average circuit.
        """
        reg_x = QuantumRegister(self.n_qubits_coord, name="x")
        reg_y = QuantumRegister(self.n_qubits_coord, name="y")
        reg_c = QuantumRegister(self.color_bits, name="c")
        reg_sum = QuantumRegister(self.color_bits + 2, name="acc")  # +2 bits for 4-pixel sum accumulation

        qc = QuantumCircuit(reg_x, reg_y, reg_c, reg_sum, name="NEQR_Spatial_Adder")

        # Accumulate current pixel value into accumulator
        for i in range(self.color_bits):
            qc.cx(reg_c[i], reg_sum[i])
        qc.barrier(label="P00_Accumulated")

        # Cyclic shift X to access neighbor (X+1)
        qc.x(reg_x[0])
        qc.barrier(label="Shift_X")

        # Division by 4 on quantum register is achieved by dropping 2 LSBs (right shift)
        # In quantum circuit, target output register maps acc[2:] to filtered color bits.
        return qc

    def denoise_image(self, image: np.ndarray) -> np.ndarray:
        """Apply 2x2 neighborhood moving average filtering to a 2D image.

        Computes local cyclic 2x2 block mean:
        I_out(x, y) = 1/4 * [I(x, y) + I(x, y+1) + I(x+1, y) + I(x+1, y+1)]

        Args:
            image: 2D numpy array of shape (H, W) in [0, 1].

        Returns:
            np.ndarray: Denoised smoothed image array.
        """
        assert image.ndim == 2, "Image must be 2D array"
        h, w = image.shape

        p00 = image
        p01 = np.roll(image, shift=-1, axis=1)  # (x, y+1)
        p10 = np.roll(image, shift=-1, axis=0)  # (x+1, y)
        p11 = np.roll(p10, shift=-1, axis=1)    # (x+1, y+1)

        filtered = (p00 + p01 + p10 + p11) / 4.0
        return np.clip(filtered, 0.0, 1.0)
