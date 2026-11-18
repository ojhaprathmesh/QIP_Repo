from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import asyncio
import json

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

event_bus = EventBus()

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
    await register_event_handlers(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                request = SimulationRequest(**json.loads(data))

                # Simulate the 6-stage pipeline
                await simulate_pipeline(request, websocket)

            except Exception as e:
                await websocket.send_text(json.dumps({"error": str(e)}))
    except WebSocketDisconnect:
        print("Client disconnected")

async def simulate_pipeline(request: SimulationRequest, websocket: WebSocket) -> None:
    """Simulate the 6-stage pipeline and send progress updates."""
    # Stage 1: Circuit Compilation
    await event_bus.publish("STAGE_STARTED", STAGE_STARTED(stage_id=1, stage_name="Circuit Compilation", timestamp=asyncio.get_event_loop().time()).model_dump())
    await asyncio.sleep(0.01)
    circuit_data = CIRCUIT_COMPILED(qubits=10, depth=5, total_gates=20, cnot_count=5)
    await event_bus.publish("CIRCUIT_COMPILED", circuit_data.model_dump())
    await asyncio.sleep(0.01)

    # Stage 2: State Vector Evolution
    await event_bus.publish("STAGE_STARTED", STAGE_STARTED(stage_id=2, stage_name="State Vector Evolution", timestamp=asyncio.get_event_loop().time()).model_dump())
    await asyncio.sleep(0.01)
    state_data = STATEVECTOR_UPDATED(amplitudes=[0.1, 0.2, 0.3, 0.4], purity=0.95)
    await event_bus.publish("STATEVECTOR_UPDATED", state_data.model_dump())
    await asyncio.sleep(0.01)

    # Stage 3: Shot Accumulation
    await event_bus.publish("STAGE_STARTED", STAGE_STARTED(stage_id=3, stage_name="Shot Accumulation", timestamp=asyncio.get_event_loop().time()).model_dump())
    await asyncio.sleep(0.01)
    shots_data = SHOTS_ACCUMULATED(shots_completed=100, total_shots=1000, bitstring_counts={"000": 50, "001": 50})
    await event_bus.publish("SHOTS_ACCUMULATED", shots_data.model_dump())
    await asyncio.sleep(0.01)

    # Stage 4: Frame Reconstruction
    await event_bus.publish("STAGE_STARTED", STAGE_STARTED(stage_id=4, stage_name="Frame Reconstruction", timestamp=asyncio.get_event_loop().time()).model_dump())
    await asyncio.sleep(0.01)
    frame_data = FRAME_RECONSTRUCTED(pixels=[[0.1, 0.2], [0.3, 0.4]], psnr=30.0, ssim=0.9, mse=0.01)
    await event_bus.publish("FRAME_RECONSTRUCTED", frame_data.model_dump())
    await asyncio.sleep(0.01)

    # Stage 5: Phase Criticality Analysis
    await event_bus.publish("STAGE_STARTED", STAGE_STARTED(stage_id=5, stage_name="Phase Criticality Analysis", timestamp=asyncio.get_event_loop().time()).model_dump())
    await asyncio.sleep(0.01)
    phase_data = PHASE_CRIT_FOUND(p_crit=0.5, advantage_verdict="Quantum advantage demonstrated")
    await event_bus.publish("PHASE_CRIT_FOUND", phase_data.model_dump())
    await asyncio.sleep(0.01)

    # Stage 6: Final Results
    await event_bus.publish("STAGE_STARTED", STAGE_STARTED(stage_id=6, stage_name="Final Results", timestamp=asyncio.get_event_loop().time()).model_dump())
    await asyncio.sleep(0.01)
    await websocket.send_text(json.dumps({"status": "completed"}))

# Subscribe to events and forward to WebSocket
async def forward_event(event_type: str, event_data: Dict[str, Any], websocket: WebSocket) -> None:
    await websocket.send_text(json.dumps({**{"event_type": event_type}, **event_data}))

# Register event handlers
async def register_event_handlers(websocket: WebSocket) -> None:
    await event_bus.subscribe("STAGE_STARTED", lambda data: forward_event("STAGE_STARTED", data, websocket))
    await event_bus.subscribe("CIRCUIT_COMPILED", lambda data: forward_event("CIRCUIT_COMPILED", data, websocket))
    await event_bus.subscribe("STATEVECTOR_UPDATED", lambda data: forward_event("STATEVECTOR_UPDATED", data, websocket))
    await event_bus.subscribe("SHOTS_ACCUMULATED", lambda data: forward_event("SHOTS_ACCUMULATED", data, websocket))
    await event_bus.subscribe("FRAME_RECONSTRUCTED", lambda data: forward_event("FRAME_RECONSTRUCTED", data, websocket))
    await event_bus.subscribe("PHASE_CRIT_FOUND", lambda data: forward_event("PHASE_CRIT_FOUND", data, websocket))
