import pytest
from fastapi.testclient import TestClient
from backend.cyber_security_engine import CyberSecurityEngine
from backend.api import AnalyticalBackend
from backend.server import app

def test_cyber_security_clean_telemetry():
    cs = CyberSecurityEngine()
    obs = {"egt": 650.0, "altitude": 1000.0, "fuel_flow": 20.0}
    exp = {"egt": 650.0, "altitude": 1000.0, "fuel_flow": 20.0}
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    
    audit = cs.audit_telemetry(obs, exp, env)
    assert audit["status"] == "SECURE_TAMPER_FREE"
    assert audit["is_tampered"] is False
    assert audit["threat_count"] == 0

def test_cyber_security_egt_tampering():
    cs = CyberSecurityEngine()
    cs.simulate_attack("EGT_TAMPERING")
    
    obs = {"egt": 100.0, "altitude": 1000.0, "fuel_flow": 20.0} # physically impossible low EGT at high throttle
    exp = {"egt": 680.0, "altitude": 1000.0, "fuel_flow": 20.0}
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    
    audit = cs.audit_telemetry(obs, exp, env)
    assert audit["is_tampered"] is True
    assert audit["status"] == "MALICIOUS_SPOOFING_DETECTED"
    assert len(audit["threats"]) >= 1
    assert "egt" in audit["compromised_channels"]

def test_cyber_security_gps_spoofing():
    cs = CyberSecurityEngine()
    cs.simulate_attack("GPS_SPOOFING")
    
    obs = {"egt": 650.0, "altitude": 12000.0, "fuel_flow": 20.0}
    exp = {"egt": 650.0, "altitude": 1000.0, "fuel_flow": 20.0}
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    
    audit = cs.audit_telemetry(obs, exp, env)
    assert audit["is_tampered"] is True
    assert "altitude" in audit["compromised_channels"]

def test_cyber_security_api_endpoints():
    client = TestClient(app)
    
    # 1. GET /api/security/status
    res_status = client.get("/api/security/status")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert "status" in data_status
    assert "is_tampered" in data_status
    
    # 2. POST /api/security/simulate-attack
    res_attack = client.post("/api/security/simulate-attack", json={"attack_type": "EGT_TAMPERING"})
    assert res_attack.status_code == 200
    data_attack = res_attack.json()
    assert data_attack["success"] is True
    assert data_attack["active_attack"] == "EGT_TAMPERING"
    
    # 3. GET /api/security/status under attack
    res_status2 = client.get("/api/security/status")
    assert res_status2.status_code == 200
    data_status2 = res_status2.json()
    assert data_status2["is_tampered"] is True
