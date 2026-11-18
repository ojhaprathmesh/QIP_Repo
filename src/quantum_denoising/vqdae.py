"""Variational Quantum Denoising Autoencoder (VQDAE).

Implements a Hardware-Efficient Parameterized Quantum Circuit (PQC) trained to project
corrupted, noisy quantum states onto the clean manifold. Supports both PennyLane and
Qiskit parameterized circuits, latent bottleneck compression, and a high-performance
classical-quantum surrogate for fast evaluation on micro-resolutions.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import scipy.optimize

from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import Statevector, DensityMatrix

import pennylane as qml

from src.metrics.quantum_metrics import compute_state_fidelity


class VariationalQuantumDenoisingAutoencoder:
    """Parameterized Quantum Circuit (PQC) trained to project noisy states onto clean manifold.

    Features:
        - Hardware-Efficient Ansatz with alternating single-qubit rotations (Ry, Rz)
          and cyclic entangling CNOT layers.
        - Optional latent bottleneck compression subspace (trash qubit tracing/reset).
        - Multi-framework circuit synthesis (PennyLane & Qiskit).
        - Optimization loop minimizing state fidelity loss L = 1 - F(rho_clean, rho_reconstructed)
          via COBYLA or Adam with exact parameter-shift gradients.
        - High-throughput classical-quantum surrogate for micro-resolution evaluation.
    """

    def __init__(
        self,
        n_qubits: int,
        n_layers: int = 4,
        bottleneck_qubits: Optional[int] = None,
        backend: str = "pennylane",
        seed: Optional[int] = 42,
    ):
        """Initialize Variational Quantum Denoising Autoencoder.

        Args:
            n_qubits: Number of quantum system qubits (must be >= 1).
            n_layers: Number of variational ansatz layers (must be >= 1).
            bottleneck_qubits: Optional number of latent bottleneck qubits (1 <= k <= n_qubits).
            backend: Default execution backend ("pennylane", "qiskit", or "surrogate").
            seed: Random seed for parameter initialization.
        """
        if n_qubits < 1:
            raise ValueError(f"n_qubits must be >= 1, got {n_qubits}")
        if n_layers < 1:
            raise ValueError(f"n_layers must be >= 1, got {n_layers}")
        if bottleneck_qubits is not None:
            if bottleneck_qubits < 1 or bottleneck_qubits > n_qubits:
                raise ValueError(
                    f"bottleneck_qubits must be between 1 and n_qubits ({n_qubits}), got {bottleneck_qubits}"
                )

        self.n_qubits = int(n_qubits)
        self.n_layers = int(n_layers)
        self.bottleneck_qubits = int(bottleneck_qubits) if bottleneck_qubits is not None else None
        self.backend = backend.lower()
        self.seed = seed
        self.dim = 1 << self.n_qubits

        # Partition layers into encoder and decoder if bottleneck compression is active
        if self.bottleneck_qubits is not None and self.bottleneck_qubits < self.n_qubits:
            self.n_enc_layers = max(1, self.n_layers // 2)
            self.n_dec_layers = self.n_layers - self.n_enc_layers
        else:
            self.n_enc_layers = self.n_layers
            self.n_dec_layers = 0

        # Each layer applies Ry and Rz on each qubit (2 parameters per qubit per layer)
        self.param_shape = (self.n_layers, self.n_qubits, 2)
        self.n_params = self.n_layers * self.n_qubits * 2

        # Initialize parameters
        rng = np.random.default_rng(seed)
        self.params = rng.uniform(0.0, 2.0 * np.pi, size=self.param_shape)

    def _validate_and_format_params(self, params: Optional[np.ndarray] = None) -> np.ndarray:
        """Validate parameter shape and reshape to (n_layers, n_qubits, 2)."""
        if params is None:
            return self.params.copy()
        p = np.asarray(params, dtype=np.float64)
        if p.size != self.n_params:
            raise ValueError(
                f"Parameter size mismatch: expected {self.n_params} parameters, got {p.size} (shape {p.shape})"
            )
        return p.reshape(self.param_shape)

    def build_qiskit_circuit(
        self,
        params: Optional[np.ndarray] = None,
        parameterized: bool = False,
    ) -> QuantumCircuit:
        """Construct hardware-efficient Qiskit circuit with alternating Ry/Rz and CNOT layers.

        Args:
            params: Optional parameter array. If None and parameterized=False, uses self.params.
            parameterized: If True, uses symbolic ParameterVector('theta', n_params).

        Returns:
            QuantumCircuit: Parameterized or bound Qiskit circuit.
        """
        qc = QuantumCircuit(self.n_qubits, name="VQDAE")
        if parameterized:
            theta = ParameterVector("theta", self.n_params)
            param_idx = 0
        else:
            p = self._validate_and_format_params(params)

        for l in range(self.n_layers):
            # Insert bottleneck trash reset at encoder-decoder boundary
            if (
                self.bottleneck_qubits is not None
                and self.bottleneck_qubits < self.n_qubits
                and l == self.n_enc_layers
            ):
                qc.barrier(label="Bottleneck_Reset")
                for q in range(self.bottleneck_qubits, self.n_qubits):
                    qc.reset(q)
                qc.barrier(label="Decoder_Start")

            # Single-qubit rotations
            for q in range(self.n_qubits):
                if parameterized:
                    qc.ry(theta[param_idx], q)
                    qc.rz(theta[param_idx + 1], q)
                    param_idx += 2
                else:
                    qc.ry(p[l, q, 0], q)
                    qc.rz(p[l, q, 1], q)

            # Entangling CNOT layer
            for q in range(self.n_qubits - 1):
                qc.cx(q, q + 1)
            if self.n_qubits > 2:
                qc.cx(self.n_qubits - 1, 0)

        return qc

    def build_pennylane_circuit(
        self,
        params: Optional[np.ndarray] = None,
        wires: Optional[List[int]] = None,
    ):
        """Construct PennyLane parameterized QNode.

        Args:
            params: Optional parameter array.
            wires: Target wire indices (default range(n_qubits)).

        Returns:
            Callable PennyLane QNode taking (initial_state=None, weights=None) and returning statevector.
        """
        target_wires = wires if wires is not None else list(range(self.n_qubits))
        dev = qml.device("default.qubit", wires=self.n_qubits)
        default_p = self._validate_and_format_params(params)

        @qml.qnode(dev)
        def qnode(initial_state=None, weights=None):
            w = self._validate_and_format_params(weights if weights is not None else default_p)
            if initial_state is not None:
                qml.StatePrep(np.asarray(initial_state, dtype=complex), wires=target_wires)

            for l in range(self.n_layers):
                for q in range(self.n_qubits):
                    qml.RY(w[l, q, 0], wires=target_wires[q])
                    qml.RZ(w[l, q, 1], wires=target_wires[q])
                for q in range(self.n_qubits - 1):
                    qml.CNOT(wires=[target_wires[q], target_wires[q + 1]])
                if self.n_qubits > 2:
                    qml.CNOT(wires=[target_wires[self.n_qubits - 1], target_wires[0]])

            return qml.state()

        return qnode

    def build_ansatz(
        self,
        params: Optional[np.ndarray] = None,
        framework: Optional[str] = None,
    ):
        """Construct hardware-efficient alternating rotation and entangling ansatz.

        Args:
            params: Parameter values. If None, uses self.params or symbolic parameters.
            framework: "pennylane" or "qiskit". Defaults to self.backend.

        Returns:
            QuantumCircuit (if Qiskit) or callable QNode (if PennyLane).
        """
        fw = (framework or self.backend).lower()
        if fw == "qiskit":
            return self.build_qiskit_circuit(params=params)
        elif fw == "pennylane":
            return self.build_pennylane_circuit(params=params)
        else:
            raise ValueError(f"Unsupported framework '{fw}'. Choose 'pennylane' or 'qiskit'.")

    # -------------------------------------------------------------------------
    # Classical-Quantum Surrogate (Vectorized Micro-Resolution Simulator)
    # -------------------------------------------------------------------------

    @staticmethod
    def _apply_single_qubit_gate(
        state_tensor: np.ndarray,
        gate_matrix: np.ndarray,
        qubit: int,
    ) -> np.ndarray:
        """Apply a 2x2 unitary gate to the specified qubit axis of a state tensor."""
        out = np.tensordot(gate_matrix, state_tensor, axes=(1, qubit))
        return np.moveaxis(out, 0, qubit)

    @staticmethod
    def _apply_cnot_gate(
        state_tensor: np.ndarray,
        ctrl: int,
        tgt: int,
    ) -> np.ndarray:
        """Apply CNOT between control and target axes in a state tensor."""
        out = state_tensor.copy()
        idx0 = [slice(None)] * state_tensor.ndim
        idx0[ctrl] = 1
        idx0[tgt] = 0
        idx1 = [slice(None)] * state_tensor.ndim
        idx1[ctrl] = 1
        idx1[tgt] = 1
        tmp = out[tuple(idx0)].copy()
        out[tuple(idx0)] = out[tuple(idx1)]
        out[tuple(idx1)] = tmp
        return out

    def _run_surrogate_statevector(
        self,
        psi: np.ndarray,
        params: np.ndarray,
    ) -> np.ndarray:
        """Execute statevector evolution through the ansatz using tensor contractions."""
        t = np.asarray(psi, dtype=complex).reshape([2] * self.n_qubits)

        for l in range(self.n_layers):
            # Bottleneck trash reset at layer boundary
            if (
                self.bottleneck_qubits is not None
                and self.bottleneck_qubits < self.n_qubits
                and l == self.n_enc_layers
            ):
                # Project trash qubits to |0> and renormalize
                k = self.bottleneck_qubits
                n_trash = self.n_qubits - k
                t_reset = np.zeros_like(t)
                slc_zero = [slice(None)] * k + [0] * n_trash
                t_reset[tuple(slc_zero)] = t[tuple(slc_zero)]
                norm = np.linalg.norm(t_reset)
                t = t_reset / norm if norm > 1e-12 else t_reset

            # Single-qubit rotations
            for q in range(self.n_qubits):
                th, ph = params[l, q, 0], params[l, q, 1]
                c, s = np.cos(th / 2.0), np.sin(th / 2.0)
                ez0, ez1 = np.exp(-1j * ph / 2.0), np.exp(1j * ph / 2.0)
                r_gate = np.array([[ez0 * c, -ez0 * s], [ez1 * s, ez1 * c]], dtype=complex)
                t = self._apply_single_qubit_gate(t, r_gate, q)

            # Entangling CNOT layer
            for q in range(self.n_qubits - 1):
                t = self._apply_cnot_gate(t, q, q + 1)
            if self.n_qubits > 2:
                t = self._apply_cnot_gate(t, self.n_qubits - 1, 0)

        out = t.flatten()
        norm = np.linalg.norm(out)
        return out / norm if norm > 1e-12 else out

    def _partial_trace_and_reset_density_matrix(self, rho: np.ndarray) -> np.ndarray:
        """Partial trace over trash qubits (k to n-1) and tensor with |0...0><0...0|."""
        k = self.bottleneck_qubits
        if k is None or k >= self.n_qubits:
            return rho

        n = self.n_qubits
        n_trash = n - k
        r = rho.reshape([2] * (2 * n))
        r_latent = np.zeros([2] * (2 * k), dtype=complex)

        for idx in range(1 << n_trash):
            trash_bits = [(idx >> bit) & 1 for bit in range(n_trash)]
            slc = [slice(None)] * k + trash_bits + [slice(None)] * k + trash_bits
            r_latent += r[tuple(slc)]

        r_reset = np.zeros([2] * (2 * n), dtype=complex)
        zero_trash = [0] * n_trash
        slc_reset = [slice(None)] * k + zero_trash + [slice(None)] * k + zero_trash
        r_reset[tuple(slc_reset)] = r_latent
        return r_reset.reshape((self.dim, self.dim))

    def _compute_unitary_matrix(
        self,
        params_slice: np.ndarray,
        start_layer: int,
        end_layer: int,
    ) -> np.ndarray:
        """Compute exact unitary matrix for a sequence of layers using basis column mapping."""
        u_mat = np.zeros((self.dim, self.dim), dtype=complex)
        sub_layers = end_layer - start_layer
        sub_params = params_slice[start_layer:end_layer]

        for i in range(self.dim):
            basis = np.zeros(self.dim, dtype=complex)
            basis[i] = 1.0
            t = basis.reshape([2] * self.n_qubits)
            for l in range(sub_layers):
                for q in range(self.n_qubits):
                    th, ph = sub_params[l, q, 0], sub_params[l, q, 1]
                    c, s = np.cos(th / 2.0), np.sin(th / 2.0)
                    ez0, ez1 = np.exp(-1j * ph / 2.0), np.exp(1j * ph / 2.0)
                    r_gate = np.array([[ez0 * c, -ez0 * s], [ez1 * s, ez1 * c]], dtype=complex)
                    t = self._apply_single_qubit_gate(t, r_gate, q)
                for q in range(self.n_qubits - 1):
                    t = self._apply_cnot_gate(t, q, q + 1)
                if self.n_qubits > 2:
                    t = self._apply_cnot_gate(t, self.n_qubits - 1, 0)
            u_mat[:, i] = t.flatten()

        return u_mat

    def classical_quantum_surrogate(
        self,
        state: Union[np.ndarray, Statevector, DensityMatrix],
        params: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Evaluate quantum state through ansatz using fast classical-quantum surrogate.

        Args:
            state: Input quantum state (1D statevector or 2D density matrix).
            params: Optional parameter array.

        Returns:
            np.ndarray: Denoised statevector or density matrix.
        """
        p = self._validate_and_format_params(params)

        # Handle Qiskit Statevector / DensityMatrix conversion
        if isinstance(state, Statevector):
            state_arr = state.data
        elif isinstance(state, DensityMatrix):
            state_arr = state.data
        else:
            state_arr = np.asarray(state)

        # 1D Statevector path
        if state_arr.ndim == 1:
            if state_arr.size != self.dim:
                raise ValueError(
                    f"Statevector dimension mismatch: expected {self.dim}, got {state_arr.size}"
                )
            return self._run_surrogate_statevector(state_arr, p)

        # 2D Density Matrix path
        elif state_arr.ndim == 2:
            if state_arr.shape != (self.dim, self.dim):
                raise ValueError(
                    f"Density matrix shape mismatch: expected ({self.dim}, {self.dim}), got {state_arr.shape}"
                )
            rho = np.asarray(state_arr, dtype=complex)

            if self.bottleneck_qubits is not None and self.bottleneck_qubits < self.n_qubits:
                # Encoder
                u_enc = self._compute_unitary_matrix(p, 0, self.n_enc_layers)
                rho_enc = u_enc @ rho @ u_enc.conj().T
                # Bottleneck reset
                rho_reset = self._partial_trace_and_reset_density_matrix(rho_enc)
                # Decoder
                u_dec = self._compute_unitary_matrix(p, self.n_enc_layers, self.n_layers)
                rho_out = u_dec @ rho_reset @ u_dec.conj().T
            else:
                u_full = self._compute_unitary_matrix(p, 0, self.n_layers)
                rho_out = u_full @ rho @ u_full.conj().T

            tr = np.trace(rho_out)
            return rho_out / tr if np.abs(tr) > 1e-12 else rho_out

        else:
            raise ValueError(f"Expected 1D statevector or 2D density matrix, got shape {state_arr.shape}")

    # -------------------------------------------------------------------------
    # Denoise Inference & Optimization
    # -------------------------------------------------------------------------

    def denoise(
        self,
        noisy_state: Union[np.ndarray, Statevector, DensityMatrix, List[Any]],
        params: Optional[np.ndarray] = None,
        backend: Optional[str] = None,
    ) -> Any:
        """Evaluate variational ansatz with trained parameters to project state onto clean manifold.

        Args:
            noisy_state: Input noisy statevector, density matrix, 2D micro-image, or batch of states.
            params: Optional parameters (defaults to self.params).
            backend: Execution engine ("surrogate", "pennylane", "qiskit").

        Returns:
            Denoised state in format matching input.
        """
        p = self._validate_and_format_params(params)
        engine = (backend or self.backend).lower()

        # Handle batch of states
        if isinstance(noisy_state, list):
            return [self.denoise(s, params=p, backend=backend) for s in noisy_state]

        # Handle Qiskit Statevector
        if isinstance(noisy_state, Statevector):
            out_arr = self.classical_quantum_surrogate(noisy_state.data, params=p)
            return Statevector(out_arr)

        # Handle Qiskit DensityMatrix
        if isinstance(noisy_state, DensityMatrix):
            out_arr = self.classical_quantum_surrogate(noisy_state.data, params=p)
            return DensityMatrix(out_arr)

        arr = np.asarray(noisy_state)

        # 2D Grayscale image path (where H * W == 2^n_qubits)
        if arr.ndim == 2 and not np.iscomplexobj(arr) and arr.shape != (self.dim, self.dim):
            if arr.size == self.dim:
                return self.denoise_image(arr, params=p)

        # Statevector or Density Matrix
        if engine == "pennylane" and arr.ndim == 1 and (self.bottleneck_qubits is None or self.bottleneck_qubits == self.n_qubits):
            circuit = self.build_pennylane_circuit(params=p)
            return np.asarray(circuit(initial_state=arr))
        else:
            # High-performance surrogate (exact and handles bottleneck reset)
            return self.classical_quantum_surrogate(arr, params=p)

    def denoise_image(
        self,
        image: np.ndarray,
        params: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Denoise a 2D grayscale image using amplitude state encoding and VQDAE.

        Args:
            image: 2D array with total pixels == 2^n_qubits.
            params: Optional ansatz parameters.

        Returns:
            np.ndarray: Denoised image matching input shape.
        """
        img_arr = np.asarray(image, dtype=np.float64)
        if img_arr.size != self.dim:
            raise ValueError(
                f"Image size {img_arr.size} ({img_arr.shape}) does not match 2^n_qubits={self.dim}"
            )

        orig_shape = img_arr.shape
        flat = img_arr.flatten()
        norm = np.linalg.norm(flat)
        if norm < 1e-12:
            return np.zeros_like(img_arr)

        state_in = flat / norm
        denoised_state = self.classical_quantum_surrogate(state_in, params=params)
        reconstructed = np.abs(denoised_state) * norm
        return reconstructed.reshape(orig_shape)

    def _loss_single_pair(
        self,
        clean_state: Union[np.ndarray, Statevector, DensityMatrix],
        noisy_state: Union[np.ndarray, Statevector, DensityMatrix],
        params: np.ndarray,
    ) -> float:
        """Compute state fidelity loss L = 1 - F(rho_clean, rho_reconstructed) for one pair."""
        rec_state = self.classical_quantum_surrogate(noisy_state, params=params)

        # Extract pure vectors or density matrices
        if isinstance(clean_state, Statevector):
            clean_arr = clean_state.data
        elif isinstance(clean_state, DensityMatrix):
            clean_arr = clean_state.data
        else:
            clean_arr = np.asarray(clean_state)

        # Pure statevector case
        if clean_arr.ndim == 1 and rec_state.ndim == 1:
            overlap = np.vdot(clean_arr, rec_state)
            fid = float(np.real(overlap * np.conj(overlap)))
        else:
            fid = compute_state_fidelity(clean_arr, rec_state)

        return float(1.0 - np.clip(fid, 0.0, 1.0))

    def fit(
        self,
        noisy_states: Union[np.ndarray, List[Any]],
        clean_states: Union[np.ndarray, List[Any]],
        epochs: int = 50,
        lr: float = 0.05,
        optimizer: str = "adam",
        verbose: bool = False,
    ) -> Dict[str, List[float]]:
        """Train variational ansatz parameters against state fidelity loss.

        Loss function:
            L = 1 - F(rho_clean, rho_reconstructed)

        Args:
            noisy_states: Single noisy state or list of noisy training states.
            clean_states: Single clean reference state or list of clean states.
            epochs: Number of optimization iterations / epochs.
            lr: Learning rate for Adam optimizer.
            optimizer: "adam" (gradient-based via parameter-shift rule) or "cobyla" (simplex).
            verbose: If True, prints loss progression during optimization.

        Returns:
            Dict[str, List[float]]: Training history with 'loss' progression.
        """
        # Standardize state inputs to list
        if not isinstance(noisy_states, list) and (
            isinstance(noisy_states, (Statevector, DensityMatrix)) or (isinstance(noisy_states, np.ndarray) and noisy_states.ndim <= 2)
        ):
            noisy_list = [noisy_states]
        else:
            noisy_list = list(noisy_states)

        if not isinstance(clean_states, list) and (
            isinstance(clean_states, (Statevector, DensityMatrix)) or (isinstance(clean_states, np.ndarray) and clean_states.ndim <= 2)
        ):
            clean_list = [clean_states]
        else:
            clean_list = list(clean_states)

        if len(noisy_list) != len(clean_list):
            raise ValueError(
                f"Mismatch in training dataset sizes: {len(noisy_list)} noisy states vs {len(clean_list)} clean states"
            )

        n_samples = len(noisy_list)

        def objective_fn_flat(flat_p: np.ndarray) -> float:
            p = self._validate_and_format_params(flat_p)
            total_loss = 0.0
            for clean_s, noisy_s in zip(clean_list, noisy_list):
                total_loss += self._loss_single_pair(clean_s, noisy_s, p)
            return float(total_loss / n_samples)

        history: Dict[str, List[float]] = {"loss": []}
        opt_name = optimizer.lower()

        if opt_name == "cobyla":
            initial_loss = objective_fn_flat(self.params.flatten())
            history["loss"].append(initial_loss)

            def cobyla_callback(xk):
                curr_loss = objective_fn_flat(xk)
                history["loss"].append(curr_loss)
                if verbose and len(history["loss"]) % max(1, epochs // 10) == 0:
                    print(f"COBYLA step {len(history['loss']) - 1}: Loss = {curr_loss:.6f}")

            res = scipy.optimize.minimize(
                objective_fn_flat,
                x0=self.params.flatten(),
                method="COBYLA",
                callback=cobyla_callback,
                options={"maxiter": epochs},
            )
            self.params = self._validate_and_format_params(res.x)
            final_loss = objective_fn_flat(self.params.flatten())
            if not history["loss"] or history["loss"][-1] != final_loss:
                history["loss"].append(final_loss)

        elif opt_name == "adam":
            flat_params = self.params.flatten().copy()
            m = np.zeros_like(flat_params)
            v = np.zeros_like(flat_params)
            beta1, beta2, eps_stab = 0.9, 0.999, 1e-8
            shift = np.pi / 2.0

            initial_loss = objective_fn_flat(flat_params)
            history["loss"].append(initial_loss)

            for epoch in range(1, epochs + 1):
                # Compute exact gradient using parameter-shift rule
                grad = np.zeros_like(flat_params)
                for i in range(len(flat_params)):
                    p_plus = flat_params.copy()
                    p_plus[i] += shift
                    p_minus = flat_params.copy()
                    p_minus[i] -= shift
                    grad[i] = (objective_fn_flat(p_plus) - objective_fn_flat(p_minus)) / 2.0

                # Adam moments update
                m = beta1 * m + (1.0 - beta1) * grad
                v = beta2 * v + (1.0 - beta2) * (grad ** 2)
                m_hat = m / (1.0 - beta1 ** epoch)
                v_hat = v / (1.0 - beta2 ** epoch)
                flat_params -= lr * m_hat / (np.sqrt(v_hat) + eps_stab)

                epoch_loss = objective_fn_flat(flat_params)
                history["loss"].append(epoch_loss)

                if verbose and epoch % max(1, epochs // 10) == 0:
                    print(f"Epoch {epoch}/{epochs} - State Fidelity Loss: {epoch_loss:.6f}")

            self.params = self._validate_and_format_params(flat_params)

        else:
            raise ValueError(f"Unsupported optimizer '{optimizer}'. Supported: 'adam', 'cobyla'.")

        return history
