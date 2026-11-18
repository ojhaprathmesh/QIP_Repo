"""Master runner for EXP-03: Bit-Flip Asymmetry Study in NEQR Color Qubits.

Injects bit-flip (Pauli-X) noise specifically into individual color qubits C_0 through C_{q-1}
of NEQR, measures empirical delta MSE per bit position k, verifies empirical scaling against
Theorem 2 (Delta MSE_k proportional to 2^{2k}), and exports structured JSON results.
"""

from typing import Any, Dict, List, Optional, Tuple
import argparse
import datetime
import json
import math
from pathlib import Path
import numpy as np

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError

from src.encoding.neqr import NEQREncoder
from src.metrics.image_metrics import compute_all_image_metrics, compute_mse, compute_psnr, compute_ssim
from src.metrics.quantum_metrics import extract_circuit_complexity


def generate_pattern(pattern_name: str, size: int) -> np.ndarray:
    """Generate synthetic 2D benchmark test image normalized in [0, 1]."""
    if pattern_name == "checkerboard":
        coords = np.indices((size, size))
        return ((coords[0] + coords[1]) % 2).astype(np.float64)
    elif pattern_name == "gradient":
        x = np.linspace(0.0, 1.0, size)
        y = np.linspace(0.0, 1.0, size)
        xx, yy = np.meshgrid(x, y)
        return (xx + yy) / 2.0
    elif pattern_name == "shepp_logan":
        grid = np.zeros((size, size), dtype=np.float64)
        center = size / 2.0
        r_outer = size * 0.4
        r_inner = size * 0.2
        for r in range(size):
            for c in range(size):
                dist = np.hypot(r - center + 0.5, c - center + 0.5)
                if dist <= r_inner:
                    grid[r, c] = 0.9
                elif dist <= r_outer:
                    grid[r, c] = 0.5
                else:
                    grid[r, c] = 0.1
        return grid
    elif pattern_name == "point_impulse":
        grid = np.zeros((size, size), dtype=np.float64)
        grid[size // 2, size // 2] = 1.0
        return grid
    else:
        return np.linspace(0.0, 1.0, size * size).reshape((size, size))


def run_bitflip_study(
    error_rate: float = 0.01,
    resolution: int = 4,
    color_bits: int = 8,
    pattern: str = "checkerboard",
    shots: int = 10000,
    output_path: str = "data/experiment_results/bitflip_study.json",
) -> Dict[str, Any]:
    """Execute Bit-Flip Asymmetry Study (EXP-03) on NEQR color qubits."""
    n_coord = int(np.log2(resolution))
    if 1 << n_coord != resolution:
        raise ValueError(f"Resolution {resolution} must be a power of 2.")

    clean_img = generate_pattern(pattern, resolution)

    encoder = NEQREncoder(n_qubits_coord=n_coord, color_bits=color_bits)
    qc = encoder.encode(clean_img, add_measurement=True)
    sim_base = AerSimulator()
    qc_trans = transpile(qc, sim_base, optimization_level=1)

    complexity = extract_circuit_complexity(qc)
    ideal_img_int = encoder._prepare_image(clean_img)
    ideal_flat_int = ideal_img_int.flatten()
    max_intensity = encoder.max_intensity

    print(
        f"[EXP-03] Running Bit-Flip Study on {color_bits} NEQR color qubits (C_0 .. C_{color_bits - 1})"
    )
    print(f"         Resolution: {resolution}x{resolution}, Error Rate p={error_rate}, Shots={shots}")

    results_by_qubit: List[Dict[str, Any]] = []
    empirical_mses: List[float] = []
    theoretical_mses: List[float] = []

    for k in range(color_bits):
        # Target qubit k in color register (qubit index k in circuit)
        nm = NoiseModel()
        ro_err = ReadoutError([[1.0 - error_rate, error_rate], [error_rate, 1.0 - error_rate]])
        nm.add_readout_error(ro_err, [k])

        sim = AerSimulator(noise_model=nm)
        res = sim.run(qc_trans, shots=shots).result()
        counts = res.get_counts()

        # 1. Compute per-shot empirical delta MSE in raw intensity units: E[(C_noisy - C_ideal)^2]
        total_shots = sum(counts.values())
        sq_err_sum = 0.0
        # For expectation decoding
        pixel_color_sums = np.zeros(encoder.total_pixels, dtype=np.float64)
        pixel_counts = np.zeros(encoder.total_pixels, dtype=np.float64)

        for bitstring, count in counts.items():
            raw = bitstring.replace(" ", "")
            color_val = int(raw[-color_bits:], 2)
            pos_val = int(raw[:-color_bits], 2)

            if pos_val < encoder.total_pixels:
                ideal_val = ideal_flat_int[pos_val]
                sq_err_sum += count * ((color_val - ideal_val) ** 2)
                pixel_color_sums[pos_val] += count * color_val
                pixel_counts[pos_val] += count

        empirical_mse_shot = float(sq_err_sum / total_shots)
        theoretical_mse = float(error_rate * (1.0 - error_rate) * (4.0**k))
        ratio_to_4k = float(empirical_mse_shot / (4.0**k))

        empirical_mses.append(empirical_mse_shot)
        theoretical_mses.append(theoretical_mse)

        # 2. Reconstructed image metrics using expectation decoding
        recon_flat_exp = np.zeros(encoder.total_pixels, dtype=np.float64)
        for i in range(encoder.total_pixels):
            if pixel_counts[i] > 0:
                recon_flat_exp[i] = pixel_color_sums[i] / pixel_counts[i]
            else:
                recon_flat_exp[i] = ideal_flat_int[i]

        recon_img_norm = (recon_flat_exp / float(max_intensity)).reshape((resolution, resolution))
        recon_metrics = compute_all_image_metrics(clean_img, recon_img_norm)

        # Also get standard discrete decoder output
        recon_discrete = encoder.decode(counts, normalize=True)
        discrete_metrics = compute_all_image_metrics(clean_img, recon_discrete)

        significance = "LSB" if k == 0 else ("MSB" if k == color_bits - 1 else f"Bit_{k}")

        qubit_result = {
            "bit_position": k,
            "qubit_name": f"C_{k}",
            "significance": significance,
            "weight": 1 << k,
            "weight_squared": 1 << (2 * k),
            "empirical_delta_mse_per_shot": empirical_mse_shot,
            "theoretical_delta_mse": theoretical_mse,
            "scaling_ratio_to_4k": ratio_to_4k,
            "normalized_shot_mse": float(empirical_mse_shot / (float(max_intensity) ** 2)),
            "reconstructed_image_mse": float(recon_metrics["mse"]),
            "reconstructed_image_psnr": float(recon_metrics["psnr"]),
            "reconstructed_image_ssim": float(recon_metrics["ssim"]),
            "discrete_decoded_psnr": float(discrete_metrics["psnr"]),
        }
        results_by_qubit.append(qubit_result)

        print(
            f"  Qubit C_{k:02d} ({significance:>3}): "
            f"Empirical MSE={empirical_mse_shot:8.3f} | "
            f"Theoretical={theoretical_mse:8.3f} | "
            f"Ratio/(4^k)={ratio_to_4k:.5f} | "
            f"PSNR={recon_metrics['psnr']:.2f} dB"
        )

    # 3. Statistical verification against Theorem 2: Delta MSE_k proportional to 2^{2k} = 4^k
    k_arr = np.array(list(range(color_bits)), dtype=np.float64)
    # Filter out potential zeros for log2
    safe_mses = np.array([max(1e-12, m) for m in empirical_mses])
    log2_mses = np.log2(safe_mses)

    # Fit line: log2(MSE) = slope * k + intercept
    slope, intercept = np.polyfit(k_arr, log2_mses, 1)

    # R^2 correlation with theoretical 4^k values
    x_4k = 4.0**k_arr
    corr = np.corrcoef(x_4k, safe_mses)[0, 1]
    r_squared = float(corr**2)

    # Verification threshold: slope near 2.0 (i.e. 2k) and high R^2
    slope_error = abs(slope - 2.0)
    is_verified = bool(r_squared >= 0.95 and slope_error < 0.35)

    theorem_summary = {
        "theorem": "Theorem 2 (NEQR Bit-Significance Variance)",
        "formula": "E[(C_noisy - C_ideal)^2] = p_X * (1 - p_X) * 2^(2k)",
        "scaling_target": "2^(2k) = 4^k",
        "log2_fitted_slope": float(slope),
        "expected_log2_slope": 2.0,
        "slope_error": float(slope_error),
        "r_squared": float(r_squared),
        "mean_ratio_to_4k": float(np.mean([q["scaling_ratio_to_4k"] for q in results_by_qubit])),
        "theoretical_constant": float(error_rate * (1.0 - error_rate)),
        "empirical_verification": "PASS" if is_verified else "FAIL",
    }

    out_data = {
        "experiment": "EXP-03_bitflip_study",
        "metadata": {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "resolution": resolution,
            "pattern": pattern,
            "error_rate": error_rate,
            "color_bits": color_bits,
            "shots": shots,
            "circuit_complexity": complexity,
        },
        "theorem_2_verification": theorem_summary,
        "results_by_qubit": results_by_qubit,
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(out_data, f, indent=2)

    print(f"\n[DONE] Saved bitflip study results to: {out_file.resolve()}")
    print(
        f"Theorem 2 Empirical Verification: {theorem_summary['empirical_verification']} "
        f"(Slope={slope:.4f}/2.0, R^2={r_squared:.6f})"
    )

    return out_data


def main():
    parser = argparse.ArgumentParser(
        description="Run bit-flip sensitivity analysis across NEQR color qubits C0-C(q-1) (EXP-03)."
    )
    parser.add_argument(
        "--error-rate",
        type=float,
        default=0.01,
        help="Target bit-flip error probability p_X (default: 0.01).",
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=4,
        help="Image resolution NxN (default: 4).",
    )
    parser.add_argument(
        "--color-bits",
        type=int,
        default=8,
        help="Color bit depth for NEQR color register (default: 8).",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="checkerboard",
        help="Synthetic image pattern: checkerboard, gradient, shepp_logan, point_impulse (default: checkerboard).",
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=10000,
        help="Number of measurement shots (default: 10000).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/experiment_results/bitflip_study.json",
        help="Output JSON path (default: data/experiment_results/bitflip_study.json).",
    )
    args = parser.parse_args()

    run_bitflip_study(
        error_rate=args.error_rate,
        resolution=args.resolution,
        color_bits=args.color_bits,
        pattern=args.pattern,
        shots=args.shots,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
