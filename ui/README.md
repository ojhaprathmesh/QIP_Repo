# QIP Quantum Studio — Real-Time Quantum Image Processing Dashboard

> **Interactive 6-Stage Web Studio for Quantum Image Robustness, Open-System Decoherence, and Denoising Benchmarking**
>
> 🌐 **Live Production URL:** [https://qip.ojhaprathmesh.in](https://qip.ojhaprathmesh.in)  
> ⚡ **Connected Simulation Engine:** FastAPI + Qiskit on Render (`https://qip-backend-93n1.onrender.com`)

---

## 1. Overview

**QIP Quantum Studio** is a state-of-the-art web application providing visual, interactive, gate-level telemetry for quantum image processing under realistic Noisy Intermediate-Scale Quantum (NISQ) conditions. 

Built with **Next.js 16 (React 19)**, **Tailwind CSS v4**, **Framer Motion**, and **Zustand**, the studio streams full-duplex quantum simulation state from a Qiskit backend via WebSockets at 60 FPS, with an in-browser classical simulation fallback when the backend is offline.

---

## 2. Core Architecture & Features

### 🎮 6-Stage Modular Visual Pipeline
1. **Stage 01 — Real-World Image Ingestion & Preprocessing:**
   - Real-world image upload (PNG, JPG, WebP) with auto center-crop and ITU-R BT.709 grayscale luminance extraction.
   - Built-in canonical paper benchmarks (USC-SIPI Cameraman, NASA Lunar Crater, Shepp-Logan CT Phantom, Checkerboard, Gradient).
   - Configurable register resolution ($4 \times 4$ up to $128 \times 128$) with dynamic qubit scaling ($2n+1$ for FRQI vs $2n+q$ for NEQR).
   - Anti-aliased Area, Bilinear, and Nearest-neighbor downsampling kernels; 8-bit / 4-bit color quantization; radiometric gamma correction ($\gamma$ slider).
   - Dynamic noise regime indicator with critical horizon $p_{\text{crit}} = 0.008$.

2. **Stage 02 — Quantum State Synthesis & Encoding:**
   - Visual toggle between **FRQI** (Continuous $R_y$ rotation angle encoding) and **NEQR** (Discrete computational basis bitstrings).
   - Gate-level circuit DAG summary (qubit register size, circuit depth, single-qubit vs CNOT count).
   - Superposition probability distribution bar chart.

3. **Stage 03 — NISQ Noise Chamber & Decoherence:**
   - Simulation of completely positive trace-preserving (CPTP) Kraus noise channels: Depolarizing, Thermal Relaxation ($T_1$ damping, $T_2$ pure dephasing), Readout Confusion, and Composite NISQ.
   - Interactive 3D Bloch sphere decoherence visualizer.
   - Quantum state fidelity gauge ($\mathcal{F}$) and purity tracking ($\text{Tr}(\rho^2)$).

4. **Stage 04 — Denoise Arena & Benchmark Comparison:**
   - Split-screen visual comparison: Quantum-Assisted Filter (**QHWT** / **Quantum Spatial Adder**) vs Classical Baselines (**BM3D**, **Bilateral**, **Median**, **Gaussian**).
   - PSNR (dB), SSIM, and MSE metrics with real-time delta scorecards.

5. **Stage 05 — Shot-Based Measurement & State Tomography:**
   - Projective readout simulation across variable shot budgets ($N_{\text{shots}} \in [10^3, 10^6]$).
   - Progressive Monte Carlo shot accumulation and raster image reconstruction.

6. **Stage 06 — Performance Benchmarks & Phase Transition:**
   - Live parametric sweep curves across noise rates $p \in [10^{-4}, 10^{-1}]$ powered by Recharts.
   - Empirical $p_{\text{crit}}$ phase boundary derivation comparing quantum vs classical regimes.
   - Dynamic Quantum Advantage verdict badge.

---

## 3. UI/UX Specifications

- **Obsidian Dark Aesthetic:** Custom cyber-quantum palette (`#090a0f` obsidian background, `#00f5ff` electric cyan, `#a855f7` quantum violet, `#10b981` emerald).
- **100vh Viewport Lock:** Strict fixed-viewport layout (`h-screen overflow-hidden`) with fixed header, internal stage scrolling, and a full-height vertical pipeline stepper.
- **Dual Execution Modes:**
  - **Auto Flow:** Continuous 6-stage simulation with automatic progression.
  - **Manual Step:** Guided stage-by-stage stepping (advance via UI button or `→` / `Space` hotkey).
- **Graceful Fallback:** Automatically probes backend health and switches smoothly between **Qiskit Simulator** (connected) and **Client Fallback** (in-browser mock engine) without breaking the user experience.

---

## 4. Local Development

### Prerequisites
- Node.js `20.x` or later
- npm, pnpm, or bun

### Setup

1. **Install dependencies:**
   ```bash
   npm ci
   ```

2. **Configure environment:**
   Create `.env.local` (optional for local development):
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/simulate
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.

4. **Build production bundle:**
   ```bash
   npm run build
   ```

---

## 5. Deployment

- **Vercel:** Automatically deploys on git push to `main` with root directory set to `ui`.
- **Environment Variables in Production:**
  - `NEXT_PUBLIC_API_URL`: `https://qip-backend-93n1.onrender.com`
  - `NEXT_PUBLIC_WS_URL`: `wss://qip-backend-93n1.onrender.com/ws/simulate`
