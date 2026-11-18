"""Master runner for EXP-01 (Depolarizing Sweep) and EXP-02 (T1/T2 Relaxation).

Executes systematic noise sensitivity sweeps across FRQI and NEQR representations,
evaluates image reconstruction quality (PSNR, SSIM, MSE), computes quantum state
fidelity, estimates critical error threshold p_crit, and outputs structured JSON.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import argparse
import datetime
import json
import math
from pathlib import Path
import yaml
import numpy as np

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector, DensityMatrix
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel

from src.encoding.frqi import FRQIEncoder
from src.encoding.neqr import NEQREncoder
from src.noise.channels import (
    build_depolarizing_model,
    build_thermal_relaxation_model,
)
from src.metrics.image_metrics import compute_all_image_metrics, compute_psnr, compute_mse
from src.metrics.quantum_metrics import compute_state_fidelity, extract_circuit_complexity


def generate_pattern(pattern_name: str, size: int) -> np.ndarray:
    """Generate synthetic 2D benchmark test image normalized in [0, 1].

    Args:
        pattern_name: Pattern type ('checkerboard', 'gradient', 'shepp_logan', 'point_impulse').
        size: Width and height of square image (must be a power of 2).

    Returns:
        np.ndarray: 2D numpy array with shape (size, size) in [0, 1].
    """
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
        # Default ramp
        return np.linspace(0.0, 1.0, size * size).reshape((size, size))


def simulate_classical_depolarizing_noise(
    image: np.ndarray, p: float, rng: Optional[np.random.Generator] = None
) -> np.ndarray:
    """Simulate equivalent classical depolarizing corruption for baseline comparison.

    With probability p, each pixel is replaced with a uniformly distributed random intensity.
    """
    if rng is None:
        rng = np.random.default_rng(42)
    noisy = image.copy()
    mask = rng.random(image.shape) < p
    noisy[mask] = rng.random(np.sum(mask))
    return np.clip(noisy, 0.0, 1.0)


def sanitize_metric(val: Any) -> Any:
    """Ensure metric values are strictly JSON compliant (no inf or nan)."""
    if val is None:
        return None
    if isinstance(val, (float, np.floating)):
        if math.isinf(val):
            return 100.0 if val > 0 else -100.0
        if math.isnan(val):
            return None
        return float(val)
    return val


def find_log_crossover(
    x_vals: List[float], y_vals: List[float], threshold: float, crossing_direction: str = "down"
) -> Optional[float]:
    """Find interpolated crossover point x_crit where y(x) crosses threshold.

    Interpolates in log10(x) space with inf/nan safety clamping.
    """
    if len(x_vals) < 2:
        return None

    # Sanitize y values to finite numbers
    y_clean = [
        100.0 if math.isinf(y) and y > 0 else (-100.0 if math.isinf(y) and y < 0 else (0.0 if math.isnan(y) else float(y)))
        for y in y_vals
    ]

    for i in range(len(x_vals) - 1):
        x1, x2 = x_vals[i], x_vals[i + 1]
        y1, y2 = y_clean[i], y_clean[i + 1]

        crosses = False
        if crossing_direction == "down" and y1 >= threshold >= y2:
            crosses = True
        elif crossing_direction == "up" and y1 <= threshold <= y2:
            crosses = True

        if crosses:
            if abs(y2 - y1) < 1e-12:
                return float(x1)
            alpha = (threshold - y1) / (y2 - y1)
            alpha = max(0.0, min(1.0, alpha))
            log_x1 = math.log10(max(1e-15, x1))
            log_x2 = math.log10(max(1e-15, x2))
            log_crit = log_x1 + alpha * (log_x2 - log_x1)
            return float(10.0**log_crit)

    # If first point already beyond threshold
    if crossing_direction == "down" and y_clean[0] < threshold:
        return float(x_vals[0])
    if crossing_direction == "up" and y_clean[0] > threshold:
        return float(x_vals[0])

    return None


def run_frqi_single_noise(
    qc_meas: QuantumCircuit,
    qc_pure: QuantumCircuit,
    encoder: FRQIEncoder,
    clean_img: np.ndarray,
    noise_model: NoiseModel,
    shots: int,
    ideal_sv: Statevector,
    compute_fidelity: bool = True,
) -> Dict[str, Any]:
    """Run FRQI measurement and density matrix fidelity calculation."""
    sim = AerSimulator(noise_model=noise_model)
    qc_trans = transpile(qc_meas, sim, optimization_level=1)
    res = sim.run(qc_trans, shots=shots).result()
    counts = res.get_counts()
    reconstructed = encoder.decode(counts, shots=shots)
    img_metrics = compute_all_image_metrics(clean_img, reconstructed)
    drift = float(np.mean(reconstructed) - np.mean(clean_img))

    fidelity = None
    if compute_fidelity and qc_pure.num_qubits <= 10:
        try:
            qc_dm = qc_pure.copy()
            qc_dm.save_density_matrix()
            sim_dm = AerSimulator(method="density_matrix", noise_model=noise_model)
            qc_dm_trans = transpile(qc_dm, sim_dm, optimization_level=1)
            res_dm = sim_dm.run(qc_dm_trans).result()
            dm = res_dm.data(0)["density_matrix"]
            fidelity = compute_state_fidelity(ideal_sv, dm)
        except Exception:
            fidelity = None

    return {
        "psnr": sanitize_metric(img_metrics["psnr"]),
        "ssim": sanitize_metric(img_metrics["ssim"]),
        "mse": sanitize_metric(img_metrics["mse"]),
        "brightness_drift": sanitize_metric(drift),
        "state_fidelity": sanitize_metric(fidelity),
    }


def run_neqr_single_noise(
    qc_meas: QuantumCircuit,
    qc_pure: QuantumCircuit,
    encoder: NEQREncoder,
    clean_img: np.ndarray,
    noise_model: NoiseModel,
    shots: int,
    ideal_sv: Statevector,
    compute_fidelity: bool = True,
) -> Dict[str, Any]:
    """Run NEQR measurement and density matrix / overlap fidelity calculation."""
    sim = AerSimulator(noise_model=noise_model)
    qc_trans = transpile(qc_meas, sim, optimization_level=1)
    res = sim.run(qc_trans, shots=shots).result()
    counts = res.get_counts()
    reconstructed = encoder.decode(counts, normalize=True)
    img_metrics = compute_all_image_metrics(clean_img, reconstructed)
    drift = float(np.mean(reconstructed) - np.mean(clean_img))

    fidelity = None
    if compute_fidelity:
        if qc_pure.num_qubits <= 10:
            try:
                qc_dm = qc_pure.copy()
                qc_dm.save_density_matrix()
                sim_dm = AerSimulator(method="density_matrix", noise_model=noise_model)
                qc_dm_trans = transpile(qc_dm, sim_dm, optimization_level=1)
                res_dm = sim_dm.run(qc_dm_trans).result()
                dm = res_dm.data(0)["density_matrix"]
                fidelity = compute_state_fidelity(ideal_sv, dm)
            except Exception:
                fidelity = None
        else:
            # For > 10 qubits, compute basis state overlap fidelity from counts
            ideal_int = encoder._prepare_image(clean_img).flatten()
            correct_shots = 0
            for bitstring, count in counts.items():
                raw = bitstring.replace(" ", "")
                c_val = int(raw[-encoder.color_bits :], 2)
                p_val = int(raw[: -encoder.color_bits], 2)
                if p_val < encoder.total_pixels and c_val == ideal_int[p_val]:
                    correct_shots += count
            fidelity = float(correct_shots / shots)

    return {
        "psnr": sanitize_metric(img_metrics["psnr"]),
        "ssim": sanitize_metric(img_metrics["ssim"]),
        "mse": sanitize_metric(img_metrics["mse"]),
        "brightness_drift": sanitize_metric(drift),
        "state_fidelity": sanitize_metric(fidelity),
    }


def run_noise_sweep(
    representation: str = "both",
    resolution: int = 4,
    pattern: str = "checkerboard",
    num_points: int = 10,
    p_min: float = 1e-4,
    p_max: float = 0.1,
    shots: int = 10000,
    output_path: str = "data/experiment_results/noise_sweep.json",
    config_path: str = "config/noise_profiles.yaml",
    color_bits: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute complete noise sweep pipeline (EXP-01 and EXP-02)."""
    n_coord = int(np.log2(resolution))
    if 1 << n_coord != resolution:
        raise ValueError(f"Resolution {resolution} must be a power of 2.")

    # Load config if available
    noise_cfg: Dict[str, Any] = {}
    cfg_file = Path(config_path)
    if cfg_file.exists():
        with open(cfg_file, "r") as f:
            noise_cfg = yaml.safe_load(f) or {}

    relaxation_profiles_cfg = noise_cfg.get("relaxation_profiles", {})

    # Generate benchmark image
    clean_img = generate_pattern(pattern, resolution)

    representations_to_run = (
        ["frqi", "neqr"] if representation == "both" else [representation.lower()]
    )

    if color_bits is None:
        color_bits = 4 if resolution <= 4 else 8

    # Pre-build circuits and ideal statevectors
    circuits: Dict[str, Dict[str, Any]] = {}
    if "frqi" in representations_to_run:
        frqi_enc = FRQIEncoder(n_qubits_coord=n_coord)
        qc_frqi_pure = frqi_enc.encode(clean_img, add_measurement=False)
        qc_frqi_meas = frqi_enc.encode(clean_img, add_measurement=True)
        sv_frqi = Statevector.from_instruction(qc_frqi_pure)
        circuits["frqi"] = {
            "encoder": frqi_enc,
            "qc_pure": qc_frqi_pure,
            "qc_meas": qc_frqi_meas,
            "ideal_sv": sv_frqi,
            "complexity": extract_circuit_complexity(qc_frqi_pure),
        }

    if "neqr" in representations_to_run:
        neqr_enc = NEQREncoder(n_qubits_coord=n_coord, color_bits=color_bits)
        qc_neqr_pure = neqr_enc.encode(clean_img, add_measurement=False)
        qc_neqr_meas = neqr_enc.encode(clean_img, add_measurement=True)
        sv_neqr = Statevector.from_instruction(qc_neqr_pure)
        circuits["neqr"] = {
            "encoder": neqr_enc,
            "qc_pure": qc_neqr_pure,
            "qc_meas": qc_neqr_meas,
            "ideal_sv": sv_neqr,
            "complexity": extract_circuit_complexity(qc_neqr_pure),
        }

    p_values = np.logspace(np.log10(p_min), np.log10(p_max), num_points).tolist()

    depolarizing_results: Dict[str, List[Dict[str, Any]]] = {
        rep: [] for rep in representations_to_run
    }
    classical_baseline_results: List[Dict[str, float]] = []

    print(
        f"[EXP-01] Sweeping depolarizing noise across {num_points} points "
        f"in [{p_min:.1e}, {p_max:.1e}] for {representations_to_run}..."
    )

    for idx, p in enumerate(p_values):
        nm_depol = build_depolarizing_model(p_1q=p, p_2q=min(1.0, 10.0 * p))

        # Classical baseline for equivalent noise rate p
        noisy_classical = simulate_classical_depolarizing_noise(clean_img, p)
        classical_metrics = compute_all_image_metrics(clean_img, noisy_classical)
        classical_baseline_results.append(
            {
                "p": float(p),
                "psnr": sanitize_metric(classical_metrics["psnr"]),
                "ssim": sanitize_metric(classical_metrics["ssim"]),
                "mse": sanitize_metric(classical_metrics["mse"]),
            }
        )

        for rep in representations_to_run:
            c_info = circuits[rep]
            if rep == "frqi":
                res_point = run_frqi_single_noise(
                    c_info["qc_meas"],
                    c_info["qc_pure"],
                    c_info["encoder"],
                    clean_img,
                    nm_depol,
                    shots,
                    c_info["ideal_sv"],
                )
            else:
                res_point = run_neqr_single_noise(
                    c_info["qc_meas"],
                    c_info["qc_pure"],
                    c_info["encoder"],
                    clean_img,
                    nm_depol,
                    shots,
                    c_info["ideal_sv"],
                )

            res_point["p"] = float(p)
            res_point["classical_baseline_psnr"] = sanitize_metric(classical_metrics["psnr"])
            depolarizing_results[rep].append(res_point)

        print(
            f"  Point {idx + 1}/{num_points}: p={p:.2e} | "
            + " | ".join(
                f"{r.upper()} PSNR: {depolarizing_results[r][-1]['psnr']:.2f} dB, "
                f"Fid: {depolarizing_results[r][-1]['state_fidelity'] if depolarizing_results[r][-1]['state_fidelity'] is not None else 0.0:.3f}"
                for r in representations_to_run
            )
            + f" | Classical PSNR: {classical_metrics['psnr']:.2f} dB"
        )

    # EXP-02: Thermal relaxation sweep & profile evaluations
    print("\n[EXP-02] Evaluating T1/T2 thermal relaxation profiles and coherence sweep...")
    relaxation_results: Dict[str, Any] = {"profiles": {}, "t1_sweep": []}

    # 1. Configured hardware relaxation profiles
    for prof_name, params in relaxation_profiles_cfg.items():
        t1 = float(params.get("t1_us", 100.0))
        t2 = float(params.get("t2_us", 80.0))
        gt1 = float(params.get("gate_time_single_ns", 35.0))
        gt2 = float(params.get("gate_time_two_ns", 250.0))

        nm_relax = build_thermal_relaxation_model(
            t1_us=t1, t2_us=t2, gate_time_1q_ns=gt1, gate_time_2q_ns=gt2
        )

        prof_entry: Dict[str, Any] = {
            "t1_us": t1,
            "t2_us": t2,
            "gate_time_single_ns": gt1,
            "gate_time_two_ns": gt2,
        }

        for rep in representations_to_run:
            c_info = circuits[rep]
            if rep == "frqi":
                prof_entry[rep] = run_frqi_single_noise(
                    c_info["qc_meas"],
                    c_info["qc_pure"],
                    c_info["encoder"],
                    clean_img,
                    nm_relax,
                    shots,
                    c_info["ideal_sv"],
                )
            else:
                prof_entry[rep] = run_neqr_single_noise(
                    c_info["qc_meas"],
                    c_info["qc_pure"],
                    c_info["encoder"],
                    clean_img,
                    nm_relax,
                    shots,
                    c_info["ideal_sv"],
                )

        relaxation_results["profiles"][prof_name] = prof_entry

    # 2. Parametric T1 sweep: T1 in [10, 200] us, T2 = 0.8 * T1
    t1_values = np.linspace(15.0, 150.0, max(3, min(5, num_points))).tolist()
    for t1 in t1_values:
        t2 = 0.8 * t1
        nm_t1 = build_thermal_relaxation_model(t1_us=t1, t2_us=t2)
        sweep_entry: Dict[str, Any] = {"t1_us": float(t1), "t2_us": float(t2)}

        for rep in representations_to_run:
            c_info = circuits[rep]
            if rep == "frqi":
                sweep_entry[rep] = run_frqi_single_noise(
                    c_info["qc_meas"],
                    c_info["qc_pure"],
                    c_info["encoder"],
                    clean_img,
                    nm_t1,
                    shots,
                    c_info["ideal_sv"],
                )
            else:
                sweep_entry[rep] = run_neqr_single_noise(
                    c_info["qc_meas"],
                    c_info["qc_pure"],
                    c_info["encoder"],
                    clean_img,
                    nm_t1,
                    shots,
                    c_info["ideal_sv"],
                )

        relaxation_results["t1_sweep"].append(sweep_entry)

    # Crossover point p_crit analysis
    crossover_analysis: Dict[str, Any] = {}
    for rep in representations_to_run:
        psnr_list = [pt["psnr"] for pt in depolarizing_results[rep]]
        classical_psnr_list = [pt["classical_baseline_psnr"] for pt in depolarizing_results[rep]]

        # p_crit for 10 dB threshold
        p_crit_10db = sanitize_metric(
            find_log_crossover(p_values, psnr_list, threshold=10.0, crossing_direction="down")
        )

        # p_crit where quantum PSNR drops below classical baseline PSNR
        delta_psnr = [
            (q if q is not None else 0.0) - (c if c is not None else 0.0)
            for q, c in zip(psnr_list, classical_psnr_list)
        ]
        p_crit_classical = sanitize_metric(
            find_log_crossover(p_values, delta_psnr, threshold=0.0, crossing_direction="down")
        )

        crossover_analysis[rep] = {
            "p_crit_10db": p_crit_10db,
            "p_crit_classical": p_crit_classical,
            "min_psnr": sanitize_metric(min(psnr_list)),
            "max_psnr": sanitize_metric(max(psnr_list)),
        }

    # Structured JSON output
    out_data = {
        "experiment": "EXP-01_EXP-02_noise_sweep",
        "metadata": {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "resolution": resolution,
            "pattern": pattern,
            "shots": shots,
            "num_points": num_points,
            "p_min": p_min,
            "p_max": p_max,
            "color_bits": color_bits if "neqr" in representations_to_run else None,
            "representations": representations_to_run,
            "circuit_complexities": {
                rep: circuits[rep]["complexity"] for rep in representations_to_run
            },
        },
        "crossover_analysis": crossover_analysis,
        "depolarizing_sweep": {
            "p_values": p_values,
            "representations": depolarizing_results,
            "classical_baseline": classical_baseline_results,
        },
        "thermal_relaxation_sweep": relaxation_results,
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(out_data, f, indent=2)

    print(f"\n[DONE] Saved noise sweep results to: {out_file.resolve()}")
    print("Crossover Analysis Summary:")
    for rep, cross in crossover_analysis.items():
        p_10 = (
            f"{cross['p_crit_10db']:.4e}"
            if cross["p_crit_10db"] is not None
            else "Not crossed in range"
        )
        p_class = (
            f"{cross['p_crit_classical']:.4e}"
            if cross["p_crit_classical"] is not None
            else "Not crossed in range"
        )
        print(f"  [{rep.upper()}] p_crit (10 dB threshold): {p_10}")
        print(f"  [{rep.upper()}] p_crit (Classical crossover): {p_class}")

    return out_data


def main():
    parser = argparse.ArgumentParser(
        description="Run noise sensitivity sweeps for FRQI and NEQR (EXP-01 & EXP-02)."
    )
    parser.add_argument(
        "--representation",
        choices=["frqi", "neqr", "both"],
        default="both",
        help="Quantum image representation to benchmark (default: both).",
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=4,
        help="Image resolution NxN (default: 4).",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="checkerboard",
        help="Synthetic image pattern: checkerboard, gradient, shepp_logan, point_impulse (default: checkerboard).",
    )
    parser.add_argument(
        "--num-points",
        type=int,
        default=10,
        help="Number of log-spaced noise sweep points (default: 10).",
    )
    parser.add_argument(
        "--p-min",
        type=float,
        default=1e-4,
        help="Minimum depolarizing error rate (default: 1e-4).",
    )
    parser.add_argument(
        "--p-max",
        type=float,
        default=0.1,
        help="Maximum depolarizing error rate (default: 0.1).",
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
        default="data/experiment_results/noise_sweep.json",
        help="Output JSON path (default: data/experiment_results/noise_sweep.json).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/noise_profiles.yaml",
        help="Path to noise profile YAML (default: config/noise_profiles.yaml).",
    )
    parser.add_argument(
        "--color-bits",
        type=int,
        default=None,
        help="Color bit-depth for NEQR (default: 4 for res<=4, else 8).",
    )
    args = parser.parse_args()

    run_noise_sweep(
        representation=args.representation,
        resolution=args.resolution,
        pattern=args.pattern,
        num_points=args.num_points,
        p_min=args.p_min,
        p_max=args.p_max,
        shots=args.shots,
        output_path=args.output,
        config_path=args.config,
        color_bits=args.color_bits,
    )


if __name__ == "__main__":
    main()
