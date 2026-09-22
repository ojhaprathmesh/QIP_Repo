"""Quantum noise channel definitions using Qiskit Aer noise modules."""

from typing import Optional


def build_depolarizing_model(p_1q: float, p_2q: Optional[float] = None):
    """Build a Qiskit Aer NoiseModel with 1-qubit and 2-qubit depolarizing noise.

    Args:
        p_1q: Depolarizing error probability for single-qubit gates.
        p_2q: Depolarizing error probability for two-qubit gates (defaults to 10 * p_1q).

    Returns:
        NoiseModel: Configured Qiskit Aer NoiseModel.
    """
    raise NotImplementedError("Phase 1 implementation pending.")


def build_thermal_relaxation_model(
    t1_us: float,
    t2_us: float,
    gate_time_1q_ns: float = 35.0,
    gate_time_2q_ns: float = 250.0,
):
    """Build a thermal relaxation noise model parameterized by T1 and T2 times.

    Args:
        t1_us: Longitudinal relaxation time (microseconds).
        t2_us: Dephasing coherence time (microseconds, T2 <= 2*T1).
        gate_time_1q_ns: Duration of 1-qubit gate in nanoseconds.
        gate_time_2q_ns: Duration of 2-qubit gate in nanoseconds.

    Returns:
        NoiseModel: Configured Qiskit Aer NoiseModel.
    """
    raise NotImplementedError("Phase 1 implementation pending.")


def build_composite_nisq_model(backend_name: str = "fake_brisbane"):
    """Build a realistic composite noise model mirroring hardware calibration snapshots.

    Args:
        backend_name: Key from config/hardware_backends.yaml.

    Returns:
        NoiseModel: Composite Qiskit Aer NoiseModel.
    """
    raise NotImplementedError("Phase 1 implementation pending.")
