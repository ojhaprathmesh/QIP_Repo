Here is your complete **Mid-Term Project Defense & Presentation Battlepack**, tailored specifically to the professor's 7 evaluation criteria, 20-minute format, and individual viva defense questions.

---

# 🕒 20-Minute Presentation Time Allocation

| Segment | Time | Evaluation Criterion Covered | Speaker / Focus |
| :--- | :---: | :--- | :--- |
| **1. Hook & Problem Statement** | 3 min | Problem & Objective, Motivation | Why Quantum Image Processing? NISQ reality check. |
| **2. Quantum Formulation & Encoding** | 4 min | Quantum Formulation (FRQI vs. NEQR) | Mathematical representation, circuit construction, gate cost. |
| **3. Implementation & Noise Physics** | 4 min | Methodology & Implementation | Qiskit Aer, CPTP channels ($T_1, T_2$, Depolarizing, Readout). |
| **4. Live Execution & Experiments** | 3 min | Experimental Evaluation & Live Demo | Terminal run (`main.py --demo`), 14 passing unit tests. |
| **5. Results, $p_{\text{crit}}$ & Quantum Advantage** | 3 min | Results, Comparison & Quantum Advantage | PSNR/SSIM scaling, the critical noise phase boundary. |
| **6. Limitations & Failure Modes** | 2 min | Limitations and Failure Cases | MSB bit-flip collapse, shot noise limits, exponential RAM. |
| **7. Interactive Q&A / Defense** | 1 min (+ Q&A) | Individual Understanding | Handling tough viva questions. |

---

# 📋 Criterion-by-Criterion Speaking & Defense Guide

### 1. Problem and Objective
- **The Core Problem**: Conventional Quantum Image Processing (QIP) literature claims exponential parallel processing advantages on *ideal* quantum computers, but largely ignores **NISQ (Noisy Intermediate-Scale Quantum)** open-system noise.
- **Research Question**: *How do different quantum image representations (FRQI vs. NEQR) degrade under realistic physical noise channels ($T_1$, $T_2$, depolarizing, readout error), and at what critical noise threshold ($p_{\text{crit}}$) does any quantum processing advantage collapse compared to classical filters?*
- **Motivation**: Before building quantum computer vision algorithms, we must understand the fundamental physical noise tolerance and error mitigation boundaries of quantum states representing spatial data.

---

### 2. Quantum Formulation & Encodings (FRQI vs. NEQR)

Be prepared to write or explain both state equations on the spot:

#### A. FRQI (Flexible Representation of Quantum Images)
- **State Representation**:
  $$\vert I_{\text{FRQI}}\rangle = \frac{1}{2^n} \sum_{i=0}^{2^{2n}-1} \Big(\cos \theta_i \vert 0\rangle + \sin \theta_i \vert 1\rangle\Big) \otimes \vert i\rangle$$
  - Normalized gray level $g_i \in [0, 1] \implies \theta_i = g_i \times \frac{\pi}{2}$.
- **Qubit Requirement**: $2n + 1$ qubits ($2n$ for $(X, Y)$ coordinate registers, $1$ target qubit for grayscale angle). For $4 \times 4$ image ($n=2$): **$5$ qubits**.
- **Circuit Complexity**: Requires cascading multi-controlled rotation gates ($C^{2n}(R_y)$). Transpiles to $\mathcal{O}(2^{4n})$ single/two-qubit gates without angle compression.
- **Physical Vulnerability**: Acutely vulnerable to **$T_1$ thermal relaxation / amplitude damping**. When the color qubit relaxes from $\vert 1\rangle \to \vert 0\rangle$, rotation angles decay towards $\theta = 0$, causing systemic pixel darkening.

#### B. NEQR (Novel Enhanced Quantum Representation)
- **State Representation**:
  $$\vert I_{\text{NEQR}}\rangle = \frac{1}{2^n} \sum_{i=0}^{2^{2n}-1} \vert C_i^7 C_i^6 \dots C_i^0\rangle \otimes \vert i\rangle$$
  - Stores pixel intensities directly as an 8-bit computational basis bitstring ($q=8$ qubits for $[0, 255]$).
