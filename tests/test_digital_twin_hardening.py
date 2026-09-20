import pytest
from backend.simulator.simulator import Simulator
from backend.digital_twin.twin_model import DigitalTwin

def test_twin_independence():
    sim = Simulator()
    twin = DigitalTwin()
    env = {"throttle": 80.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    
    sim.step(1.0, env)
    twin.step(1.0, env, sim.sensors.get_observed(sim.engine.state))
    
    sim.engine.state["rpm"] = 9999.0
    assert twin.healthy_engine.state["rpm"] != 9999.0

def test_transient_residuals_controlled():
    sim = Simulator(seed=42)
    twin = DigitalTwin()
    env = {"throttle": 100.0, "load": 50.0, "altitude": 0.0, "ambient_temp": 20.0, "injection_timing": 0.0}
    
    for _ in range(20):
        res = sim.step(1.0, env)
        twin_res = twin.step(1.0, env, res["observed"])
        assert abs(twin_res["residuals"]["rpm"]) < 50.0

    env["throttle"] = 50.0
    for _ in range(20):
        res = sim.step(1.0, env)
        twin_res = twin.step(1.0, env, res["observed"])
        assert abs(twin_res["residuals"]["rpm"]) < 50.0

def test_multi_operating_point_healthy():
    scenarios = [
        {"throttle": 30.0, "load": 30.0, "altitude": 0.0, "ambient_temp": 20.0},
        {"throttle": 100.0, "load": 80.0, "altitude": 3000.0, "ambient_temp": 40.0},
    ]
    for env in scenarios:
        env["injection_timing"] = 0.0
        sim = Simulator(seed=42)
        twin = DigitalTwin()
        for _ in range(50):
            res = sim.step(1.0, env)
            twin_res = twin.step(1.0, env, res["observed"])
            assert abs(twin_res["residuals"]["rpm"]) < 50.0
            assert abs(twin_res["residuals"]["oil_pressure"]) < 5.0

def test_data_integrity():
    sim = Simulator()
    twin = DigitalTwin()
    env = {"throttle": 80.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    
    sim.inject_fault("overheating", 1.0, 10.0)
    for _ in range(10):
        res = sim.step(1.0, env)
        twin.step(1.0, env, res["observed"])
        
    assert twin.healthy_engine.state["cht"] < 200.0
