"""Novel Enhanced Quantum Representation (NEQR).

Implements NEQR state preparation using discrete computational basis states
for grayscale image intensities.
"""

from typing import Dict, Optional, Tuple, Union
import numpy as np

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Statevector


class NEQREncoder:
    """Encoder and decoder for Novel Enhanced Quantum Representation (NEQR).

    State formula for a 2^n x 2^n image with q-bit color intensity:
        |I_NEQR> = (1 / 2^n) * sum_{i=0}^{2^{2n}-1} |C(i)> |i>
    where |C(i)> = |C_{q-1}(i) ... C_0(i)> is a q-bit binary register.
    """

    def __init__(self, n_qubits_coord: int = 2, color_bits: int = 8):
        """Initialize NEQR Encoder.

        Args:
            n_qubits_coord: Number of coordinate qubits per dimension (e.g., n=2 for 4x4, n=3 for 8x8).
            color_bits: Bit-depth for pixel intensity (default 8 for 0..255).
        """
        self.n_qubits_coord = n_qubits_coord
        self.color_bits = color_bits
        self.image_size = 1 << n_qubits_coord
        self.total_pixels = self.image_size * self.image_size
        self.n_pos_qubits = 2 * n_qubits_coord
        self.total_qubits = self.n_pos_qubits + self.color_bits
        self.max_intensity = (1 << color_bits) - 1

    def _prepare_image(self, image: np.ndarray) -> np.ndarray:
        """Convert input array to 2D integer array in [0, 2^q - 1]."""
        img = np.asarray(image)
        expected_shape = (self.image_size, self.image_size)
        if img.shape != expected_shape:
            raise ValueError(
                f"Image shape {img.shape} does not match expected {expected_shape} "
                f"for n_qubits_coord={self.n_qubits_coord}."
            )

        if img.dtype in [np.float32, np.float64]:
            if img.max() <= 1.0 and img.min() >= 0.0:
                scaled = np.round(img * self.max_intensity)
            else:
                scaled = np.round(img)
        else:
            scaled = img.astype(np.float64)

        return np.clip(scaled, 0, self.max_intensity).astype(np.int64)

    def encode(self, image: np.ndarray, add_measurement: bool = False) -> QuantumCircuit:
        """Synthesize NEQR state preparation quantum circuit.

        Register layout:
        - Qubits 0 .. color_bits - 1: Color register (|c_0> .. |c_{q-1}>)
        - Qubits color_bits .. total_qubits - 1: Position register (|pos>)

        Args:
            image: 2D array of grayscale pixel intensities.
            add_measurement: Whether to append measurement operations.

        Returns:
            QuantumCircuit: Synthesized Qiskit QuantumCircuit.
        """
        img_int = self._prepare_image(image)
        flat_img = img_int.flatten()

        color_reg = QuantumRegister(self.color_bits, name="c")
        pos_reg = QuantumRegister(self.n_pos_qubits, name="pos")

        qc = QuantumCircuit(color_reg, pos_reg, name="NEQR_Circuit")

        # Step 1: Initialize coordinate register into equal superposition
        for q in pos_reg:
            qc.h(q)

        # Step 2: For each pixel, apply MCX gates to set 1-bits in the color register
        for i, val in enumerate(flat_img):
            if val == 0:
                # Color qubits are already |0>; no MCX needed
                continue

            # Identify coordinate qubits to flip for index i
            zeros_to_flip = [
                pos_reg[k] for k in range(self.n_pos_qubits) if not ((i >> k) & 1)
            ]
            for q in zeros_to_flip:
                qc.x(q)

            # Color bits (c_0 is LSB, c_{q-1} is MSB)
            for k in range(self.color_bits):
                if (val >> k) & 1:
                    qc.mcx(list(pos_reg), color_reg[k])

            # Un-flip coordinate zero-control qubits
            for q in zeros_to_flip:
                qc.x(q)

        if add_measurement:
            c_reg = ClassicalRegister(self.total_qubits, name="meas")
            qc.add_register(c_reg)
            # Measure color register to classical bits 0..color_bits-1
            for k in range(self.color_bits):
                qc.measure(color_reg[k], c_reg[k])
            # Measure position register to classical bits color_bits..total_qubits-1
            for k in range(self.n_pos_qubits):
                qc.measure(pos_reg[k], c_reg[self.color_bits + k])

        return qc

    def decode_statevector(self, statevector: Union[Statevector, np.ndarray]) -> np.ndarray:
        """Lossless exact reconstruction from statevector basis amplitudes.

        Args:
            statevector: Qiskit Statevector or complex 1D array of dimension 2^(2n + q).

        Returns:
            np.ndarray: Reconstructed 2D float image array in [0, 1].
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

        probabilities = np.abs(vec) ** 2
        reconstructed_flat = np.zeros(self.total_pixels, dtype=np.float64)

        # Qiskit basis index:
        # bits 0 .. color_bits - 1: color value C
        # bits color_bits .. total_qubits - 1: position index i
        # index = (i << color_bits) | C
        for i in range(self.total_pixels):
            base_idx = i << self.color_bits
            slice_probs = probabilities[base_idx : base_idx + (1 << self.color_bits)]
            dominant_color = int(np.argmax(slice_probs))
            reconstructed_flat[i] = dominant_color / float(self.max_intensity)

        return reconstructed_flat.reshape((self.image_size, self.image_size))

    def decode(
        self, measurement_counts: Dict[str, int], normalize: bool = True
    ) -> np.ndarray:
        """Decode measurement counts into a 2D image matrix.

        In Qiskit counts bitstrings [b_total-1 ... b_0]:
        - Rightmost `color_bits` characters are the color register [c_{q-1} ... c_0].
        - Preceding characters are the position register [pos_{2n-1} ... pos_0].

        Args:
            measurement_counts: Dictionary of bitstring counts.
            normalize: If True, returns image in [0, 1]; if False, returns integer array [0, 2^q - 1].

        Returns:
            np.ndarray: Reconstructed 2D image matrix.
        """
        reconstructed_flat = np.zeros(self.total_pixels, dtype=np.float64)
        pixel_distributions = [dict() for _ in range(self.total_pixels)]

        for bitstring, count in measurement_counts.items():
            raw = bitstring.replace(" ", "")
            color_str = raw[-self.color_bits :]
            pos_str = raw[: -self.color_bits]

            pos_idx = int(pos_str, 2)
            color_val = int(color_str, 2)

            if pos_idx < self.total_pixels:
                pixel_distributions[pos_idx][color_val] = (
                    pixel_distributions[pos_idx].get(color_val, 0) + count
                )

        for i in range(self.total_pixels):
            dist = pixel_distributions[i]
            if dist:
                # Majority vote for discrete bitstring decoding
                best_color = max(dist.items(), key=lambda item: item[1])[0]
                reconstructed_flat[i] = best_color
            else:
                reconstructed_flat[i] = 0

        if normalize:
            reconstructed_flat = reconstructed_flat / float(self.max_intensity)

        return reconstructed_flat.reshape((self.image_size, self.image_size))