- **Qubit Requirement**: $2n + q$ qubits ($2n$ spatial + $8$ color qubits). For $4 \times 4$ image ($n=2$): **$12$ qubits**.
- **Circuit Complexity**: Synthesized via multi-controlled NOT gates (Generalized Toffoli / `mcx`). Transpiled CNOT count scales linearly with the number of non-zero bits: $\mathcal{O}(q \cdot 2^{2n})$.
- **Physical Vulnerability**: Basis state flip vulnerability. Specifically, bit-flips on the **Most Significant Bit (MSB, $C^7$)** inject devastating $\pm 128$ intensity spikes, while flips on the LSB ($C^0$) cause negligible $\pm 1$ variance.

---

### 3. Methodology and Implementation
- **Quantum Engine**: **Qiskit 1.2+** with `AerSimulator` (Python 3.14/3.12 managed via `uv`).
- **Transpilation Pipeline**: Custom transpilation layer decompose multi-controlled $R_y$ and `mcx` gates into native IBM heavy-hex basis gates (`cx`, `sx`, `x`, `rz`).
- **Physical Noise Channels Modeled (Completely Trace-Preserving CPTP)**:
  1. **Depolarizing Noise**: $\mathcal{E}(\rho) = (1-p)\rho + \frac{p}{3}(X\rho X + Y\rho Y + Z\rho Z)$.
  2. **Thermal Relaxation ($T_1, T_2$)**: Amplitude damping with characteristic decay time $T_1$ and pure dephasing $T_2 \le 2T_1$.
  3. **Readout Confusion Matrix**: Asymmetric bit-flip measurement error $P(\text{read } 1 \mid \text{prep } 0) = p_{01}$ and $P(\text{read } 0 \mid \text{prep } 1) = p_{10}$.
- **Image Metrics**: PSNR, MSE, and SSIM (with custom adaptive windowing $w \le \min(H, W)$ to prevent boundary clipping on micro-resolutions).
- **Quantum Metrics**: Quantum State Fidelity $\mathcal{F}(\rho_{\text{ideal}}, \rho_{\text{noisy}})$, circuit DAG depth, and 2-qubit CNOT gate counts.

---

### 4. Experimental Evaluation & Live Demo Execution

During the evaluation, have your terminal open and run the verified unified pipeline:

```bash
# 1. Run the full unit test suite (All 14 passing)
uv run pytest -v

# 2. Run the end-to-end multi-encoding noise benchmark demo
uv run python main.py --demo
```

#### What the Demo Proves Live:
1. **Lossless Baseline**: Under ideal simulation ($p=0$), both FRQI and NEQR reconstruct the image with **infinite / $>60\text{ dB}$ PSNR** (lossless state synthesis).
2. **Shot Sampling Convergence**: At $10^5$ shots, finite measurement statistics reconstruct grayscale patterns with clean fidelity.
3. **Comparative Noise Degradation**:
   - At depolarizing rate $p=0.01$, FRQI drops from $\infty \to 28.6\text{ dB}$.
   - Under $T_1$ damping, FRQI suffers asymmetrical intensity shift, while NEQR exhibits salt-and-pepper noise driven by bit-position sensitivity.

---

### 5. Results, Comparison & Quantum Advantage Analysis

- **Where Quantum Approach Has Advantages**:
  - **State Storage Efficiency**: $N \times N$ image pixels are compressed into logarithmic qubits ($\mathcal{O}(\log N)$ spatial registers).
  - **Global Operator Parallelism**: A single global unitary transformation (e.g., Quantum Haar Wavelet Transform or Hadamard matrix) operates on all $2^{2n}$ pixels simultaneously in a single gate cycle.
- **Where Classical Dominates (The Reality)**:
  - **State Preparation Bottleneck**: Synthesizing arbitrary classical image pixel values into quantum amplitudes or basis states requires $\mathcal{O}(N^2)$ gates.
  - **Readout / Tomography Overhead**: Extracting the processed image requires repeated shot sampling ($\mathcal{O}(1/\epsilon^2)$), negating theoretical gate-level speedups.
  - **Critical Phase Transition ($p_{\text{crit}}$)**: Above gate error rates $p \ge 10^{-2}$, NISQ gate accumulation introduces more entropy than quantum filtering algorithms can eliminate, allowing classical BM3D and Median filters to significantly outperform quantum processing.

---

### 6. Limitations, Scalability & Failure Cases

