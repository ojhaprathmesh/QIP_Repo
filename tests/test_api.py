import pytest
from fastapi.testclient import TestClient
import api.server as server
from api.server import app
from api.schemas import SimulationRequest
import json

# Disable demo pacing delays so the suite stays fast.
server.PACING_SCALE = 0.0

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "endpoints" in data
    assert data["endpoints"]["health"] == "/healthz"

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


@pytest.mark.parametrize("path,key", [
    ("/api/benchmarks/noise-sweep", "experiment"),
    ("/api/benchmarks/denoising", None),
    ("/api/benchmarks/bitflip-study", None),
])
def test_benchmark_endpoints(path, key):
    response = client.get(path)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, (dict, list)) and body
    if key:
        assert key in body


def test_benchmark_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "RESULTS_DIR", tmp_path)
    response = client.get("/api/benchmarks/noise-sweep")
    assert response.status_code == 404
    assert "error" in response.json()


def test_benchmark_invalid_json(monkeypatch, tmp_path):
    (tmp_path / "bitflip_study.json").write_text("{not json")
    monkeypatch.setattr(server, "RESULTS_DIR", tmp_path)
    response = client.get("/api/benchmarks/bitflip-study")
    assert response.status_code == 500
    assert "error" in response.json()


@pytest.mark.parametrize("encoding", ["frqi", "neqr"])
def test_websocket_real_circuit_and_classical_metrics(encoding):
    with client.websocket_connect("/ws/simulate") as websocket:
        websocket.send_text(json.dumps({
            "resolution": 4, "pattern": "checkerboard", "encoding": encoding,
            "noise_channel": "depolarizing", "noise_rate": 0.01, "shots": 100,
            "denoise_method": "threshold", "threshold": 0.5,
        }))
        events = []
        while True:
            msg = json.loads(websocket.receive_text())
            if msg.get("status") == "completed":
                break
            events.append(msg)
    circuits = [e for e in events if e["event_type"] == "CIRCUIT_COMPILED"]
    assert circuits[-1]["qubits"] == (5 if encoding == "frqi" else 12)
    assert circuits[-1]["total_gates"] > 0
    frames = [e for e in events if e["event_type"] == "FRAME_RECONSTRUCTED"]
    cm = frames[-1]["classical_metrics"]
    for name in ("median", "gaussian", "mean"):
        assert f"{name}_psnr" in cm and f"{name}_ssim" in cm
