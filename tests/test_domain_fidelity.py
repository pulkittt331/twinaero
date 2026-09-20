import pytest
from backend.simulator.engine_model import EngineModel
from backend.simulator.fault_injector import FaultInjector
from backend.simulator.wear_simulator import WearSimulator
from backend.digital_twin.twin_model import DigitalTwin
from backend.api import AnalyticalBackend

def test_multi_cylinder_baseline_spread():
    model = EngineModel()
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    state = model.step(1.0, env, {})
    
    # 4 cylinders should be tracked
    assert "cht1" in state and "cht2" in state and "cht3" in state and "cht4" in state
    assert "egt1" in state and "egt2" in state and "egt3" in state and "egt4" in state
    
    # Aggregate CHT should match cylinder average
    avg_cht = (state["cht1"] + state["cht2"] + state["cht3"] + state["cht4"]) / 4.0
    assert abs(state["cht"] - avg_cht) < 1e-3
    
    # Baseline cylinder spread should be low (< 10°C)
    spread = max(state["cht1"], state["cht2"], state["cht3"], state["cht4"]) - min(state["cht1"], state["cht2"], state["cht3"], state["cht4"])
    assert spread < 10.0

def test_single_cylinder_injector_fault():
    sim = WearSimulator(seed=42)
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    
    # Inject fault on cylinder 3
    sim.faults.inject("injector_cyl3", onset_time=0.0, max_severity=1.0, ramp_duration=1.0)
    
    res = None
    for _ in range(10):
        res = sim.step(1.0, env)
        
    obs = res["observed"]
    # Cylinder 3 CHT & EGT should be significantly elevated relative to Cylinder 1
    assert obs["cht3"] > obs["cht1"] + 30.0
    assert obs["egt3"] > obs["egt1"] + 50.0

def test_map_and_altitude_turbo_dynamics():
    model = EngineModel()
    
    # Sea level high throttle
    env_sea = {"throttle": 90, "load": 50, "altitude": 0, "ambient_temp": 25, "injection_timing": 0}
    for _ in range(10):
        s_sea = model.step(1.0, env_sea, {})
        
    # High altitude 15,000 ft high throttle
    model_alt = EngineModel()
    env_alt = {"throttle": 90, "load": 50, "altitude": 15000, "ambient_temp": -5, "injection_timing": 0}
    for _ in range(10):
        s_alt = model_alt.step(1.0, env_alt, {})
        
    # Turbocharger should boost MAP at sea level above ambient (29.92)
    assert s_sea["map"] > 35.0
    # MAP should remain operational at high altitude (> 20.0 inHg) due to turbocharger
    assert s_alt["map"] > 20.0

def test_detonation_knock_vibration_coupling():
    model = EngineModel()
    env = {"throttle": 100, "load": 80, "altitude": 0, "ambient_temp": 40, "injection_timing": 0}
    
    # Inject overboost knock fault
    fault_effects = {"add_knock_index": 50.0}
    state = model.step(1.0, env, fault_effects)
    
    assert state["knock_index"] >= 50.0
    # High knock index must induce elevated structural vibration
    assert state["vibration"] > 8.0
