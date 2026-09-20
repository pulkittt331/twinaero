import pytest
from backend.api import AnalyticalBackend
import pandas as pd

def test_A_healthy_end_to_end():
    api = AnalyticalBackend()
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    from backend.simulator.simulator import Simulator
    sim = Simulator(seed=42)
    for _ in range(50):
        r = sim.step(1.0, env)
        api.step(1.0, env, r["observed"], r["true_state"])
        diag = api.get_diagnostic_status()
    assert diag["anomaly"] == "NO"
    assert diag["fault"] == "NORMAL"
    assert api.get_health_index() > 90

def test_B_fault_injection_flow():
    from backend.simulator.wear_simulator import WearSimulator
    api = AnalyticalBackend()
    sim = WearSimulator(seed=42)
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    sim.set_wear("lubrication", 0.6)
    for _ in range(50):
        r = sim.step(1.0, env)
        api.step(1.0, env, r["observed"], r["true_state"])
        diag = api.get_diagnostic_status()
    assert diag["anomaly"] == "YES"
    assert diag["fault"] == "LUBRICATION"
    assert api.get_health_index() < 80

def test_C_expected_vs_observed():
    api = AnalyticalBackend()
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    obs = api.twin.healthy_engine.step(1.0, env, {})
    api.step(1.0, env, obs)
    exp = api.get_expected_state()
    assert exp is not None
    assert "rpm" in exp

def test_D_residual_generation():
    api = AnalyticalBackend()
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    obs = api.twin.healthy_engine.step(1.0, env, {})
    api.step(1.0, env, obs)
    res = api.get_residuals()
    assert "res_rpm" in res

def test_E_health_index():
    api = AnalyticalBackend()
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    for _ in range(25):
        obs = api.twin.healthy_engine.step(1.0, env, {})
        api.step(1.0, env, obs)
    hi = api.get_health_index()
    assert 0 <= hi <= 100

def test_F_mission_simulation():
    api = AnalyticalBackend()
    mission = [{"T": 20, "e": {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}}]
    risk, margin, fail_t, fin_t = api.simulate_mission(mission, "lubrication")
    assert "Future Mission Risk:" in risk

def test_G_mission_duration():
    api = AnalyticalBackend()
    start_t = 50.0
    api.current_time = start_t
    mission = [{"T": 20, "e": {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}}]
    _, _, _, fin_t = api.simulate_mission(mission, "lubrication")
    assert fin_t == start_t + 20

def test_H_mission_risk():
    api = AnalyticalBackend()
    mission = [{"T": 20, "e": {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}}]
    risk = api.get_mission_risk(mission, "lubrication")
    assert "Future Mission Risk:" in risk

def test_I_reset():
    api1 = AnalyticalBackend()
    api1.current_time = 100
    api2 = AnalyticalBackend()
    assert api2.current_time == 0

def test_J_no_hidden_true_state():
    api = AnalyticalBackend()
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    fake_true = {k: 9999 for k in ['rpm', 'fuel_flow', 'egt', 'cht', 'oil_temp', 'oil_pressure', 'vibration', 'battery_voltage']}
    fake_obs = {k: 1111 for k in ['rpm', 'fuel_flow', 'egt', 'cht', 'oil_temp', 'oil_pressure', 'vibration', 'battery_voltage']}
    api.step(1.0, env, fake_obs, fake_true)
    assert api.get_current_engine_state(debug=False)["rpm"] == 1111

def test_K_deterministic_demo_seed():
    from backend.simulator.wear_simulator import WearSimulator
    s1 = WearSimulator(seed=42)
    s2 = WearSimulator(seed=42)
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    assert s1.step(1.0, env)["true_state"]["rpm"] == s2.step(1.0, env)["true_state"]["rpm"]

