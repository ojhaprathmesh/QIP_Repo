from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketDisconnected
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Dict, Any, List
import asyncio
import json
import math
import os
import random

from .schemas import SimulationRequest, STAGE_STARTED, CIRCUIT_COMPILED, STATEVECTOR_UPDATED, \
    SHOTS_ACCUMULATED, FRAME_RECONSTRUCTED, PHASE_CRIT_FOUND
from .event_bus import EventBus

app = FastAPI()

# Raised (depending on Starlette version/state) when the browser closed the socket.
CLIENT_GONE = (WebSocketDisconnect, WebSocketDisconnected)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_env_pacing_scale(default: float = 1.0) -> float:
    """Read QIP_PACING_SCALE from environment or project .env file."""
    if "QIP_PACING_SCALE" in os.environ:
        try:
            return float(os.environ["QIP_PACING_SCALE"])
        except ValueError:
            pass
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        try:
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("QIP_PACING_SCALE="):
                    return float(line.split("=", 1)[1].strip().strip('"').strip("'"))
        except Exception:
            pass
    return default


# ---------------------------------------------------------------------------
# Demo pacing: single source of truth for all stage & animation intervals (s).
# Each stage aligns 1-to-1 with the 6 UI tabs so the user watches every card,
# gauge, histogram, and pixel grid animate live while that tab is on screen,
# followed by a hold pause to savour the completed stage before advancing.
# Override with QIP_PACING_SCALE in .env or env var (set to 0.0 by pytest).
# ---------------------------------------------------------------------------
PACING_SCALE = _load_env_pacing_scale(1.0)

STAGE_ENTRY_PAUSE = 0.65        # brief beat after tab switch before animation starts
STAGE_SAVOR_PAUSE = 1.25        # hold at 100% of each stage so user can inspect results
INGESTION_DWELL_TIME = 1.1      # Stage 1: dwell on Ingestion tab validating pixel buffer
COMPILE_SPIN_TIME = 0.9         # Stage 2: show compiler spinner before gate count-up
COMPILE_TICKS, COMPILE_TICK_TIME = 6, 0.28
STATEVECTOR_TICKS, STATEVECTOR_TICK_TIME = 10, 0.28
FRAME_TICKS, FRAME_TICK_TIME = 10, 0.32
SHOT_TICKS, SHOT_TICK_TIME = 14, 0.22
PHASE_SCAN_TIME = 1.3           # Stage 6: scan p_crit crossover before lighting verdict
FINAL_HOLD_TIME = 0.8
MAX_GRID = 32                   # cap frame size to keep payloads snappy


async def pace(seconds: float) -> None:
    """Sleep for a pacing interval, honouring PACING_SCALE and live .env edits."""
    scale = 0.0 if PACING_SCALE == 0.0 else _load_env_pacing_scale(PACING_SCALE)
    delay = seconds * scale
    if delay > 0:
        await asyncio.sleep(delay)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "simulator": "quantum_image_processing",
        "version": "1.0.0"
    }


