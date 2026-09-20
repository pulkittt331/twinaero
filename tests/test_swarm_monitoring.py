import pytest
from fastapi.testclient import TestClient
from backend.swarm_manager import SwarmManager
from backend.server import app

def test_swarm_manager_initialization():
    sm = SwarmManager()
    status = sm.get_swarm_status()
    assert status["total_uavs"] == 4
    assert status["active_uav_id"] == "UAV-ALPHA"
    assert "UAV-ALPHA" in status["uavs"]
    assert "UAV-BRAVO" in status["uavs"]
    assert "UAV-CHARLIE" in status["uavs"]
    assert "UAV-DELTA" in status["uavs"]
    assert status["swarm_health_avg"] > 80.0

def test_swarm_select_uav():
    sm = SwarmManager()
    assert sm.select_uav("UAV-BRAVO") is True
    status = sm.get_swarm_status()
    assert status["active_uav_id"] == "UAV-BRAVO"
    assert status["uavs"]["UAV-BRAVO"]["is_active"] is True
    assert status["uavs"]["UAV-ALPHA"]["is_active"] is False

def test_swarm_fault_injection_and_reallocation():
    sm = SwarmManager()
    res = sm.inject_uav_fault("UAV-ALPHA", "lubrication")
    assert res["active_faults_count"] >= 1
    uav_alpha = res["uavs"]["UAV-ALPHA"]
    assert uav_alpha["fault"] == "LUBRICATION"
    assert len(res["reallocation_notices"]) >= 1
    notice = res["reallocation_notices"][0]
    assert notice["from_uav"] == "UAV-ALPHA"

def test_swarm_api_endpoints():
    client = TestClient(app)
    
    # 1. GET /api/swarm/status
    res_status = client.get("/api/swarm/status")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert data_status["total_uavs"] == 4
    
    # 2. POST /api/swarm/select
    res_select = client.post("/api/swarm/select", json={"uav_id": "UAV-CHARLIE"})
    assert res_select.status_code == 200
    data_select = res_select.json()
    assert data_select["active_uav_id"] == "UAV-CHARLIE"
    
    # 3. POST /api/swarm/inject-fault
    res_fault = client.post("/api/swarm/inject-fault", json={"uav_id": "UAV-DELTA", "fault_type": "overheating"})
    assert res_fault.status_code == 200
    data_fault = res_fault.json()
    assert data_fault["uavs"]["UAV-DELTA"]["fault"] == "OVERHEATING"
