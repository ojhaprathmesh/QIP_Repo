"""Quantum Noise Channel Builders and Simulation Models.

Provides utilities for constructing Qiskit Aer NoiseModel instances
for depolarizing, amplitude damping (T1), dephasing (T2), and readout errors.
"""

from .channels import (
    build_depolarizing_model,
    build_thermal_relaxation_model,
    build_composite_nisq_model,
)
from .readout import build_readout_error_model

__all__ = [
    "build_depolarizing_model",
    "build_thermal_relaxation_model",
    "build_composite_nisq_model",
    "build_readout_error_model",
]
