import pytest
from fastapi.testclient import TestClient
from backend.server import app

client = TestClient(app)

def test_status_uninitialized():
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "health_index" in data

def test_start_healthy_endpoint():
    res = client.post("/api/start-healthy")
    assert res.status_code == 200
    data = res.json()
    assert data["uninitialized"] == False
    assert data["health_index"] > 80.0

def test_inject_fault_endpoint():
    res = client.post("/api/inject-fault", json={"fault_type": "overheating"})
    assert res.status_code == 200
    data = res.json()
    assert data["current_fault"] == "overheating"

def test_simulate_mission_endpoint():
    client.post("/api/start-healthy")
    res = client.post("/api/simulate-mission", json={"profile": "Nominal"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] == True
    assert "advisory" in data

def test_reset_endpoint():
    res = client.post("/api/reset")
    assert res.status_code == 200
    data = res.json()
    assert data["uninitialized"] == True
