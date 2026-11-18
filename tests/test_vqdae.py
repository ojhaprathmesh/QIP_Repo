"""Unit tests for Variational Quantum Denoising Autoencoder (VQDAE)."""

import pytest
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, DensityMatrix

from src.quantum_denoising.vqdae import VariationalQuantumDenoisingAutoencoder
from src.metrics.quantum_metrics import compute_state_fidelity


def test_vqdae_initialization():
    """Verify VQDAE initialization parameter shapes and invalid input exceptions."""
    vqdae = VariationalQuantumDenoisingAutoencoder(n_qubits=3, n_layers=4, seed=42)
    assert vqdae.n_qubits == 3
    assert vqdae.n_layers == 4
    assert vqdae.dim == 8
    assert vqdae.param_shape == (4, 3, 2)
    assert vqdae.n_params == 24
    assert vqdae.params.shape == (4, 3, 2)

    # Bottleneck initialization
    vqdae_bn = VariationalQuantumDenoisingAutoencoder(n_qubits=4, n_layers=4, bottleneck_qubits=2)
    assert vqdae_bn.bottleneck_qubits == 2
    assert vqdae_bn.n_enc_layers == 2
    assert vqdae_bn.n_dec_layers == 2

    # Exceptions on invalid inputs
    with pytest.raises(ValueError, match="n_qubits must be >= 1"):
        VariationalQuantumDenoisingAutoencoder(n_qubits=0)

    with pytest.raises(ValueError, match="n_layers must be >= 1"):
        VariationalQuantumDenoisingAutoencoder(n_qubits=2, n_layers=0)

    with pytest.raises(ValueError, match="bottleneck_qubits must be between 1 and n_qubits"):
        VariationalQuantumDenoisingAutoencoder(n_qubits=2, bottleneck_qubits=3)

    with pytest.raises(ValueError, match="bottleneck_qubits must be between 1 and n_qubits"):
        VariationalQuantumDenoisingAutoencoder(n_qubits=2, bottleneck_qubits=0)


def test_vqdae_qiskit_ansatz_building():
    """Verify Qiskit circuit building with numeric and symbolic parameters."""
    vqdae = VariationalQuantumDenoisingAutoencoder(n_qubits=3, n_layers=2)

    # Bound numeric circuit
    qc = vqdae.build_qiskit_circuit()
    assert isinstance(qc, QuantumCircuit)
    assert qc.num_qubits == 3
    ops = dict(qc.count_ops())
    # 2 layers * 3 qubits * 1 ry = 6 ry, 6 rz
    assert ops.get("ry") == 6
    assert ops.get("rz") == 6
    # 2 layers * 3 CNOTs (circular) = 6 cx
    assert ops.get("cx") == 6

    # Parameterized symbolic circuit
    qc_sym = vqdae.build_qiskit_circuit(parameterized=True)
    assert qc_sym.num_parameters == vqdae.n_params
    assert "theta" in [p.name.split("[")[0] for p in qc_sym.parameters]

    # Circuit with bottleneck includes reset operations
    vqdae_bn = VariationalQuantumDenoisingAutoencoder(n_qubits=3, n_layers=2, bottleneck_qubits=2)
    qc_bn = vqdae_bn.build_qiskit_circuit()
    ops_bn = dict(qc_bn.count_ops())
    assert ops_bn.get("reset") == 1  # 1 trash qubit (qubit 2) reset


def test_vqdae_pennylane_ansatz_building():
    """Verify PennyLane QNode creation and statevector evaluation."""
    vqdae = VariationalQuantumDenoisingAutoencoder(n_qubits=2, n_layers=2)
    qnode = vqdae.build_pennylane_circuit()

    # Default initial state (|00>)
    out_state = qnode()
    assert out_state.shape == (4,)
    assert np.isclose(np.linalg.norm(out_state), 1.0)

    # Custom initial state
    init_state = np.array([0.0, 1.0, 0.0, 0.0], dtype=complex)
    out_custom = qnode(initial_state=init_state)
    assert out_custom.shape == (4,)
    assert np.isclose(np.linalg.norm(out_custom), 1.0)


