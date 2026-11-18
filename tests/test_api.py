import pytest
from fastapi.testclient import TestClient
import api.server as server
from api.server import app
from api.schemas import SimulationRequest
import json

# Disable demo pacing delays so the suite stays fast.
server.PACING_SCALE = 0.0

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "simulator": "quantum_image_processing",
        "version": "1.0.0"
    }

def test_simulation_request_schema():
    valid_request = {
        "resolution": 100,
        "pattern": "test_pattern",
        "encoding": "amplitude",
        "noise_channel": "depolarizing",
        "noise_rate": 0.1,
        "shots": 1000,
        "denoise_method": "threshold",
        "threshold": 0.5
    }
    request = SimulationRequest(**valid_request)
    assert request.resolution == 100
    assert request.pattern == "test_pattern"

    with pytest.raises(ValueError):
        SimulationRequest(resolution="invalid", pattern="test_pattern", encoding="amplitude",
                          noise_channel="depolarizing", noise_rate=0.1, shots=1000,
                          denoise_method="threshold", threshold=0.5)

def test_websocket_simulate():
    with client.websocket_connect("/ws/simulate") as websocket:
        request = {
            "resolution": 100,
            "pattern": "test_pattern",
            "encoding": "amplitude",
            "noise_channel": "depolarizing",
            "noise_rate": 0.1,
            "shots": 1000,
            "denoise_method": "threshold",
            "threshold": 0.5
        }
        websocket.send_text(json.dumps(request))

        # Receive and verify all progressive events until completion
        received_events = []
        while True:
            data = websocket.receive_text()
            msg = json.loads(data)
            if msg.get("status") == "completed":
                break
            assert "event_type" in msg
            received_events.append(msg)

        # Verify we received events from all stages
        assert len(received_events) >= 6
        event_types = [e["event_type"] for e in received_events]
        assert "STAGE_STARTED" in event_types
        assert "CIRCUIT_COMPILED" in event_types
