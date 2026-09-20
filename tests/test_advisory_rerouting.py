import pytest
from backend.advisory_engine import AdvisoryEngine
from backend.api import AnalyticalBackend
from backend.simulator.wear_simulator import WearSimulator

def test_glide_footprint_calculation():
    # At 10,000 ft altitude with nominal engine health (degradation = 0.0)
    footprint = AdvisoryEngine.calculate_glide_footprint(10000.0, 0.0)
    assert footprint["pure_glide_nm"] > 15.0
    assert footprint["powered_glide_nm"] > footprint["pure_glide_nm"]
    assert footprint["glide_km"] > 30.0

def test_diversion_airfield_evaluation():
    airfields = AdvisoryEngine.evaluate_diversion_airfields(15000.0, 100.0, "OVERHEATING", 0.3)
    assert len(airfields) == 4
    
    statuses = [af["status"] for af in airfields]
    assert "REACHABLE" in statuses
    
    for af in airfields:
        assert "dist_nm" in af
        assert "ete_min" in af
        assert "recommended_throttle" in af
        assert af["recommended_throttle"] == 55

def test_mavlink_statustext_formatting():
    diag_nominal = {"anomaly": "NO", "fault": "NORMAL", "confirmed": False}
    adv_data = {"recommended_throttle_cap": 100, "glide_footprint": {"powered_glide_nm": 35.0}, "airfields": []}
    
    text_nom = AdvisoryEngine.format_mavlink_statustext(diag_nominal, adv_data)
    assert "[MAV_SEVERITY_INFO]" in text_nom
    
    diag_fault = {"anomaly": "YES", "fault": "LUBRICATION", "confirmed": True}
    adv_data_fault = {
        "recommended_throttle_cap": 45,
        "glide_footprint": {"powered_glide_nm": 20.0},
        "airfields": [{"name": "ATR Challakere", "status": "REACHABLE"}]
    }
    text_fault = AdvisoryEngine.format_mavlink_statustext(diag_fault, adv_data_fault)
    assert "[MAV_SEVERITY_ALERT]" in text_fault
    assert "CRITICAL LUBRICATION FAULT" in text_fault
    assert "CAP THROTTLE AT 45%" in text_fault

def test_api_emergency_advisory_and_what_if():
    api = AnalyticalBackend()
    env = {"throttle": 80, "load": 50, "altitude": 12000, "ambient_temp": 25, "injection_timing": 0}
    sim = WearSimulator(seed=42)
    sim.set_wear("overheating", 0.8)
    
    for _ in range(25):
        res = sim.step(1.0, env)
        api.step(1.0, env, res["observed"], res["true_state"])
        
    advisory = api.get_emergency_advisory(env)
    assert "glide_footprint" in advisory
    assert "airfields" in advisory
    assert advisory["recommended_throttle_cap"] == 55
    assert "mavlink_statustext" in advisory
    
    what_if = api.simulate_what_if_trajectory(throttle_cap=55.0, target_altitude=10000.0, duration_sec=60)
    assert what_if["throttle_cap"] == 55.0
    assert "safety_margin" in what_if