def test_vqdae_build_ansatz_framework_dispatch():
    """Verify build_ansatz dispatches to appropriate framework."""
    vqdae = VariationalQuantumDenoisingAutoencoder(n_qubits=2, n_layers=2, backend="qiskit")
    qc = vqdae.build_ansatz()
    assert isinstance(qc, QuantumCircuit)

    vqdae_pl = VariationalQuantumDenoisingAutoencoder(n_qubits=2, n_layers=2, backend="pennylane")
    pl_circuit = vqdae_pl.build_ansatz()
    assert callable(pl_circuit)

    # Explicit override
    qc_explicit = vqdae_pl.build_ansatz(framework="qiskit")
    assert isinstance(qc_explicit, QuantumCircuit)

    with pytest.raises(ValueError, match="Unsupported framework"):
        vqdae.build_ansatz(framework="cirq")


def test_vqdae_parameter_dimension_matching():
    """Verify parameter formatting, 1D and 3D reshaping, and dimension validation."""
    vqdae = VariationalQuantumDenoisingAutoencoder(n_qubits=2, n_layers=3)
    assert vqdae.n_params == 12

    # 1D array matching
    flat_params = np.linspace(0.1, 1.2, 12)
    reshaped = vqdae._validate_and_format_params(flat_params)
    assert reshaped.shape == (3, 2, 2)
    assert np.allclose(reshaped.flatten(), flat_params)

    # 3D array matching
    arr_3d = np.ones((3, 2, 2), dtype=np.float64) * 0.5
    validated_3d = vqdae._validate_and_format_params(arr_3d)
    assert validated_3d.shape == (3, 2, 2)

    # Dimension mismatch error
    with pytest.raises(ValueError, match="Parameter size mismatch"):
        vqdae._validate_and_format_params(np.zeros(10))


def test_vqdae_surrogate_unitary_and_consistency():
    """Verify classical-quantum surrogate preserves norm and matches Qiskit/PennyLane execution."""
    vqdae = VariationalQuantumDenoisingAutoencoder(n_qubits=2, n_layers=2, seed=123)
    psi_in = np.array([0.5, 0.5, 0.5, 0.5], dtype=complex)

    # Surrogate evaluation
    out_surrogate = vqdae.classical_quantum_surrogate(psi_in)
    assert out_surrogate.shape == (4,)
    assert np.isclose(np.linalg.norm(out_surrogate), 1.0)

    # PennyLane evaluation
    qnode = vqdae.build_pennylane_circuit()
    out_pl = qnode(initial_state=psi_in)
    # Both evaluate the same circuit operations in wire order 0, 1
    assert np.allclose(out_surrogate, out_pl, atol=1e-6)


def test_vqdae_optimization_loss_reduction_adam():
    """Verify that fit with Adam optimizer strictly reduces state fidelity loss."""
    np.random.seed(42)
    vqdae = VariationalQuantumDenoisingAutoencoder(n_qubits=2, n_layers=2, seed=42)

    # Target clean state
    clean_state = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)

    # Corrupted noisy state
    noisy_state = np.array([0.7, 0.4, 0.4, 0.43588989], dtype=complex)
    noisy_state /= np.linalg.norm(noisy_state)

    initial_fidelity = compute_state_fidelity(clean_state, vqdae.denoise(noisy_state))
    initial_loss = 1.0 - initial_fidelity

    # Run Adam optimization
    history = vqdae.fit(noisy_state, clean_state, epochs=30, lr=0.1, optimizer="adam")

    assert "loss" in history
    assert len(history["loss"]) >= 30
    final_loss = history["loss"][-1]

    # Verify significant loss reduction
    assert final_loss < initial_loss
    assert final_loss < 0.1, f"Expected final loss < 0.1, got {final_loss}"

    # Verify post-training fidelity increased
    denoised_state = vqdae.denoise(noisy_state)
    final_fidelity = compute_state_fidelity(clean_state, denoised_state)
    assert final_fidelity > initial_fidelity
    assert final_fidelity > 0.90


