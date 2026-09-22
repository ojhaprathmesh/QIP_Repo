"""Master runner for EXP-01 (Depolarizing Sweep) and EXP-02 (T1/T2 Relaxation)."""

import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Run noise sensitivity sweeps for FRQI and NEQR."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/noise_profiles.yaml",
        help="Path to noise profile YAML.",
    )
    parser.add_argument(
        "--representation",
        choices=["frqi", "neqr", "both"],
        default="both",
        help="Quantum image representation to benchmark.",
    )
    args = parser.parse_args()
    print(
        f"Initializing Noise Sweep experiment for representation: {args.representation}"
    )
    print("Pending Phase 3 empirical implementation.")


if __name__ == "__main__":
    main()
