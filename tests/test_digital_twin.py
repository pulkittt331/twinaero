import pytest
import math
from backend.simulator.simulator import Simulator
from backend.digital_twin.twin_model import DigitalTwin

def get_steady_state(sim, twin, env, steps=120):
    for _ in range(steps):
        res = sim.step(1.0, env)
        twin_res = twin.step(1.0, env, res["observed"])
    return res, twin_res

def test_healthy_small_residuals():
    sim = Simulator(seed=42)
    twin = DigitalTwin()
    env = {"throttle": 80.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    _, twin_res = get_steady_state(sim, twin, env)
    
    for k, v in twin_res["normalized_residuals"].items():
        assert abs(v) < 0.05

def test_throttle_changes_expected():
    twin = DigitalTwin()
    env = {"throttle": 50.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    for _ in range(120): twin.step(1.0, env, {})
    rpm_50 = twin.healthy_engine.state["rpm"]
    ff_50 = twin.healthy_engine.state["fuel_flow"]
    
    env["throttle"] = 100.0
    for _ in range(120): twin.step(1.0, env, {})
    rpm_100 = twin.healthy_engine.state["rpm"]
    ff_100 = twin.healthy_engine.state["fuel_flow"]
    
    assert rpm_100 > rpm_50
    assert ff_100 > ff_50

def test_altitude_changes_expected():
    twin = DigitalTwin()
    env = {"throttle": 80.0, "load": 50.0, "altitude": 0.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    for _ in range(120): twin.step(1.0, env, {})
    rpm_0 = twin.healthy_engine.state["rpm"]
    
    env["altitude"] = 3000.0
    for _ in range(120): twin.step(1.0, env, {})
    rpm_3000 = twin.healthy_engine.state["rpm"]
    
    assert rpm_3000 < rpm_0

def test_ambient_temp_changes_expected():
    twin = DigitalTwin()
    env = {"throttle": 80.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 10.0, "injection_timing": 0.0}
    for _ in range(120): twin.step(1.0, env, {})
    cht_10 = twin.healthy_engine.state["cht"]
    
    env["ambient_temp"] = 40.0
    for _ in range(120): twin.step(1.0, env, {})
    cht_40 = twin.healthy_engine.state["cht"]
    
    assert cht_40 > cht_10

def test_oil_pressure_no_false_anomaly():
    sim = Simulator(seed=42)
    twin = DigitalTwin()
    env = {"throttle": 50.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    res, twin_res = get_steady_state(sim, twin, env)
    
    obs_op = res["observed"]["oil_pressure"]
    assert obs_op < 45.0
    assert abs(twin_res["residuals"]["oil_pressure"]) < 5.0

def test_overheating_residual():
    sim = Simulator(seed=42)
    twin = DigitalTwin()
    env = {"throttle": 80.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    get_steady_state(sim, twin, env, 50)
    
    sim.inject_fault("overheating", max_severity=1.0, ramp_duration=10.0)
    res, twin_res = get_steady_state(sim, twin, env, 50)
    
    assert twin_res["residuals"]["cht"] > 50.0
    assert twin_res["residuals"]["egt"] > 100.0

def test_lubrication_residual():
    sim = Simulator(seed=42)
    twin = DigitalTwin()
    env = {"throttle": 80.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    get_steady_state(sim, twin, env, 50)
    
    sim.inject_fault("lubrication", max_severity=1.0, ramp_duration=10.0)
    res, twin_res = get_steady_state(sim, twin, env, 50)
    
    assert twin_res["residuals"]["oil_pressure"] < -20.0

def test_injector_residual():
    sim = Simulator(seed=42)
    twin = DigitalTwin()
    env = {"throttle": 80.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    get_steady_state(sim, twin, env, 50)
    
    sim.inject_fault("injector", max_severity=1.0, ramp_duration=10.0)
    res, twin_res = get_steady_state(sim, twin, env, 50)
    
    assert abs(twin_res["residuals"]["fuel_flow"]) > 5.0

def test_vibration_residual():
    sim = Simulator(seed=42)
    twin = DigitalTwin()
    env = {"throttle": 80.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    get_steady_state(sim, twin, env, 50)
    
    sim.inject_fault("vibration", max_severity=1.0, ramp_duration=10.0)
    res, twin_res = get_steady_state(sim, twin, env, 50)
    
    assert twin_res["residuals"]["vibration"] > 5.0

def test_no_nan_inf():
    sim = Simulator(seed=42)
    twin = DigitalTwin()
    env = {"throttle": 80.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    res, twin_res = get_steady_state(sim, twin, env, 100)
    
    for k, v in twin_res["expected_state"].items():
        assert not math.isnan(v) and not math.isinf(v)
    for k, v in twin_res["residuals"].items():
        assert not math.isnan(v) and not math.isinf(v)