def test_vqdae_optimization_loss_reduction_cobyla():
    """Verify that fit with COBYLA optimizer reduces state fidelity loss."""
    vqdae = VariationalQuantumDenoisingAutoencoder(n_qubits=2, n_layers=2, seed=10)

    clean_state = np.array([0.0, 1.0, 0.0, 0.0], dtype=complex)
    noisy_state = np.array([0.6, 0.6, 0.3, 0.360555], dtype=complex)
    noisy_state /= np.linalg.norm(noisy_state)

    initial_loss = 1.0 - compute_state_fidelity(clean_state, vqdae.denoise(noisy_state))

    history = vqdae.fit(noisy_state, clean_state, epochs=25, optimizer="cobyla")

    assert len(history["loss"]) > 0
    final_loss = history["loss"][-1]
    assert final_loss < initial_loss


def test_vqdae_bottleneck_compression_and_recovery():
    """Verify VQDAE execution with bottleneck latent compression subspace."""
    # 3 qubits compressed to 2 bottleneck qubits
    vqdae_bn = VariationalQuantumDenoisingAutoencoder(
        n_qubits=3,
        n_layers=2,
        bottleneck_qubits=2,
        seed=42,
    )

    clean_state = np.zeros(8, dtype=complex)
    clean_state[0] = 1.0

    noisy_state = np.random.randn(8) + 1j * np.random.randn(8)
    noisy_state /= np.linalg.norm(noisy_state)

    history = vqdae_bn.fit(noisy_state, clean_state, epochs=20, lr=0.1, optimizer="adam")
    assert history["loss"][-1] < history["loss"][0]

    denoised = vqdae_bn.denoise(noisy_state)
    assert denoised.shape == (8,)
    assert np.isclose(np.linalg.norm(denoised), 1.0)


def test_vqdae_denoise_qiskit_objects():
    """Verify denoise interface handles Qiskit Statevector and DensityMatrix."""
    vqdae = VariationalQuantumDenoisingAutoencoder(n_qubits=2, n_layers=2)

    sv = Statevector([1.0, 0.0, 0.0, 0.0])
    denoised_sv = vqdae.denoise(sv)
    assert isinstance(denoised_sv, Statevector)
    assert denoised_sv.is_valid()

    dm = DensityMatrix(np.eye(4) / 4.0)
    denoised_dm = vqdae.denoise(dm)
    assert isinstance(denoised_dm, DensityMatrix)
    assert denoised_dm.is_valid()


def test_vqdae_denoise_micro_image():
    """Verify 2D micro-image denoising via amplitude encoding."""
    vqdae = VariationalQuantumDenoisingAutoencoder(n_qubits=2, n_layers=2)  # 2^2 = 4 pixels (2x2 image)

    test_image = np.array([
        [0.2, 0.8],
        [0.4, 0.6],
    ], dtype=np.float64)

    denoised_img = vqdae.denoise_image(test_image)
    assert denoised_img.shape == (2, 2)
    assert np.all(denoised_img >= 0.0)

    # Also test generic denoise() handling 2D image
    res = vqdae.denoise(test_image)
    assert res.shape == (2, 2)


def test_vqdae_batch_denoise():
    """Verify batch denoising of a list of states."""
    vqdae = VariationalQuantumDenoisingAutoencoder(n_qubits=2, n_layers=1)
    states = [
        np.array([1, 0, 0, 0], dtype=complex),
        np.array([0, 1, 0, 0], dtype=complex),
        np.array([0, 0, 1, 0], dtype=complex),
    ]

    results = vqdae.denoise(states)
    assert len(results) == 3
    for s in results:
        assert s.shape == (4,)
        assert np.isclose(np.linalg.norm(s), 1.0)
