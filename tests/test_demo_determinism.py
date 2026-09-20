import pytest
from backend.api import AnalyticalBackend
from backend.simulator.wear_simulator import WearSimulator

def run_demo(fault_type, seed=42):
    api = AnalyticalBackend()
    sim = WearSimulator(seed=seed)
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    
    if fault_type != "healthy":
        sim.set_wear(fault_type, 1.0)
    
    detection_time = None
    confirmed_time = None
    
    # Run 50 steps
    for t in range(1, 51):
        r = sim.step(1.0, env)
        api.step(1.0, env, r["observed"], r["true_state"])
        diag = api.get_diagnostic_status()
        
        if api.anomaly_history[-1] and detection_time is None:
            detection_time = t
            
        if diag["confirmed"] and confirmed_time is None:
            confirmed_time = t
            
    final_diag = api.get_diagnostic_status()
    hi = api.get_health_index()
    f_type = final_diag["fault"].lower() if final_diag["fault"] != "NORMAL" else None
    rul = api.get_rul_estimate(f_type, env)
    
    m_nominal = [{"T": 10, "e": {"throttle": 60, "load": 40, "altitude": 2000, "ambient_temp": 15, "injection_timing": 0}}]
    m_agg = [{"T": 10, "e": {"throttle": 100, "load": 80, "altitude": 2000, "ambient_temp": 15, "injection_timing": 0}}]
    
    risk_n, mar_n, ft_n, final_t_n = api.simulate_mission(m_nominal, f_type)
    risk_a, mar_a, ft_a, final_t_a = api.simulate_mission(m_agg, f_type)
    
    return {
        "detection_time": detection_time,
        "confirmed_time": confirmed_time,
        "fault": final_diag["fault"],
        "model_probability": final_diag["model_probability"],
        "hi": hi,
        "rul": rul,
        "risk_n": risk_n,
        "mar_n": mar_n,
        "risk_a": risk_a,
        "mar_a": mar_a
    }

def test_demo_determinism():
    faults = ["healthy", "overheating", "lubrication", "vibration", "injector"]
    
    for f in faults:
        run1 = run_demo(f, seed=100)
        run2 = run_demo(f, seed=100)
        
        assert run1 == run2, f"Determinism failed for {f}"

def test_mission_differentiation_threshold():
    faults = ["overheating", "lubrication"]
    for f in faults:
        run = run_demo(f, seed=200)
        
        mar_n = run["mar_n"]
        mar_a = run["mar_a"]
        
        assert abs(mar_n - mar_a) > 0.005, f"Mission differentiation too small for {f}: nominal={mar_n}, agg={mar_a}"

