"""Quantum Image Processing (QIP) Framework - Unified Master Entry Point.

Usage:
    python main.py --demo                      # Run end-to-end demo (FRQI + NEQR + Noise + Metrics)
    python main.py --demo --resolution 8       # Run demo on 8x8 image
    python main.py --run noise-sweep           # Execute noise sensitivity sweep
    python main.py --run bitflip-study         # Execute NEQR bit-flip sensitivity study
    python main.py --run denoise-benchmark     # Execute quantum vs classical denoise benchmark
"""

import argparse
import sys
import numpy as np

from qiskit import transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from src.encoding.frqi import FRQIEncoder
from src.encoding.neqr import NEQREncoder
from src.noise.channels import build_depolarizing_model, build_composite_nisq_model
from src.metrics.image_metrics import compute_all_image_metrics
from src.metrics.quantum_metrics import extract_circuit_complexity
from src.classical_denoising.standard_filters import (
    apply_mean_filter,
    apply_median_filter,
    apply_gaussian_filter,
)


def generate_pattern(pattern_name: str, size: int) -> np.ndarray:
    """Generate synthetic 2D test patterns scaled to [0, 1]."""
    if pattern_name == "checkerboard":
        coords = np.indices((size, size))
        pattern = ((coords[0] + coords[1]) % 2).astype(np.float64)
        return pattern
    elif pattern_name == "gradient":
        x = np.linspace(0.0, 1.0, size)
        y = np.linspace(0.0, 1.0, size)
        xx, yy = np.meshgrid(x, y)
        return (xx + yy) / 2.0
    elif pattern_name == "shepp_logan":
        # Simplified synthetic phantom target
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
    else:
        # Default smooth ramp
        return np.linspace(0.0, 1.0, size * size).reshape((size, size))