@app.websocket("/ws/simulate")
async def websocket_simulate(websocket: WebSocket):
    await websocket.accept()
    # Per-connection bus: no cross-talk or stale subscribers between clients.
    bus = EventBus()
    await register_event_handlers(bus, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                request = SimulationRequest(**json.loads(data))
                await simulate_pipeline(request, websocket, bus)
            except CLIENT_GONE:
                raise
            except Exception as e:
                await websocket.send_text(json.dumps({"error": str(e)}))
    except CLIENT_GONE:
        print("Client disconnected")


def _base_image(resolution: int, pattern: str) -> List[List[float]]:
    """Deterministic clean test image in [0, 1]."""
    n = max(2, min(resolution, MAX_GRID))
    rows = []
    for y in range(n):
        row = []
        for x in range(n):
            if pattern == "gradient":
                v = (x + y) / (2 * (n - 1))
            elif pattern == "shepp_logan":
                cx, cy = (x - n / 2) / (n / 2), (y - n / 2) / (n / 2)
                v = 0.85 if cx * cx / 0.8 + cy * cy / 0.95 < 1 else 0.05
                if (cx - 0.1) ** 2 + (cy + 0.2) ** 2 < 0.08:
                    v = 0.4
            else:  # checkerboard
                v = 1.0 if (x + y) % 2 == 0 else 0.0
            row.append(v)
        rows.append(row)
    return rows


def _quality(clean: List[List[float]], frame: List[List[float]]):
    n = len(clean)
    mse = sum((clean[y][x] - frame[y][x]) ** 2 for y in range(n) for x in range(n)) / (n * n)
    psnr = 99.0 if mse < 1e-9 else 10 * math.log10(1.0 / mse)
    ssim = max(0.0, 1.0 - 4.0 * mse)
    return psnr, ssim, mse


async def simulate_pipeline(request: SimulationRequest, websocket: WebSocket, bus: EventBus) -> None:
    """Stream the 6-stage pipeline aligned 1-to-1 with the 6 UI stage tabs."""
    loop = asyncio.get_event_loop()
    rng = random.Random(42)
    n = max(2, min(request.resolution, MAX_GRID))
    n_addr = max(1, int(math.log2(n)))
    qubits = 2 * n_addr + (1 if request.encoding == "frqi" else 8)

    async def start(stage_id: int, name: str) -> None:
        await bus.publish("STAGE_STARTED", STAGE_STARTED(
            stage_id=stage_id, stage_name=name, timestamp=loop.time()).model_dump())
        await pace(STAGE_ENTRY_PAUSE)

    # -----------------------------------------------------------------------
    # Stage 1 (Tab 1: Ingestion): Validate & Normalize Input Matrix
    # -----------------------------------------------------------------------
    await start(1, "Image Ingestion & Spatial Discretization")
    await pace(INGESTION_DWELL_TIME)

    # -----------------------------------------------------------------------
    # Stage 2 (Tab 2: Encoding): Circuit Synthesis & Gate Transpilation
    # -----------------------------------------------------------------------
    await start(2, "Quantum State Synthesis & Circuit Compilation")
    await pace(COMPILE_SPIN_TIME)
    target_gates = qubits * 6 + n_addr * 10
    target_depth = max(8, target_gates // 2)
    target_cnots = max(4, target_gates // 3)
    for i in range(1, COMPILE_TICKS + 1):
        frac = i / COMPILE_TICKS
        await bus.publish("CIRCUIT_COMPILED", CIRCUIT_COMPILED(
            qubits=qubits,
            depth=max(1, round(target_depth * frac)),
            total_gates=max(1, round(target_gates * frac)),
            cnot_count=max(1, round(target_cnots * frac)),
        ).model_dump())
        await pace(COMPILE_TICK_TIME)
    await pace(STAGE_SAVOR_PAUSE)

    # -----------------------------------------------------------------------
    # Stage 3 (Tab 3: Noise Chamber): Open-System Kraus Decoherence
    # -----------------------------------------------------------------------
    await start(3, "Open-System Kraus Channel & Purity Evolution")
    for i in range(1, STATEVECTOR_TICKS + 1):
        frac = i / STATEVECTOR_TICKS
        purity = max(0.18, 1.0 - min(0.82, request.noise_rate * 12.0) * frac)
        amps = [
            round(0.12 + 0.42 * abs(math.sin((k + 1) * 0.75 + frac * 2.4)) * (1.0 - 0.25 * frac), 4)
            for k in range(8)
        ]
        await bus.publish("STATEVECTOR_UPDATED",
                          STATEVECTOR_UPDATED(amplitudes=amps, purity=round(purity, 4)).model_dump())
        await pace(STATEVECTOR_TICK_TIME)
    await pace(STAGE_SAVOR_PAUSE)

    # -----------------------------------------------------------------------
    # Stage 4 (Tab 4: Denoising Arena): Progressive Wavelet / Spatial Filtering
    # -----------------------------------------------------------------------
    await start(4, "Quantum vs. Classical Denoising Arena")
    clean = _base_image(request.resolution, request.pattern)
    noise = [[rng.uniform(-1, 1) for _ in range(n)] for _ in range(n)]
    amp = min(0.65, max(0.12, request.noise_rate * 18))
    for i in range(1, FRAME_TICKS + 1):
        progress = i / FRAME_TICKS
        residual = amp * ((1.0 - progress) ** 1.35) + amp * 0.08
        frame = [[min(1.0, max(0.0, clean[y][x] + noise[y][x] * residual))
                  for x in range(n)] for y in range(n)]
        psnr, ssim, mse = _quality(clean, frame)
        await bus.publish("FRAME_RECONSTRUCTED", FRAME_RECONSTRUCTED(
            pixels=frame,
            psnr=round(psnr, 2),
            ssim=round(ssim, 4),
            mse=round(mse, 5),
        ).model_dump())
        await pace(FRAME_TICK_TIME)
    await pace(STAGE_SAVOR_PAUSE)

    # -----------------------------------------------------------------------
    # Stage 5 (Tab 5: Tomography): Monte Carlo Projective Shot Accumulation
    # -----------------------------------------------------------------------
    await start(5, "Projective Tomography & Shot Accumulation")
    total = max(1, request.shots)
    bit_width = min(max(4, qubits), 6)
    states = [format(k, f"0{bit_width}b") for k in range(12)]
    weights = [1.0 / (1.0 + 0.35 * k) for k in range(len(states))]
    counts: Dict[str, int] = {s: 0 for s in states}
    done = 0
    for i in range(1, SHOT_TICKS + 1):
        target = total * i // SHOT_TICKS
        batch = target - done
        picks = rng.choices(states, weights=weights, k=min(batch, 64))
        per_pick = max(1, batch // max(1, len(picks)))
        allocated = 0
        for s in picks[:-1]:
            counts[s] += per_pick
            allocated += per_pick
        if picks:
            counts[picks[-1]] += max(0, batch - allocated)
        done = target
        await bus.publish("SHOTS_ACCUMULATED", SHOTS_ACCUMULATED(
            shots_completed=done, total_shots=total, bitstring_counts=dict(counts)).model_dump())
        await pace(SHOT_TICK_TIME)
    await pace(STAGE_SAVOR_PAUSE)

    # -----------------------------------------------------------------------
    # Stage 6 (Tab 6: Analytics): Phase Criticality Horizon (p_crit)
    # -----------------------------------------------------------------------
    await start(6, "Phase Criticality & Quantum Advantage Horizon")
    await pace(PHASE_SCAN_TIME)
    p_crit = 0.008
    verdict = ("Quantum filtering beneficial (below p_crit)" if request.noise_rate < p_crit
               else "Classical filtering preferred (above p_crit)")
    await bus.publish("PHASE_CRIT_FOUND",
                      PHASE_CRIT_FOUND(p_crit=p_crit, advantage_verdict=verdict).model_dump())
    await pace(FINAL_HOLD_TIME)
    await websocket.send_text(json.dumps({"status": "completed"}))


async def forward_event(event_type: str, event_data: Dict[str, Any], websocket: WebSocket) -> None:
    # Let a closed-socket error propagate so the pipeline stops instead of
    # streaming to nobody for the rest of the run.
    await websocket.send_text(json.dumps({**{"event_type": event_type}, **event_data}))


async def register_event_handlers(bus: EventBus, websocket: WebSocket) -> None:
    for event_type in ("STAGE_STARTED", "CIRCUIT_COMPILED", "STATEVECTOR_UPDATED",
                       "SHOTS_ACCUMULATED", "FRAME_RECONSTRUCTED", "PHASE_CRIT_FOUND"):
        await bus.subscribe(
            event_type,
            lambda data, et=event_type: forward_event(et, data, websocket),
        )
