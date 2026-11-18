from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Demo pacing: single source of truth for all animation timings (seconds).
# Total run time is ~13 s at scale 1.0. Override with QIP_PACING_SCALE
# (e.g. 0.5 = twice as fast, 0 = no delays, used by the test suite).
# ---------------------------------------------------------------------------
PACING_SCALE = float(os.environ.get("QIP_PACING_SCALE", "1.0"))
STAGE_PAUSE = 1.0          # dwell on each stage banner before data arrives
CIRCUIT_COMPILE_TIME = 1.5
STATEVECTOR_TICKS, STATEVECTOR_TICK_TIME = 5, 0.4
SHOT_TICKS, SHOT_TICK_TIME = 12, 0.25
FRAME_TICKS, FRAME_TICK_TIME = 8, 0.4
PHASE_ANALYSIS_TIME = 1.2
FINAL_PAUSE = 0.6
MAX_GRID = 32              # cap frame size to keep payloads small


async def pace(seconds: float) -> None:
    """Sleep for a pacing interval, honouring the global scale (non-blocking)."""
    delay = seconds * PACING_SCALE
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
            except WebSocketDisconnect:
                raise
            except Exception as e:
                await websocket.send_text(json.dumps({"error": str(e)}))
    except WebSocketDisconnect:
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
    """Stream the 6-stage pipeline with demo-friendly pacing and progressive updates."""
    loop = asyncio.get_event_loop()
    rng = random.Random(42)
    n = max(2, min(request.resolution, MAX_GRID))
    n_addr = max(1, int(math.log2(n)))
    qubits = 2 * n_addr + (1 if request.encoding == "frqi" else 8)

    async def start(stage_id: int, name: str) -> None:
        await bus.publish("STAGE_STARTED", STAGE_STARTED(
            stage_id=stage_id, stage_name=name, timestamp=loop.time()).model_dump())
        await pace(STAGE_PAUSE)

    # Stage 1: Circuit Compilation
    await start(1, "Circuit Compilation")
    await pace(CIRCUIT_COMPILE_TIME)
    gates = qubits * 4 + n_addr * 6
    await bus.publish("CIRCUIT_COMPILED", CIRCUIT_COMPILED(
        qubits=qubits, depth=gates // 3, total_gates=gates, cnot_count=gates // 4).model_dump())

    # Stage 2: State Vector Evolution (purity decays as noise accumulates)
    await start(2, "State Vector Evolution")
    for i in range(1, STATEVECTOR_TICKS + 1):
        frac = i / STATEVECTOR_TICKS
        purity = max(0.0, 1.0 - request.noise_rate * 10 * frac)
        amps = [round(abs(math.sin((k + 1) * frac)) / 2, 4) for k in range(8)]
        await bus.publish("STATEVECTOR_UPDATED",
                          STATEVECTOR_UPDATED(amplitudes=amps, purity=round(purity, 4)).model_dump())
        await pace(STATEVECTOR_TICK_TIME)

    # Stage 3: Shot Accumulation (counts grow progressively toward the budget)
    await start(3, "Shot Accumulation")
    total = max(1, request.shots)
    states = [format(k, f"0{min(qubits, 6)}b") for k in range(4)]
    counts: Dict[str, int] = {s: 0 for s in states}
    done = 0
    for i in range(1, SHOT_TICKS + 1):
        target = total * i // SHOT_TICKS
        batch = target - done
        for _ in range(4):
            counts[rng.choice(states)] += batch // 4
        counts[states[0]] += batch - 4 * (batch // 4)
        done = target
        await bus.publish("SHOTS_ACCUMULATED", SHOTS_ACCUMULATED(
            shots_completed=done, total_shots=total, bitstring_counts=dict(counts)).model_dump())
        await pace(SHOT_TICK_TIME)

    # Stage 4: Frame Reconstruction (noisy image progressively refined)
    await start(4, "Frame Reconstruction")
    clean = _base_image(request.resolution, request.pattern)
    noise = [[rng.uniform(-1, 1) for _ in range(n)] for _ in range(n)]
    amp = min(0.5, request.noise_rate * 20)
    last = None
    for i in range(1, FRAME_TICKS + 1):
        residual = amp * (1 - i / FRAME_TICKS) + amp * 0.1
        frame = [[min(1.0, max(0.0, clean[y][x] + noise[y][x] * residual))
                  for x in range(n)] for y in range(n)]
        psnr, ssim, mse = _quality(clean, frame)
        last = FRAME_RECONSTRUCTED(pixels=frame, psnr=round(psnr, 2),
                                   ssim=round(ssim, 4), mse=round(mse, 5))
        await bus.publish("FRAME_RECONSTRUCTED", last.model_dump())
        await pace(FRAME_TICK_TIME)

    # Stage 5: Phase Criticality Analysis
    await start(5, "Phase Criticality Analysis")
    await pace(PHASE_ANALYSIS_TIME)
    p_crit = 0.008
    verdict = ("Quantum filtering beneficial (below p_crit)" if request.noise_rate < p_crit
               else "Classical filtering preferred (above p_crit)")
    await bus.publish("PHASE_CRIT_FOUND",
                      PHASE_CRIT_FOUND(p_crit=p_crit, advantage_verdict=verdict).model_dump())

    # Stage 6: Final Results
    await start(6, "Final Results")
    await pace(FINAL_PAUSE)
    await websocket.send_text(json.dumps({"status": "completed"}))


async def forward_event(event_type: str, event_data: Dict[str, Any], websocket: WebSocket) -> None:
    try:
        await websocket.send_text(json.dumps({**{"event_type": event_type}, **event_data}))
    except Exception:
        pass  # client went away mid-stream


async def register_event_handlers(bus: EventBus, websocket: WebSocket) -> None:
    for event_type in ("STAGE_STARTED", "CIRCUIT_COMPILED", "STATEVECTOR_UPDATED",
                       "SHOTS_ACCUMULATED", "FRAME_RECONSTRUCTED", "PHASE_CRIT_FOUND"):
        await bus.subscribe(
            event_type,
            lambda data, et=event_type: forward_event(et, data, websocket),
        )
