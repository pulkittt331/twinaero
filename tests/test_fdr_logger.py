import pytest
from fastapi.testclient import TestClient
from backend.fdr_logger import FlightDataRecorder
from backend.api import AnalyticalBackend
from backend.server import app

def test_fdr_record_step():
    fdr = FlightDataRecorder()
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    obs = {"egt": 650.0, "cht": 150.0, "rpm": 4800.0, "fuel_flow": 22.0, "altitude": 1000.0}
    exp = {"egt": 650.0, "cht": 150.0}
    adv = {"recommended_throttle_cap": 90}
    
    fdr.record_step(1.0, env, obs, exp, 98.5, "NORMAL", adv)
    assert len(fdr.fdr_buffer) == 1
    frame = fdr.fdr_buffer[0]
    assert frame["step_id"] == 1
    assert frame["flight_time_s"] == 1.0
    assert frame["health_index"] == 98.5

def test_fdr_get_replay_slice():
    fdr = FlightDataRecorder()
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    obs = {"egt": 650.0, "cht": 150.0, "rpm": 4800.0, "fuel_flow": 22.0, "altitude": 1000.0}
    
    for i in range(10):
        fdr.record_step(float(i+1), env, obs, obs, 100.0 - i, "NORMAL", {})
        
    slice_res = fdr.get_replay_slice(2, 6)
    assert slice_res["total_recorded_steps"] == 10
    assert slice_res["slice_count"] == 4
    assert len(slice_res["frames"]) == 4

def test_fdr_post_flight_report():
    fdr = FlightDataRecorder()
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    obs = {"egt": 720.0, "cht": 190.0, "rpm": 5100.0, "fuel_flow": 28.0, "altitude": 1000.0}
    exp = {"egt": 650.0, "cht": 150.0}
    
    fdr.record_step(1.0, env, obs, exp, 45.0, "OVERHEATING", {})
    report = fdr.generate_post_flight_report("UAV-ALPHA")
    
    assert report["uav_id"] == "UAV-ALPHA"
    assert report["minimum_health_index"] == 45.0
    assert "OVERHEATING" in report["diagnosed_faults"]
    assert len(report["maintenance_action_items"]) >= 1

def test_fdr_export_csv():
    fdr = FlightDataRecorder()
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    obs = {"egt": 650.0, "cht": 150.0, "rpm": 4800.0, "fuel_flow": 22.0, "altitude": 1000.0}
    
    fdr.record_step(1.0, env, obs, obs, 100.0, "NORMAL", {})
    csv_out = fdr.export_csv_telemetry()
    assert "step_id" in csv_out
    assert "flight_time_s" in csv_out
    assert "health_index" in csv_out

def test_fdr_api_endpoints():
    client = TestClient(app)
    
    # 1. GET /api/fdr/replay
    res_replay = client.get("/api/fdr/replay")
    assert res_replay.status_code == 200
    data_replay = res_replay.json()
    assert "total_recorded_steps" in data_replay
    
    # 2. GET /api/fdr/report
    res_report = client.get("/api/fdr/report?uav_id=UAV-BRAVO")
    assert res_report.status_code == 200
    data_report = res_report.json()
    assert data_report["uav_id"] == "UAV-BRAVO"
    
    # 3. GET /api/fdr/download-csv
    res_csv = client.get("/api/fdr/download-csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