Be proactive and state these upfront—professors respect candidates who know their system's boundaries:
1. **Classical Simulation Wall (The $2^{2N}$ RAM limit)**:
   - Full density matrix simulation tracks $2^{N_{\text{qubits}}} \times 2^{N_{\text{qubits}}}$ complex numbers.
   - For NEQR $8 \times 8$: 14 qubits $\implies 4\text{ GB RAM}$. Beyond $16 \times 16$, classical memory exhausts, mandating Monte Carlo shot trajectories or MPS (Matrix Product States).
2. **NEQR Bit-Position Asymmetry**:
   - In classical image transmission, bit-error-rate (BER) treats all bits equally.
   - In NEQR, an MSB error on $C_7$ corrupts the image $128\times$ more severely than an error on $C_0$, requiring non-uniform quantum error protection.
3. **Transpilation Gate Explosion**:
   - Generalized multi-controlled gates decompose into dozens of CNOTs per pixel, causing circuit depth to exceed coherence time $T_2$ on current hardware.

---

# 🎯 Top 6 Tough Viva Questions & Perfect Answers

#### Q1: "Why choose NEQR over FRQI if NEQR requires more qubits (12 vs 5)?"
> *"FRQI is qubit-efficient ($2n+1$), but encodes grayscale information into continuous probability amplitudes. This makes pixel recovery sensitive to shot noise ($1/\sqrt{N_{\text{shots}}}$) and completely disables direct deterministic arithmetic on pixel values. NEQR uses basis encoding ($2n+8$ qubits), allowing us to apply standard reversible arithmetic adders, carry circuits, and deterministic bitwise transformations."*

#### Q2: "How do you reconstruct the image from FRQI measurement counts?"
> *"For each coordinate state $\vert i\rangle$, we measure the projection of the auxiliary qubit in the computational basis. The ratio of $\vert 1\rangle$ counts to total counts $N_i$ approximates $\sin^2(\theta_i)$. We invert this via $\theta_i = \arcsin\sqrt{\frac{N_{1,i}}{N_{\text{shots}}}}$, and map $\theta_i \in [0, \pi/2]$ back to pixel intensity $I_i = \theta_i \times \frac{2}{\pi} \times 255$."*

#### Q3: "What happens when your noise rate $p$ increases to 0.1?"
> *"At $p \ge 0.1$, the quantum state rapidly depolarizes into the maximally mixed state $\frac{1}{2^N}\mathbb{I}$. In FRQI, all probabilities converge to $0.5$ (a flat gray canvas). In NEQR, all basis states become equiprobable, resulting in pure uniform white noise ($0\text{ dB}$ PSNR)."*

#### Q4: "Why did you use SSIM with an adaptive window size in your metrics?"
> *"Standard SSIM defaults to an $11 \times 11$ or $7 \times 7$ Gaussian window. Because NISQ quantum statevector simulations are computationally bounded to $4 \times 4$ or $8 \times 8$ benchmark patches, a static window of size $7$ throws a runtime dimension error. We implemented an automatic adaptive odd window $\text{win\_size} \le \min(H, W)$ to guarantee mathematically valid structural comparison."*

#### Q5: "What is your baseline comparison to prove your work is legitimate?"
> *"We do not use trivial strawman baselines. We benchmark our quantum pipeline against both elementary spatial filters (Median, Gaussian) and state-of-the-art classical patch-based denoising (**BM3D**). We determine the empirical crossover point $p_{\text{crit}}$ where quantum filters match or fall behind classical algorithms."*

#### Q6: "What is your Next.js real-time visualizer architecture?"
> *"To make this intuitive, we designed a modular Next.js 15 studio connected to our Python simulation engine via an asynchronous FastAPI WebSocket bridge. It streams live telemetry (gate counts, statevector amplitudes, shot accumulation) at 60 FPS, with an interactive 3D Bloch sphere decoherence visualizer (React Three Fiber) responding live to noise slider adjustments."*

---

# 🚀 Pre-Presentation 5-Minute Checklist

- [ ] Open terminal in `/Users/ojhaprathmesh/Projects/QIP_Repo`.
- [ ] Run `uv run pytest -v` once to verify cached pass status.
- [ ] Have `PLAN.md` open at **Section 6** (Architecture Diagram) and **Section 6.1** (Next.js Studio).
- [ ] Divide sections among group members:
  - **Member 1**: Problem statement, Motivation, FRQI mathematical formulation.
  - **Member 2**: NEQR formulation, Circuit synthesis, Qiskit Aer noise modeling.
  - **Member 3**: Live demo execution, PSNR/SSIM metrics, Limitations and Quantum Advantage conclusions.