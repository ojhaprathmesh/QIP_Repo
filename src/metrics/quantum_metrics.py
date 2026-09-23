"""Quantum Information and Circuit Complexity Metrics."""

from typing import Dict, Any, Union
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, DensityMatrix, state_fidelity


def compute_state_fidelity(
    state_ideal: Union[Statevector, DensityMatrix, np.ndarray],
    state_noisy: Union[Statevector, DensityMatrix, np.ndarray],
) -> float:
    """Compute Uhlmann-Jozsa quantum state fidelity between two states or density matrices.

    F(rho, sigma) = (Tr(sqrt(sqrt(rho) * sigma * sqrt(rho))))^2

    Args:
        state_ideal: Target ideal pure state or density matrix.
        state_noisy: Corrupted mixed state or density matrix.

    Returns:
        float: Fidelity in [0, 1].
    """
    if isinstance(state_ideal, np.ndarray):
        if state_ideal.ndim == 1:
            state_ideal = Statevector(state_ideal)
        else:
            state_ideal = DensityMatrix(state_ideal)

    if isinstance(state_noisy, np.ndarray):
        if state_noisy.ndim == 1:
            state_noisy = Statevector(state_noisy)
        else:
            state_noisy = DensityMatrix(state_noisy)

    return float(state_fidelity(state_ideal, state_noisy))


def extract_circuit_complexity(circuit: QuantumCircuit) -> Dict[str, Any]:
    """Extract circuit gate count, CNOT count, and critical DAG depth.

    Args:
        circuit: Qiskit QuantumCircuit.

    Returns:
        Dict[str, Any]: Dictionary containing total gates, 2-qubit CNOT count, depth, and ops breakdown.
    """
    ops = dict(circuit.count_ops())
    cnot_count = ops.get("cx", 0) + ops.get("cz", 0) + ops.get("ecr", 0)

    return {
        "num_qubits": circuit.num_qubits,
        "depth": circuit.depth(),
        "total_gates": sum(ops.values()),
        "cnot_count": cnot_count,
        "ops": ops,
    }
