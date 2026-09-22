"""Measurement readout confusion matrix models."""

from typing import Tuple


def build_readout_error_model(p_0_given_1: float = 0.03, p_1_given_0: float = 0.01):
    """Build a measurement assignment readout error model.

    Args:
        p_0_given_1: Probability of measuring |0> when true state is |1>.
        p_1_given_0: Probability of measuring |1> when true state is |0>.

    Returns:
        NoiseModel: Noise model containing readout errors for projective measurement.
    """
    raise NotImplementedError("Phase 1 implementation pending.")
