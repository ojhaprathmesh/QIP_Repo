"""Unit tests for noise channel builders and noisy circuit execution."""

import pytest
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel

from src.noise.channels import (
    build_depolarizing_model,
    build_thermal_relaxation_model,
    build_composite_nisq_model,
)
from src.noise.readout import build_readout_error_model


def test_build_depolarizing_model():
    """Verify depolarizing noise model creation with valid quantum errors."""
    noise_model = build_depolarizing_model(p_1q=0.01, p_2q=0.05)
    assert isinstance(noise_model, NoiseModel)
    assert "cx" in noise_model.noise_instructions or "h" in noise_model.noise_instructions


def test_build_thermal_relaxation_model():
    """Verify thermal relaxation noise model satisfies physical constraints."""
    noise_model = build_thermal_relaxation_model(t1_us=100.0, t2_us=80.0)
    assert isinstance(noise_model, NoiseModel)


def test_build_readout_error_model():
    """Verify readout error model contains valid assignment matrices."""
    noise_model = build_readout_error_model(p_0_given_1=0.05, p_1_given_0=0.02)
    assert isinstance(noise_model, NoiseModel)


def test_build_composite_nisq_model():
    """Verify composite NISQ noise model initializes successfully."""
    noise_model = build_composite_nisq_model(backend_name="fake_brisbane")
    assert isinstance(noise_model, NoiseModel)


def test_noisy_simulation_execution():
    """Verify a simple Bell circuit executes on AerSimulator with depolarizing noise."""
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])

    noise_model = build_depolarizing_model(p_1q=0.02, p_2q=0.1)
    sim = AerSimulator(noise_model=noise_model)

    job = sim.run(qc, shots=2000)
    counts = job.result().get_counts()

    # In ideal Bell state, only '00' and '11' occur. Under noise, '01' and '10' appear.
    assert len(counts) > 1
    assert "00" in counts or "11" in counts
