"""Measurement readout confusion matrix models."""

from qiskit_aer.noise import NoiseModel, ReadoutError


def build_readout_error_model(
    p_0_given_1: float = 0.03, p_1_given_0: float = 0.01
) -> NoiseModel:
    """Build a measurement assignment readout error model.

    Probabilities matrix Lambda:
    Lambda[0][0] = P(measure 0 | true 0) = 1 - p_1_given_0
    Lambda[0][1] = P(measure 1 | true 0) = p_1_given_0
    Lambda[1][0] = P(measure 0 | true 1) = p_0_given_1
    Lambda[1][1] = P(measure 1 | true 1) = 1 - p_0_given_1

    Args:
        p_0_given_1: Probability of measuring |0> when true state is |1>.
        p_1_given_0: Probability of measuring |1> when true state is |0>.

    Returns:
        NoiseModel: Noise model containing readout errors for projective measurement.
    """
    matrix = [
        [1.0 - p_1_given_0, p_1_given_0],
        [p_0_given_1, 1.0 - p_0_given_1],
    ]
    readout_error = ReadoutError(matrix)

    noise_model = NoiseModel()
    noise_model.add_all_qubit_readout_error(readout_error)
    return noise_model
