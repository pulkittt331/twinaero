import pytest
import numpy as np
import copy
from backend.api import AnalyticalBackend, keys
from backend.simulator.wear_simulator import WearSimulator
from backend.models.degradation_observer_config import OBSERVER_CONFIG

def get_base_env():
    return {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}

def test_two_layer_risk_semantics():
    api = AnalyticalBackend()
    # Fill history to avoid 0s
    for _ in range(10):
        obs = {k: 100.0 for k in keys}
        api.step(1.0, get_base_env(), obs)
        
    mission = [{"T": 10, "e": get_base_env()}]
    
    # Case B: Current GREEN, Future GREEN
    api.obs_history = [{k: 100.0 for k in keys} for _ in range(10)]
    api.obs_history[-1]["cht"] = 100.0
    risk, _, _, _ = api.simulate_mission(mission, "overheating")
    assert "Current Risk: GREEN" in risk
    
    # Case A: Current RED, Future GREEN
    # If CHT is 300, normalized margin is (270 - 300)/70 = -30/70 < 0 -> RED
    # We force the estimated state to be 300 for CHT by manipulating obs_history
    api.obs_history = [{k: 300.0 if k == "cht" else 100.0 for k in keys} for _ in range(10)]
    # But we want future to be GREEN. Future sim uses est_sev. 
    # Let's set preproc_stats such that Z is low, so est_sev=0
    # Actually, future sim steps forward. If est_sev=0, CHT might drop back to nominal (around 200).
    api.preproc_stats = {k: {"mean": 100.0, "std": 1.0} for k in keys}
    api.res_history.append({f"res_{k}": 0.0 for k in keys}) # force Z=0 -> est_sev=0
    
    risk, f_margin, _, _ = api.simulate_mission(mission, "overheating")
    assert "Current Risk: RED" in risk
    assert "Future Mission Risk" in risk
    # Future will likely be GREEN because est_sev is 0 and throttle is 80 (nominal CHT < 270)
    
    # Advisory test
    adv = api.get_advisory(mission, "overheating")
    assert "CURRENT RED: Prototype-defined simulated criterion crossed" in adv

def test_oracle_free_handoff():
    api = AnalyticalBackend()
    env = get_base_env()
    
    # Run a few steps
    sim = WearSimulator(seed=42)
    sim.set_wear("vibration", 0.5)
    for _ in range(10):
        r = sim.step(1.0, env)
        api.step(1.0, env, r["observed"], r["true_state"])
        
    mission = [{"T": 10, "e": env}]
    risk1, margin1, fail1, t1 = api.simulate_mission(mission, "vibration")
    
    # Now silently change true_state_debug in the API
    api.last_true_state_debug = {k: 9999.9 for k in keys}
    
    # Run simulation again
    risk2, margin2, fail2, t2 = api.simulate_mission(mission, "vibration")
    
    # Must be exactly identical
    assert risk1 == risk2
    assert margin1 == margin2
    assert fail1 == fail2
    assert t1 == t2
    
def test_calibrated_observer_bounds():
    from backend.api import estimate_degradation
    for fault in ["overheating", "lubrication", "vibration"]:
        config = OBSERVER_CONFIG[fault]
        
        # extreme low Z
        z_low = {k: -1000.0 for k in keys}
        sev_low = estimate_degradation(fault, z_low)
        assert sev_low == config["clip_min"]
        
        # extreme high Z
        z_high = {k: 1000.0 for k in keys}
        sev_high = estimate_degradation(fault, z_high)
        assert sev_high == config["clip_max"]
        
        # Monotonicity
        z_mid1 = {k: 10.0 for k in keys}
        z_mid2 = {k: 20.0 for k in keys}
        sev1 = estimate_degradation(fault, z_mid1)
        sev2 = estimate_degradation(fault, z_mid2)
        if config["slope"] > 0:
            assert sev2 >= sev1
        else:
            assert sev2 <= sev1

def test_temporal_confirmation_logic():
    api = AnalyticalBackend()
    # Mock preproc and iso to easily control anomaly status
    api.preproc_stats = {k: {"mean": 0.0, "std": 1.0} for k in keys}
    class MockIso:
        def __init__(self): self.pred = 1 # 1=Normal, -1=Anomaly
        def predict(self, X): return [self.pred]
    class MockRF:
        def __init__(self): self.classes_ = np.array(["normal", "vibration", "overheating"])
        def predict_proba(self, X): return [[0.1, 0.8, 0.1]]
        
    api.iso = MockIso()
    api.rf_fault = MockRF()
    
    env = get_base_env()
    obs = {k: 0.0 for k in keys}
    
    # 1. Normal
    api.step(1.0, env, obs)
    stat = api.get_diagnostic_status()
    assert stat["confirmed"] == False
    assert stat["anomaly"] == "NO"
    
    # 2. One Anomaly
    api.iso.pred = -1
    api.step(1.0, env, obs)
    stat = api.get_diagnostic_status()
    assert stat["confirmed"] == False
    assert stat["anomaly"] == "NO" # Because not confirmed! Wait, the implementation says if not confirmed -> NO
    
    # 3. Two Anomalies
    api.step(1.0, env, obs)
    stat = api.get_diagnostic_status()
    assert stat["confirmed"] == False
    
    # 4. Three Anomalies
    api.step(1.0, env, obs)
    stat = api.get_diagnostic_status()
    assert stat["confirmed"] == True
    assert stat["anomaly"] == "YES"
    assert stat["fault"] == "VIBRATION"
    
    # 5. Reset to Normal
    api.iso.pred = 1
    api.step(1.0, env, obs)
    stat = api.get_diagnostic_status()
    assert stat["confirmed"] == False

def test_frozen_baseline():
    api = AnalyticalBackend()
    assert api.preproc_stats is not None
    orig_stats = copy.deepcopy(api.preproc_stats)
    
    sim = WearSimulator()
    sim.set_wear("overheating", 1.0)
    for _ in range(10):
        r = sim.step(1.0, get_base_env())
        api.step(1.0, get_base_env(), r["observed"], r["true_state"])
        
    assert api.preproc_stats == orig_stats

def test_rul_regression():
    api = AnalyticalBackend()
    # Just run it to ensure no exceptions and unsupported stays unsupported
    rul = api.get_rul_estimate("injector", get_base_env())
    assert rul is None
    
    # for supported, it needs enough history
    for _ in range(5):
        api.res_history.append({f"res_{k}": 0.0 for k in keys})
    rul2 = api.get_rul_estimate("overheating", get_base_env())
    assert rul2 is not None

