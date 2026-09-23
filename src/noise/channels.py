"""Quantum noise channel definitions using Qiskit Aer noise modules."""

from pathlib import Path
from typing import Optional
import yaml

from qiskit_aer.noise import (
    NoiseModel,
    depolarizing_error,
    thermal_relaxation_error,
    ReadoutError,
)
from .readout import build_readout_error_model


def build_depolarizing_model(
    p_1q: float, p_2q: Optional[float] = None
) -> NoiseModel:
    """Build a Qiskit Aer NoiseModel with 1-qubit and 2-qubit depolarizing noise.

    Args:
        p_1q: Depolarizing error probability for single-qubit gates.
        p_2q: Depolarizing error probability for two-qubit gates (defaults to min(1.0, 10 * p_1q)).

    Returns:
        NoiseModel: Configured Qiskit Aer NoiseModel.
    """
    if p_2q is None:
        p_2q = min(1.0, 10.0 * p_1q)

    noise_model = NoiseModel()

    if p_1q > 0.0:
        err_1q = depolarizing_error(p_1q, 1)
        noise_model.add_all_qubit_quantum_error(
            err_1q, ["u", "u1", "u2", "u3", "h", "x", "y", "z", "ry", "rz", "sx", "id"]
        )

    if p_2q > 0.0:
        err_2q = depolarizing_error(p_2q, 2)
        noise_model.add_all_qubit_quantum_error(err_2q, ["cx", "cz", "ecr"])

    return noise_model


def build_thermal_relaxation_model(
    t1_us: float,
    t2_us: float,
    gate_time_1q_ns: float = 35.0,
    gate_time_2q_ns: float = 250.0,
) -> NoiseModel:
    """Build a thermal relaxation noise model parameterized by T1 and T2 times.

    Physical constraint: T2 <= 2 * T1 (pure dephasing limit).

    Args:
        t1_us: Longitudinal relaxation time (microseconds).
        t2_us: Dephasing coherence time (microseconds).
        gate_time_1q_ns: Duration of 1-qubit gate in nanoseconds.
        gate_time_2q_ns: Duration of 2-qubit gate in nanoseconds.

    Returns:
        NoiseModel: Configured Qiskit Aer NoiseModel.
    """
    # Enforce physical T2 <= 2 * T1 limit
    if t2_us > 2.0 * t1_us:
        t2_us = 2.0 * t1_us

    t1_ns = t1_us * 1000.0
    t2_ns = t2_us * 1000.0

    noise_model = NoiseModel()

    err_1q = thermal_relaxation_error(t1_ns, t2_ns, gate_time_1q_ns)
    noise_model.add_all_qubit_quantum_error(
        err_1q, ["u", "u1", "u2", "u3", "h", "x", "y", "z", "ry", "rz", "sx", "id"]
    )

    err_1q_2 = thermal_relaxation_error(t1_ns, t2_ns, gate_time_2q_ns)
    err_2q = err_1q_2.tensor(err_1q_2)
    noise_model.add_all_qubit_quantum_error(err_2q, ["cx", "cz", "ecr"])

    return noise_model


def build_composite_nisq_model(backend_name: str = "fake_brisbane") -> NoiseModel:
    """Build a realistic composite noise model mirroring hardware calibration snapshots.

    Args:
        backend_name: Key from config/hardware_backends.yaml (default 'fake_brisbane').

    Returns:
        NoiseModel: Composite Qiskit Aer NoiseModel with relaxation, gate depolarizing, and readout errors.
    """
    config_path = Path("config/hardware_backends.yaml")
    backend_info = {}

    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                cfg = yaml.safe_load(f)
                backend_info = cfg.get("backends", {}).get(backend_name, {})
        except Exception:
            backend_info = {}

    t1_us = float(backend_info.get("average_t1_us", 240.0))
    t2_us = float(backend_info.get("average_t2_us", 150.0))
    cnot_err = float(backend_info.get("average_cnot_error", 0.008))
    readout_err = float(backend_info.get("average_readout_error", 0.015))

    # 1. Base thermal relaxation
    noise_model = build_thermal_relaxation_model(t1_us, t2_us)

    # 2. Add CNOT depolarizing gate infidelity
    if cnot_err > 0.0:
        err_cnot = depolarizing_error(cnot_err, 2)
        noise_model.add_all_qubit_quantum_error(err_cnot, ["cx", "cz"])

    # 3. Add Readout error
    if readout_err > 0.0:
        ro_matrix = [
            [1.0 - readout_err * 0.5, readout_err * 0.5],
            [readout_err, 1.0 - readout_err],
        ]
        noise_model.add_all_qubit_readout_error(ReadoutError(ro_matrix))

    return noise_model