def run_demo(resolution: int = 4, pattern: str = "checkerboard", noise_rate: float = 0.01):
    """Execute end-to-end demonstration across FRQI, NEQR, Noise, and Baselines."""
    print("=" * 80)
    print("  QUANTUM IMAGE ROBUSTNESS & DENOISING (QIP) - END-TO-END PIPELINE DEMO")
    print("=" * 80)

    n_coord = int(np.log2(resolution))
    if 1 << n_coord != resolution:
        raise ValueError(f"Resolution must be a power of 2 (e.g. 4, 8, 16). Got {resolution}.")

    print(f"\n[1/5] Ingesting Benchmark Image ({pattern.capitalize()}, {resolution}x{resolution})...")
    clean_img = generate_pattern(pattern, resolution)
    print(f"      Pixel Intensity Range: [{clean_img.min():.2f}, {clean_img.max():.2f}]")

    # ---------------- FRQI Pipeline ----------------
    print(f"\n[2/5] Synthesizing FRQI State Preparation Circuit...")
    frqi_enc = FRQIEncoder(n_qubits_coord=n_coord)
    qc_frqi = frqi_enc.encode(clean_img, add_measurement=False)
    frqi_stats = extract_circuit_complexity(qc_frqi)
    print(
        f"      FRQI Circuit: {frqi_stats['num_qubits']} qubits, "
        f"Depth: {frqi_stats['depth']}, Gates: {frqi_stats['total_gates']}"
    )

    # Lossless Statevector Check
    sv_frqi = Statevector.from_instruction(qc_frqi)
    recon_frqi_clean = frqi_enc.decode_statevector(sv_frqi)
    metrics_frqi_clean = compute_all_image_metrics(clean_img, recon_frqi_clean)
    print(f"      -> Ideal Reconstruction PSNR: {metrics_frqi_clean['psnr']:.2f} dB (Lossless)")

    # ---------------- NEQR Pipeline ----------------
    print(f"\n[3/5] Synthesizing NEQR State Preparation Circuit...")
    color_bits = 4 if resolution <= 4 else 8
    neqr_enc = NEQREncoder(n_qubits_coord=n_coord, color_bits=color_bits)
    qc_neqr = neqr_enc.encode(clean_img, add_measurement=False)
    neqr_stats = extract_circuit_complexity(qc_neqr)
    print(
        f"      NEQR Circuit: {neqr_stats['num_qubits']} qubits, "
        f"Depth: {neqr_stats['depth']}, Gates: {neqr_stats['total_gates']}"
    )

    sv_neqr = Statevector.from_instruction(qc_neqr)
    recon_neqr_clean = neqr_enc.decode_statevector(sv_neqr)
    metrics_neqr_clean = compute_all_image_metrics(clean_img, recon_neqr_clean)
    print(f"      -> Ideal Reconstruction PSNR: {metrics_neqr_clean['psnr']:.2f} dB (Lossless)")

    # ---------------- Noisy Quantum Execution ----------------
    print(f"\n[4/5] Simulating Quantum Hardware Noise (Depolarizing p={noise_rate})...")
    noise_model = build_depolarizing_model(p_1q=noise_rate, p_2q=noise_rate * 5.0)
    sim = AerSimulator(noise_model=noise_model)

    # FRQI Noisy Measurement
    qc_frqi_meas = frqi_enc.encode(clean_img, add_measurement=True)
    qc_frqi_trans = transpile(qc_frqi_meas, sim, optimization_level=1)
    shots = 50000
    job_frqi = sim.run(qc_frqi_trans, shots=shots)
    counts_frqi = job_frqi.result().get_counts()
    recon_frqi_noisy = frqi_enc.decode(counts_frqi, shots=shots)
    metrics_frqi_noisy = compute_all_image_metrics(clean_img, recon_frqi_noisy)

    # NEQR Noisy Measurement
    qc_neqr_meas = neqr_enc.encode(clean_img, add_measurement=True)
    qc_neqr_trans = transpile(qc_neqr_meas, sim, optimization_level=1)
    job_neqr = sim.run(qc_neqr_trans, shots=shots)
    counts_neqr = job_neqr.result().get_counts()
    recon_neqr_noisy = neqr_enc.decode(counts_neqr, normalize=True)
    metrics_neqr_noisy = compute_all_image_metrics(clean_img, recon_neqr_noisy)

    # ---------------- Phase 2: Quantum & Classical Denoising Baselines ----------------
    print(f"\n[5/5] Benchmarking Quantum Denoising (QHWT) vs Classical Baselines...")
    from src.quantum_denoising.qhwt import QuantumHaarFilter
    from src.quantum_denoising.spatial_adder import QuantumSpatialFilter
    from src.classical_denoising.bm3d_wrapper import apply_bm3d_filter

    # Quantum Filtering
    qhwt_filter = QuantumHaarFilter(n_qubits_coord=n_coord, threshold=0.25)
    denoised_qhwt = qhwt_filter.denoise_image(recon_frqi_noisy)
    metrics_qhwt = compute_all_image_metrics(clean_img, denoised_qhwt)

    spatial_filter = QuantumSpatialFilter(n_qubits_coord=n_coord, color_bits=color_bits)
    denoised_spatial = spatial_filter.denoise_image(recon_neqr_noisy)
    metrics_spatial = compute_all_image_metrics(clean_img, denoised_spatial)

    # Classical Filtering
    filtered_mean = apply_mean_filter(recon_frqi_noisy, kernel_size=3)
    filtered_med = apply_median_filter(recon_frqi_noisy, kernel_size=3)
    filtered_gauss = apply_gaussian_filter(recon_frqi_noisy, kernel_size=3, sigma=0.8)
    filtered_bm3d = apply_bm3d_filter(recon_frqi_noisy, sigma_psd=0.08)

    metrics_mean = compute_all_image_metrics(clean_img, filtered_mean)
    metrics_med = compute_all_image_metrics(clean_img, filtered_med)
    metrics_gauss = compute_all_image_metrics(clean_img, filtered_gauss)
    metrics_bm3d = compute_all_image_metrics(clean_img, filtered_bm3d)

    # ---------------- Summary Results Table ----------------
    print("\n" + "=" * 80)
    print("                 PHASE 2 - COMPREHENSIVE BENCHMARK RESULTS")
    print("=" * 80)
    header = f"{'Pipeline / Representation':<34} | {'PSNR (dB)':<10} | {'SSIM':<8} | {'MSE':<10}"
    print(header)
    print("-" * 80)

    rows = [
        ("FRQI Ideal (Noiseless)", metrics_frqi_clean["psnr"], metrics_frqi_clean["ssim"], metrics_frqi_clean["mse"]),
        ("NEQR Ideal (Noiseless)", metrics_neqr_clean["psnr"], metrics_neqr_clean["ssim"], metrics_neqr_clean["mse"]),
        (f"FRQI Noisy Input (p={noise_rate})", metrics_frqi_noisy["psnr"], metrics_frqi_noisy["ssim"], metrics_frqi_noisy["mse"]),
        (f"NEQR Noisy Input (p={noise_rate})", metrics_neqr_noisy["psnr"], metrics_neqr_noisy["ssim"], metrics_neqr_noisy["mse"]),
        ("-" * 34, 0.0, 0.0, 0.0),
        ("Quantum Denoised: QHWT", metrics_qhwt["psnr"], metrics_qhwt["ssim"], metrics_qhwt["mse"]),
        ("Quantum Denoised: Spatial Adder", metrics_spatial["psnr"], metrics_spatial["ssim"], metrics_spatial["mse"]),
        ("Classical Baseline: Median", metrics_med["psnr"], metrics_med["ssim"], metrics_med["mse"]),
        ("Classical Baseline: BM3D Filter", metrics_bm3d["psnr"], metrics_bm3d["ssim"], metrics_bm3d["mse"]),
        ("Classical Baseline: Mean Box", metrics_mean["psnr"], metrics_mean["ssim"], metrics_mean["mse"]),
        ("Classical Baseline: Gaussian", metrics_gauss["psnr"], metrics_gauss["ssim"], metrics_gauss["mse"]),
    ]

    for name, psnr_val, ssim_val, mse_val in rows:
        if name.startswith("-"):
            print("-" * 80)
            continue
        psnr_str = f"{psnr_val:.2f}" if psnr_val < 200 else "> 100"
        print(f"{name:<34} | {psnr_str:<10} | {ssim_val:<8.4f} | {mse_val:<10.6f}")

    print("=" * 80)
    print("Phase 2 quantum vs. classical benchmark completed successfully!\n")


