# Quantum Image Robustness & Denoising Framework (QIP) — Quickstart & Execution Guide

Welcome to the **Quantum Image Robustness & Denoising Framework (QIP)**. This step-by-step guide will walk you through setting up your environment from scratch, verifying the installation, and running all operational components in the project's current state.

---

## 1. Prerequisites & System Requirements

Before you begin, ensure your machine meets the following prerequisites:

* **Operating System:** macOS (Apple Silicon or Intel), Linux (Ubuntu 20.04+, Debian, Fedora, Arch), or Windows 10/11 (WSL2 recommended).
* **Python:** Python `3.10`, `3.11`, `3.12`, or `3.14` (verified on Python 3.14.7).
* **Package Manager:** [`uv`](https://github.com/astral-sh/uv) (recommended for 10x-100x faster dependency resolution) or standard `pip` / `conda`.
* **Hardware Requirements:**
  * **RAM:** Minimum 8 GB RAM (16 GB recommended for full statevector and density matrix simulations).
  * **Disk Space:** ~2 GB for dependencies, Qiskit Aer wheels, and virtual environment.
* **Git:** Installed on your system (`git --version`).

---

## 2. Environment Setup (Choose One Method)

### Method A: Using `uv` (Fastest & Recommended)

`uv` is an extremely fast Python package manager written in Rust.

1. **Install `uv` (if not already installed):**
   * **macOS / Linux:**
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
     *(Or via Homebrew on macOS: `brew install uv`)*
   * **Windows:**
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```

2. **Clone the repository and enter the directory:**
   ```bash
   git clone <repository-url>
   cd QIP_Repo
   ```

3. **Create and activate the virtual environment:**
   ```bash
   uv venv
   source .venv/bin/activate
   # On Windows (cmd/PowerShell): .venv\Scripts\activate
   ```

4. **Install dependencies and project in editable mode:**
   ```bash
   uv pip install -e ".[dev]"
   ```

---

### Method B: Using Standard Python `venv` + `pip`

If you do not have `uv`, standard Python 3 virtual environment works out of the box:

1. **Clone the repository and enter the directory:**
   ```bash
   git clone <repository-url>
   cd QIP_Repo
   ```

2. **Create the virtual environment:**
   ```bash
   python3 -m venv .venv
   ```

3. **Activate the virtual environment:**
   * **macOS / Linux:**
     ```bash
     source .venv/bin/activate
     ```
   * **Windows (Command Prompt):**
     ```cmd
     .venv\Scripts\activate.bat
     ```
   * **Windows (PowerShell):**
     ```powershell
     .venv\Scripts\Activate.ps1
     ```

4. **Upgrade pip and install the framework:**
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -e ".[dev]"
   ```
   *(Alternatively: `uv sync`)*

---

### Method C: Using Conda / Mamba

If you prefer managing environments through Anaconda or Miniconda:

1. **Create environment from `environment.yml`:**
   ```bash
   conda env create -f environment.yml
   ```

2. **Activate the environment:**
   ```bash
   conda activate qip
   ```

3. **Install the package in development mode:**
   ```bash
   pip install -e .
   ```

---

## 3. Verifying the Installation

### Step 3.1: Quick Dependency Import Check
Run this single-line verification to ensure Qiskit, Qiskit Aer, OpenCV, and FastAPI load correctly:

```bash
python -c "import qiskit, qiskit_aer, cv2, fastapi, pydantic; print('All core dependencies imported successfully!')"
```

### Step 3.2: Run the Full Automated Test Suite
The repository includes a comprehensive 48-test suite covering state preparation, Kraus noise channels, denoising filters, VQDAE variational ansatz, empirical sweeps, REST benchmark endpoints, and the API streaming bridge:

```bash
uv run --no-sync pytest -v
```

**Expected Output:**
```
============================= test session starts ==============================
collected 48 items

tests/test_api.py::test_health_check PASSED                              [  2%]
tests/test_api.py::test_simulation_request_schema PASSED                 [  4%]
tests/test_api.py::test_websocket_simulate PASSED                        [  6%]
tests/test_api.py::test_benchmark_endpoints[/api/benchmarks/noise-sweep] PASSED [  8%]
tests/test_api.py::test_benchmark_endpoints[/api/benchmarks/denoising] PASSED [ 10%]
tests/test_api.py::test_benchmark_endpoints[/api/benchmarks/bitflip-study] PASSED [ 12%]
tests/test_api.py::test_benchmark_missing_file PASSED                    [ 14%]
tests/test_api.py::test_benchmark_invalid_json PASSED                    [ 16%]
tests/test_api.py::test_websocket_real_circuit_and_classical_metrics[frqi] PASSED [ 18%]
tests/test_api.py::test_websocket_real_circuit_and_classical_metrics[neqr] PASSED [ 20%]
tests/test_denoising.py::test_classical_filters_execution PASSED         [ 22%]
tests/test_denoising.py::test_qhwt_circuit_synthesis PASSED              [ 25%]
tests/test_denoising.py::test_qhwt_lossless_roundtrip PASSED             [ 27%]
tests/test_denoising.py::test_qhwt_denoising_noise_reduction PASSED      [ 29%]
tests/test_denoising.py::test_spatial_adder_filter_execution PASSED      [ 31%]
tests/test_denoising_benchmark.py::test_generate_patterns PASSED         [ 33%]
tests/test_denoising_benchmark.py::test_get_noise_model PASSED           [ 35%]
tests/test_denoising_benchmark.py::test_run_benchmark_execution PASSED   [ 37%]
tests/test_denoising_benchmark.py::test_main_cli_dispatch PASSED         [ 39%]
tests/test_encoding.py::test_frqi_initialization PASSED                  [ 41%]
tests/test_encoding.py::test_neqr_initialization PASSED                  [ 43%]
tests/test_encoding.py::test_frqi_lossless_roundtrip PASSED              [ 45%]
tests/test_encoding.py::test_neqr_lossless_roundtrip PASSED              [ 47%]
tests/test_encoding.py::test_frqi_shot_sampling_roundtrip PASSED         [ 50%]
tests/test_encoding.py::test_neqr_shot_sampling_roundtrip PASSED         [ 52%]
tests/test_metrics.py::test_perfect_reconstruction_metrics PASSED        [ 54%]
tests/test_metrics.py::test_perturbed_metrics PASSED                     [ 56%]
tests/test_noise.py::test_build_depolarizing_model PASSED                [ 58%]
tests/test_noise.py::test_build_thermal_relaxation_model PASSED          [ 60%]
tests/test_noise.py::test_build_readout_error_model PASSED               [ 62%]
tests/test_noise.py::test_build_composite_nisq_model PASSED              [ 64%]
tests/test_noise.py::test_noisy_simulation_execution PASSED              [ 66%]
tests/test_sweeps.py::test_generate_pattern PASSED                       [ 68%]
tests/test_sweeps.py::test_find_log_crossover PASSED                     [ 70%]
tests/test_sweeps.py::test_bitflip_study_smoke PASSED                    [ 72%]
tests/test_sweeps.py::test_noise_sweep_smoke PASSED                      [ 75%]
tests/test_vqdae.py::test_vqdae_initialization PASSED                    [ 77%]
tests/test_vqdae.py::test_vqdae_qiskit_ansatz_building PASSED            [ 79%]
tests/test_vqdae.py::test_vqdae_pennylane_ansatz_building PASSED         [ 81%]
tests/test_vqdae.py::test_vqdae_build_ansatz_framework_dispatch PASSED   [ 83%]
tests/test_vqdae.py::test_vqdae_parameter_dimension_matching PASSED      [ 85%]
tests/test_vqdae.py::test_vqdae_surrogate_unitary_and_consistency PASSED [ 87%]
tests/test_vqdae.py::test_vqdae_optimization_loss_reduction_adam PASSED  [ 89%]
tests/test_vqdae.py::test_vqdae_optimization_loss_reduction_cobyla PASSED [ 91%]
tests/test_vqdae.py::test_vqdae_bottleneck_compression_and_recovery PASSED [ 93%]
tests/test_vqdae.py::test_vqdae_denoise_qiskit_objects PASSED            [ 95%]
tests/test_vqdae.py::test_vqdae_denoise_micro_image PASSED               [ 97%]
tests/test_vqdae.py::test_vqdae_batch_denoise PASSED                     [100%]

======================= 48 passed, 2 warnings in 34.88s ========================
```

---

## 4. Running the Project in Its Current State

### 4.1 Running the End-to-End Pipeline CLI Demo

The master command line runner `main.py` provides an end-to-end demonstration comparing FRQI, NEQR, Qiskit Aer hardware noise injection, Quantum Denoising (QHWT and Spatial Adder), and classical baselines.

#### Default $4 \times 4$ Demo:
```bash
python main.py --demo
```

#### What Happens During Execution:
1. **[1/5] Ingesting Benchmark Image:** Generates a synthetic test pattern (default: `checkerboard`, $4 \times 4$ pixels).
2. **[2/5] Synthesizing FRQI Circuit:** Builds a 5-qubit circuit ($2n+1$) with controlled $R_y$ rotations. Confirms ideal lossless statevector reconstruction ($>100\text{ dB}$ PSNR).
3. **[3/5] Synthesizing NEQR Circuit:** Builds an 8-qubit circuit ($2n+q$) with multi-controlled $X$ gates. Confirms ideal lossless reconstruction ($>100\text{ dB}$ PSNR).
4. **[4/5] Simulating Quantum Hardware Noise:** Injects depolarizing noise ($p=0.005$) on Qiskit Aer and measures 50,000 shots.
5. **[5/5] Benchmarking Filters:** Executes:
   - **Quantum Haar Wavelet Transform (QHWT)** frequency thresholding.
   - **Quantum Spatial Moving Average Filter** (reversible quantum adder).
   - **Classical Baselines:** Median Filter, BM3D Filter, Mean Box, and Gaussian Blur.

#### Output Benchmark Scorecard:
```
================================================================================
                 PHASE 2 - COMPREHENSIVE BENCHMARK RESULTS
================================================================================
Pipeline / Representation          | PSNR (dB)  | SSIM     | MSE       
--------------------------------------------------------------------------------
FRQI Ideal (Noiseless)             | > 100      | 1.0000   | 0.000000  
NEQR Ideal (Noiseless)             | > 100      | 1.0000   | 0.000000  
FRQI Noisy Input (p=0.005)         | 6.07       | 0.0144   | 0.247104  
NEQR Noisy Input (p=0.005)         | 5.99       | 0.4128   | 0.251944  
--------------------------------------------------------------------------------
Quantum Denoised: QHWT             | 6.06       | 0.0115   | 0.247820  
Quantum Denoised: Spatial Adder    | 5.83       | -0.0104  | 0.261042  
Classical Baseline: Median         | 6.02       | 0.0031   | 0.250004  
Classical Baseline: BM3D Filter    | 5.99       | -0.0019  | 0.251482  
Classical Baseline: Mean Box       | 6.02       | 0.0045   | 0.249764  
Classical Baseline: Gaussian       | 6.02       | 0.0033   | 0.250029  
================================================================================
```

---

### 4.2 Running Custom Demonstrations

You can customize the image resolution, synthetic pattern, and physical noise rate:

#### Test on an $8 \times 8$ Image (Shepp-Logan Tomography Phantom):
```bash
python main.py --demo --resolution 8 --pattern shepp_logan --noise-rate 0.01
```

#### Test Continuous Intensity Gradient:
```bash
python main.py --demo --resolution 4 --pattern gradient --noise-rate 0.001
```

Available CLI Flags:
* `--resolution`: Spatial dimension of the square image (`4`, `8`, `16`, `32`). Default: `4`.
* `--pattern`: Test image pattern (`checkerboard`, `gradient`, `shepp_logan`). Default: `checkerboard`.
* `--noise-rate`: Physical 1-qubit depolarizing error rate $p$. Default: `0.005`.

---

### 4.3 Running the Real-Time FastAPI & WebSocket Simulation Server

Phase 3A introduces an asynchronous FastAPI microservice exposing full-duplex WebSockets for streaming simulation events directly to frontends or client scripts.

#### 1. Start the Server:
```bash
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Check the Health Endpoints (in a new terminal):
```bash
curl http://localhost:8000/api/health
# Or the cloud health check alias:
curl http://localhost:8000/healthz
```
**Expected Response:**
```json
{
  "status": "healthy",
  "simulator": "quantum_image_processing",
  "version": "1.0.0"
}
```

#### 3. Inspect Empirical Benchmark REST Endpoints:
The backend exposes tracked experiment results directly as REST APIs:
```bash
curl http://localhost:8000/api/benchmarks/noise-sweep
curl http://localhost:8000/api/benchmarks/denoising
curl http://localhost:8000/api/benchmarks/bitflip-study
```

#### 4. Test WebSocket Streaming (`/ws/simulate`):
You can test the real-time event pipeline using this quick Python script:

```python
# test_stream.py
import asyncio
import json
import websockets

async def stream():
    uri = "ws://localhost:8000/ws/simulate"
    async with websockets.connect(uri) as ws:
        payload = {
            "resolution": 4,
            "pattern": "checkerboard",
            "encoding": "frqi",
            "noise_channel": "depolarizing",
            "noise_rate": 0.01,
            "shots": 10000,
            "denoise_method": "qhwt",
            "threshold": 0.2
        }
        await ws.send(json.dumps(payload))
        print("Connected and sent simulation request. Listening for telemetry:")
        
        while True:
            msg = await ws.recv()
            event = json.loads(msg)
            print("Received Event:", event)
            if event.get("status") == "completed":
                print("Simulation stream completed successfully!")
                break

asyncio.run(stream())
```
Run it with:
```bash
python test_stream.py
```

---

### 4.4 Running the Next.js 16 Real-Time Quantum Studio (`ui/`)

The web frontend is a Next.js 16 (React 19) dashboard featuring an Obsidian Dark theme, a fixed-height 100vh layout with zero outer-window scrollbar, a full-height right-docked vertical pipeline stepper, and live Recharts sweep analytics.

> 🌐 **Live Deployed Studio:** You can also access the hosted studio directly at [https://qip.ojhaprathmesh.in](https://qip.ojhaprathmesh.in).

#### 1. Start the FastAPI Simulation Backend:
In terminal 1:
```bash
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Start the Next.js Frontend Development Server:
In terminal 2:
```bash
cd ui
npm ci
npm run dev
```

#### 3. Open in Browser:
Visit `http://localhost:3000` to interact with:
* **Interactive Vertical Stepper:** Docked on the right side of the dashboard, spanning 100% viewport height with continuous connecting state lines.
* **Dual Execution Modes:** Toggle between **Auto Flow** (continuous auto-progression) and **Manual Step** (stage-by-stage pause, advance via button or `→` / `Space`).
* **Live Ingestion Configurator:** Resize images ($4\times 4$ to $128\times 128$) with live qubit requirement recalculation ($2n+1$ vs $2n+q$) and anti-aliased downsampling kernels.
* **Real-Time Simulation Trigger:** Click **"Run Simulation"** to stream gate-level circuit compilation, statevector purity, Monte Carlo shot accumulation, and progressive raster reconstruction via WebSocket at 60 FPS.

---

### 4.5 Running Phase 4 Empirical Experiment Sweeps

You can run automated parametric sweeps and save structured JSON experiment data directly to `data/experiment_results/`:

#### 1. Depolarizing and Thermal Noise Sweeps (EXP-01 & EXP-02):
```bash
python main.py --run noise-sweep --representation both --num-points 10 --shots 10000
```
* Sweeps depolarizing noise $p \in [10^{-4}, 10^{-1}]$ in logarithmic steps.
* Simulates typical and degraded superconducting relaxation profiles ($T_1, T_2$).
* Automatically calculates crossover points $p_{\text{crit}}$ and saves to `data/experiment_results/noise_sweep.json`.

#### 2. NEQR Bit-Flip Asymmetry Study (EXP-03):
```bash
python main.py --run bitflip-study --error-rate 0.01 --resolution 4
```
* Measures bit-by-bit distortion across NEQR color qubits $C_0$ (LSB) to $C_7$ (MSB).
* Empirically validates Theorem 2 ($\Delta\text{MSE}_k \propto 2^{2k}$, $R^2 > 0.99$).
* Saves results to `data/experiment_results/bitflip_study.json`.

#### 3. Quantum vs Classical Denoising Benchmark & Breakeven Depth (EXP-04 & EXP-05):
```bash
python main.py --run denoise-benchmark --image shepp_logan --noise-rate 0.005 --shots 10000
```
* Benchmarks Quantum Haar Wavelet (QHWT) and Spatial Adder against Median, BM3D, Gaussian, and Bilateral filters.
* Evaluates breakeven noise threshold $p_{\text{breakeven}}$ and critical depth $D_{\text{crit}}$ where quantum filters collapse.
* Saves results to `data/experiment_results/denoising_benchmark.json`.

---

## 5. Repository Structure & Key Files

```
QIP_Repo/
├── api/                                # Real-Time FastAPI Streaming Bridge
│   ├── event_bus.py                   # In-process asynchronous Pub/Sub dispatcher
│   ├── schemas.py                     # Pydantic v2 schemas for simulation & telemetry
│   └── server.py                      # FastAPI app with /ws/simulate & /api/health
├── config/                            # Parameterized Configuration YAMLs
│   ├── benchmark_images.yaml          # Target image dimensions and synthetic patterns
│   ├── hardware_backends.yaml         # IBM FakeBrisbane & Aer hardware calibration
│   └── noise_profiles.yaml            # Depolarizing sweeps, T1/T2, and readout error
├── data/                              # Datasets and Output Dumps
│   ├── experiment_results/            # Measurement counts & sweep logs
│   ├── noisy_classical/               # Pre-corrupted classical benchmark images
│   └── raw_images/                    # Benchmark test images
├── src/
│   ├── classical_denoising/           # Classical Image Restoration Baselines
│   │   ├── bm3d_wrapper.py            # State-of-the-art BM3D collaborative filter
│   │   └── standard_filters.py        # Spatial Mean, Median, Gaussian, Bilateral
│   ├── encoding/                      # Quantum Image State Preparation
│   │   ├── frqi.py                    # Flexible Representation (Continuous Ry)
│   │   └── neqr.py                    # Novel Enhanced Representation (Basis MCX)
│   ├── experiments/                   # Batch Execution Sweeps (Phase 4)
│   │   ├── run_bitflip_study.py       # NEQR color qubit bit-significance study
│   │   ├── run_denoising_benchmark.py # Comparative quantum vs classical benchmark
│   │   └── run_noise_sweep.py         # Multi-noise channel sweep
│   ├── metrics/                       # Evaluation Metrics Engine
│   │   ├── image_metrics.py           # PSNR, MSE, adaptive-window SSIM
│   │   └── quantum_metrics.py         # Quantum state fidelity, DAG depth, CNOT count
│   └── noise/                         # Open-System Kraus Noise Models
│       ├── channels.py                # Depolarizing, thermal relaxation (T1/T2)
│       └── readout.py                 # Asymmetric measurement confusion matrix
│   └── quantum_denoising/             # Quantum Image Denoising Circuits
│       ├── qhwt.py                    # Quantum Haar Wavelet Transform & Thresholding
│       ├── spatial_adder.py           # Reversible NEQR 2x2 Spatial Moving Average
│       └── vqdae.py                   # Variational Quantum Denoising Autoencoder
├── tests/                             # Automated Test Harness (48 Tests Passing)
│   ├── test_api.py                    # WebSocket & REST endpoint integration tests
│   ├── test_denoising.py              # QHWT, Spatial Adder, and Classical tests
│   ├── test_denoising_benchmark.py    # Denoising benchmark runner tests
│   ├── test_encoding.py               # FRQI & NEQR lossless & shot tests
│   ├── test_metrics.py                # Metric accuracy tests
│   ├── test_noise.py                  # CPTP Kraus channel validation
│   ├── test_sweeps.py                 # Noise sweep and bitflip study runner tests
│   └── test_vqdae.py                  # VQDAE variational ansatz and optimization tests
├── ui/                                # Next.js 16 Real-Time Quantum Studio
│   ├── app/                           # App Router (page.tsx, layout.tsx, globals.css)
│   ├── components/                    # 6-Stage modular pipeline stages & vertical stepper
│   ├── lib/                           # Zustand state store & WebSocket streaming hook
│   └── package.json                   # UI dependencies and build scripts
├── .github/workflows/ci.yml           # Automated CI workflow
├── Dockerfile                         # Production multi-stage backend container
├── docker-compose.yml                 # Local multi-service orchestration
├── render.yaml                        # Render backend deployment blueprint
├── GUIDE.md                           # This step-by-step setup and execution guide
├── main.py                            # Master CLI entrypoint & demo runner
├── PLAN.md                            # Comprehensive research and engineering plan
├── PREP.md                            # Mid-term project defense and viva battlepack
├── PROGRESS_REPORT.md                 # Exhaustive project progress report
├── pyproject.toml                     # Modern package metadata & dependencies
└── uv.lock                            # Deterministic pinned dependency lockfile
```

---

## 6. Troubleshooting & Common Questions

### Q1: `ModuleNotFoundError: No module named 'src'`
**Cause:** The package was not installed in editable development mode or `PYTHONPATH` was not exported.  
**Fix:** Run `uv sync --frozen --all-extras` or export `PYTHONPATH="."`.

### Q2: BM3D / OpenCV runtime warnings on $4 \times 4$ images
**Cause:** $4 \times 4$ patches are smaller than classical patch-matching windows (default 8x8 in standard BM3D).  
**Fix:** Handled automatically. The wrapper in [`bm3d_wrapper.py`](file:///Users/ojhaprathmesh/Projects/QIP_Repo/src/classical_denoising/bm3d_wrapper.py) detects micro-resolutions and gracefully falls back to an adaptive bilateral filter to prevent crashes.

### Q3: `ValueError: win_size exceeds image extent` in SSIM
**Cause:** Scikit-Image SSIM uses a default window of $7 \times 7$, which crashes on a $4 \times 4$ matrix.  
**Fix:** Handled automatically. Our implementation in [`image_metrics.py`](file:///Users/ojhaprathmesh/Projects/QIP_Repo/src/metrics/image_metrics.py) dynamically adjusts `win_size = min(H, W, 7)` ensuring valid odd window sizes for any image dimension.

### Q4: Port 8000 is already in use when launching FastAPI
**Fix:** Specify a different port when running Uvicorn:
```bash
uvicorn api.server:app --reload --port 8001
```

### Q5: Out of Memory during NEQR simulations
**Cause:** Simulating full $2^N \times 2^N$ quantum density matrices on classical computers scales exponentially. An $8 \times 8$ NEQR image requires 14 qubits ($\approx 4\text{ GB RAM}$). For $16 \times 16$ (16 qubits) and above, classical memory is exhausted.  
**Fix:** Use finite shot sampling (`add_measurement=True` with `AerSimulator()`) or Matrix Product States (MPS) rather than full statevector density matrices.

---

## 7. Next Steps & Active Exploration

With the framework fully implemented and operational, here is how to explore the project deliverables:
1. **Interactive Web Studio:** Visit [https://qip.ojhaprathmesh.in](https://qip.ojhaprathmesh.in) to interact with live downsampling, state synthesis, noise chamber controls, and side-by-side denoising.
2. **Review the Academic Paper:** Inspect `paper/main.tex` and compiled vector figures (`figures/`) for the IEEE-format manuscript.
3. **Explore the Defense Pack:** Review [`PREP.md`](file:///Users/ojhaprathmesh/Projects/QIP_Repo/PREP.md) for 20-minute presentation timings and viva defense answers.
4. **Inspect the Progress Report:** Review [`PROGRESS_REPORT.md`](file:///Users/ojhaprathmesh/Projects/QIP_Repo/PROGRESS_REPORT.md) for detailed mathematical derivations and benchmark results.

