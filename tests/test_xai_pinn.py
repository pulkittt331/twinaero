import pytest
import numpy as np
from backend.xai_engine import XAIEngine
from backend.api import AnalyticalBackend, keys
from backend.simulator.engine_model import EngineModel
from backend.simulator.wear_simulator import WearSimulator

def test_xai_feature_attribution_normalization():
    z_scores = {k: 0.0 for k in keys}
    z_scores["cht"] = 3.5
    z_scores["egt"] = 2.0
    
    attr = XAIEngine.compute_feature_attribution(z_scores)
    assert isinstance(attr, dict)
    assert len(attr) == len(keys)
    
    # Total percentage sum should equal ~100%
    total_pct = sum(attr.values())
    assert abs(total_pct - 100.0) < 1.0
    
    # CHT should have highest attribution weight due to z=3.5
    top_feature = list(attr.keys())[0]
    assert top_feature == "cht"
    assert attr["cht"] > attr["egt"]

def test_rul_confidence_interval_computation():
    api = AnalyticalBackend()
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    sim = WearSimulator(seed=42)
    sim.set_wear("overheating", 0.8)
    
    for _ in range(25):
        res = sim.step(1.0, env)
        api.step(1.0, env, res["observed"], res["true_state"])
        
    ci = api.get_rul_confidence_interval("overheating", env)
    assert ci is not None
    assert "mean" in ci
    assert "std_dev" in ci
    assert "lower_95" in ci
    assert "upper_95" in ci
    assert ci["lower_95"] <= ci["mean"] <= ci["upper_95"]

def test_pinn_energy_balance_calculation():
    engine = EngineModel()
    env = {"throttle": 80.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0}
    
    # Warmup steps for RPM and thermal inertia to settle
    for _ in range(15):
        state = engine.step(1.0, env, fault_effects={})
    
    assert "energy_balance_error" in state
    assert "thermal_efficiency" in state
    assert 0.0 <= state["energy_balance_error"] <= 100.0
    assert 10.0 <= state["thermal_efficiency"] <= 60.0