def main():
    parser = argparse.ArgumentParser(
        description="Quantum Image Robustness & Denoising Framework Master Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run quick end-to-end demonstration on a test pattern.",
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=4,
        choices=[2, 4, 8],
        help="Test image resolution (default: 4 for 4x4).",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="checkerboard",
        choices=["checkerboard", "gradient", "shepp_logan"],
        help="Test image pattern (default: checkerboard).",
    )
    parser.add_argument(
        "--noise-rate",
        type=float,
        default=0.005,
        help="Physical depolarizing noise error rate (default: 0.005).",
    )
    parser.add_argument(
        "--run",
        type=str,
        choices=["noise-sweep", "bitflip-study", "denoise-benchmark"],
        help="Launch an individual empirical experiment suite.",
    )

    args = parser.parse_args()

    if args.demo or len(sys.argv) == 1:
        run_demo(
            resolution=args.resolution,
            pattern=args.pattern,
            noise_rate=args.noise_rate,
        )
    elif args.run == "noise-sweep":
        from src.experiments.run_noise_sweep import main as sweep_main
        sweep_main()
    elif args.run == "bitflip-study":
        from src.experiments.run_bitflip_study import main as bitflip_main
        bitflip_main()
    elif args.run == "denoise-benchmark":
        from src.experiments.run_denoising_benchmark import main as denoise_main
        denoise_main()


if __name__ == "__main__":
    main()
