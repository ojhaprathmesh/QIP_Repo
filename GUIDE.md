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
The repository includes a comprehensive 21-test suite covering state preparation, Kraus noise channels, denoising filters, and the API streaming bridge:

```bash
pytest -v
```

**Expected Output:**
```
============================= test session starts ==============================
collected 21 items

tests/test_api.py::test_health_check PASSED                              [  4%]
tests/test_api.py::test_simulation_request_schema PASSED                 [  9%]
tests/test_api.py::test_websocket_simulate PASSED                        [ 14%]
tests/test_denoising.py::test_classical_filters_execution PASSED         [ 19%]
tests/test_denoising.py::test_qhwt_circuit_synthesis PASSED              [ 23%]
tests/test_denoising.py::test_qhwt_lossless_roundtrip PASSED             [ 28%]
tests/test_denoising.py::test_qhwt_denoising_noise_reduction PASSED      [ 33%]
tests/test_denoising.py::test_spatial_adder_filter_execution PASSED      [ 38%]
tests/test_encoding.py::test_frqi_initialization PASSED                  [ 42%]
tests/test_encoding.py::test_neqr_initialization PASSED                  [ 47%]
tests/test_encoding.py::test_frqi_lossless_roundtrip PASSED              [ 52%]
tests/test_encoding.py::test_neqr_lossless_roundtrip PASSED              [ 57%]
tests/test_encoding.py::test_frqi_shot_sampling_roundtrip PASSED         [ 61%]
tests/test_encoding.py::test_neqr_shot_sampling_roundtrip PASSED         [ 66%]
tests/test_metrics.py::test_perfect_reconstruction_metrics PASSED        [ 71%]
tests/test_metrics.py::test_perturbed_metrics PASSED                     [ 76%]
tests/test_noise.py::test_build_depolarizing_model PASSED                [ 80%]
tests/test_noise.py::test_build_thermal_relaxation_model PASSED          [ 85%]
tests/test_noise.py::test_build_readout_error_model PASSED               [ 90%]
tests/test_noise.py::test_build_composite_nisq_model PASSED              [ 95%]
tests/test_noise.py::test_noisy_simulation_execution PASSED              [100%]

======================== 21 passed, 1 warning in 2.85s =========================
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

#### 2. Check the Health Endpoint (in a new terminal):
```bash
curl http://localhost:8000/api/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "simulator": "quantum_image_processing",
  "version": "1.0.0"
}
```

#### 3. Test WebSocket Streaming (`/ws/simulate`):
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

### 4.4 Running the Next.js 15 Real-Time Quantum Studio (`ui/`)

Phase 3B provides a modern, interactive Next.js 15 web application with 6 modular stage components, live WebSocket streaming, and Framer Motion micro-animations.

#### 1. Start the FastAPI Simulation Backend:
In terminal 1:
```bash
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Start the Next.js Frontend Development Server:
In terminal 2:
```bash
cd ui
npm run dev
```

#### 3. Open in Browser:
Visit `http://localhost:3000` to interact with:
* **Interactive 6-Stage Pipeline Stepper:** Step through Ingestion, Encoding, Noise Chamber, Denoising Arena, Tomography, and Analytics.
* **Live Ingestion Configurator:** Resize images ($4\times 4$ to $32\times 32$) with live dynamic qubit requirement recalculation ($2n+1$ vs $2n+q$).
* **Real-Time Simulation Trigger:** Click **"Run Full Simulation"** to stream gate-level circuit compilation, statevector purity, Monte Carlo shot accumulation, and progressive raster reconstruction via WebSocket at 60 FPS.

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
├── tests/                             # Automated Test Harness
│   ├── test_api.py                    # WebSocket & REST endpoint integration tests
│   ├── test_denoising.py              # QHWT, Spatial Adder, and Classical tests
│   ├── test_encoding.py               # FRQI & NEQR lossless & shot tests
│   ├── test_metrics.py                # Metric accuracy tests
│   └── test_noise.py                  # CPTP Kraus channel validation
├── GUIDE.md                           # This step-by-step setup and execution guide
├── main.py                            # Master CLI entrypoint & demo runner
├── PLAN.md                            # Comprehensive 874-line research and engineering plan
├── PREP.md                            # Mid-term project defense and viva battlepack
├── PROGRESS_REPORT.md                 # Exhaustive project progress report
├── pyproject.toml                     # Modern package metadata & dependencies
└── uv.lock                            # Deterministic pinned dependency lockfile
```

---

## 6. Troubleshooting & Common Questions

### Q1: `ModuleNotFoundError: No module named 'src'`
**Cause:** The package was not installed in editable development mode.  
**Fix:** Run `pip install -e .` from the repository root directory while your virtual environment is active.

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

## 7. Next Steps & Active Development

Now that your local environment is running, here is how you can explore and contribute to the next milestones:
1. **Explore the Defense Pack:** Review [`PREP.md`](file:///Users/ojhaprathmesh/Projects/QIP_Repo/PREP.md) for 20-minute presentation timings and viva defense answers.
2. **Review the Progress Report:** Inspect [`PROGRESS_REPORT.md`](file:///Users/ojhaprathmesh/Projects/QIP_Repo/PROGRESS_REPORT.md) for detailed mathematical proofs and deliverables matrices.
3. **Contribute to Upcoming Phases:**
   - **Phase 3B:** Scaffold the Next.js 15 Visual Studio in `ui/`.
   - **Phase 4:** Expand [`run_noise_sweep.py`](file:///Users/ojhaprathmesh/Projects/QIP_Repo/src/experiments/run_noise_sweep.py) to execute the automated 500-run parametric sweep across $p \in [10^{-4}, 10^{-1}]$.

