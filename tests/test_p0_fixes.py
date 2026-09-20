import pytest
import numpy as np
import pandas as pd
from backend.api import AnalyticalBackend
from backend.simulator.wear_simulator import WearSimulator
from backend.model_registry import registry, keys

def test_Z_train_inference_equivalence():
    api = AnalyticalBackend()
    fake_res = {f"res_{k}": 10.0 for k in keys}
    
    z_train = []
    for k in keys:
        rm = registry.preproc_stats[k]["mean"]
        rs = registry.preproc_stats[k]["std"]
        z_train.append((10.0 - rm) / rs)
        
    api.res_history.append(fake_res)
    z_infer = []
    for k in keys:
        rm = api.preproc_stats[k]["mean"]
        rs = api.preproc_stats[k]["std"]
        z_infer.append((api.res_history[-1][f"res_{k}"] - rm) / rs)
        
    np.testing.assert_allclose(z_train, z_infer)
    assert not np.isnan(z_train).any()

def test_temporal_confirmation():
    api = AnalyticalBackend()
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    sim = WearSimulator(seed=42)
    
    sim.set_wear(None, 0.0)
    res = sim.step(1.0, env)
    api.step(1.0, env, res["observed"], res["true_state"])
    diag = api.get_diagnostic_status()
    assert diag["confirmed"] == False
    assert diag["anomaly"] == "NO"
    
    sim.set_wear("overheating", 0.8)
    
    for _ in range(50):
        res = sim.step(1.0, env)
        api.step(1.0, env, res["observed"], res["true_state"])
        diag = api.get_diagnostic_status()
        if api.anomaly_history[-1] == True:
            break
            
    assert diag["confirmed"] == False
    
    res = sim.step(1.0, env)
    api.step(1.0, env, res["observed"], res["true_state"])
    diag = api.get_diagnostic_status()
    assert diag["confirmed"] == False
    
    res = sim.step(1.0, env)
    api.step(1.0, env, res["observed"], res["true_state"])
    diag = api.get_diagnostic_status()
    assert diag["confirmed"] == True
    assert diag["anomaly"] == "YES"

def test_injector_demo_path():
    api = AnalyticalBackend()
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    sim = WearSimulator(seed=42)
    sim.set_wear("injector", 0.8)
    
    diag = None
    for _ in range(50):
        res = sim.step(1.0, env)
        api.step(1.0, env, res["observed"], res["true_state"])
        diag = api.get_diagnostic_status()
        
    assert diag["anomaly"] == "YES"
    assert diag["confirmed"] == True
    assert diag["fault"] == "INJECTOR"

def test_no_healthy_fallback():
    api = AnalyticalBackend()
    mission = [{"T": 20, "e": {"throttle": 85, "load": 50, "altitude": 0, "ambient_temp": 25, "injection_timing": 0}}]
    risk, margin, f_t, final_t = api.simulate_mission(mission, None)
    assert "Future Mission Risk: GREEN" in risk

def test_mission_differentiation():
    api = AnalyticalBackend()
    api.current_time = 100.0
    
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    sim = WearSimulator(seed=101)
    sim.set_wear("overheating", 0.6)
    for _ in range(10):
        res = sim.step(1.0, env)
        api.step(1.0, env, res["observed"], res["true_state"])
        
    m_nominal = [{"T": 100, "e": {"throttle": 60, "load": 40, "altitude": 2000, "ambient_temp": 15, "injection_timing": 0}}]
    m_agg = [{"T": 100, "e": {"throttle": 100, "load": 80, "altitude": 2000, "ambient_temp": 15, "injection_timing": 0}}]
    
    risk_n, mar_n, ft_n, _ = api.simulate_mission(m_nominal, "overheating")
    risk_a, mar_a, ft_a, _ = api.simulate_mission(m_agg, "overheating")
    
    assert mar_n != mar_a, "Mission profiles must produce different safety margins from the same starting state"
    assert mar_n > mar_a, "Aggressive mission should have lower margin"

def test_end_to_end_demo():
    faults = ["overheating", "lubrication", "vibration", "injector"]
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    
    for f in faults:
        api = AnalyticalBackend()
        sim = WearSimulator(seed=42)
        
        # Healthy warmup
        for _ in range(25):
            res = sim.step(1.0, env)
            api.step(1.0, env, res["observed"], res["true_state"])
        diag = api.get_diagnostic_status()
        assert diag["anomaly"] == "NO"
        
        # Inject
        sim.set_wear(f, 1.0)
        for _ in range(50):
            res = sim.step(1.0, env)
            api.step(1.0, env, res["observed"], res["true_state"])
            diag = api.get_diagnostic_status()
            if diag["anomaly"] == "YES" and diag["fault"] == f.upper():
                break
                
        assert diag["anomaly"] == "YES"
        assert diag["confirmed"] == True
        assert diag["fault"] == f.upper()
        
        hi = api.get_health_index()
        assert hi < 100.0
        
        rul = api.get_rul_estimate(f, env)
        assert rul is not None or f == "injector"
        
        m_nominal = [{"T": 10, "e": {"throttle": 60, "load": 40, "altitude": 2000, "ambient_temp": 15, "injection_timing": 0}}]
        m_agg = [{"T": 10, "e": {"throttle": 100, "load": 80, "altitude": 2000, "ambient_temp": 15, "injection_timing": 0}}]
        
        risk_n, mar_n, ft_n, _ = api.simulate_mission(m_nominal, f)
        risk_a, mar_a, ft_a, _ = api.simulate_mission(m_agg, f)
        
        if f != "injector":
            assert mar_n != mar_a
