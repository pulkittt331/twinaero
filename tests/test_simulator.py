import pytest
from backend.simulator.simulator import Simulator
from backend.simulator.config import PHYSICAL_BOUNDS, ENVELOPES

def test_healthy_operating_point():
    sim = Simulator(seed=42)
    env = {"throttle": 80.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    for _ in range(120):
        sim.step(1.0, env)
        
    obs = sim.sensors.get_observed(sim.engine.state)
    
    assert ENVELOPES["rpm"]["normal"][0] <= obs["rpm"] <= ENVELOPES["rpm"]["normal"][1]
    assert ENVELOPES["fuel_flow"]["normal"][0] <= obs["fuel_flow"] <= ENVELOPES["fuel_flow"]["normal"][1]
    assert ENVELOPES["egt"]["normal"][0] <= obs["egt"] <= ENVELOPES["egt"]["normal"][1]
    assert ENVELOPES["cht"]["normal"][0] <= obs["cht"] <= ENVELOPES["cht"]["normal"][1]
    assert ENVELOPES["oil_temp"]["normal"][0] <= obs["oil_temp"] <= ENVELOPES["oil_temp"]["normal"][1]
    assert ENVELOPES["oil_pressure"]["normal"][0] <= obs["oil_pressure"] <= ENVELOPES["oil_pressure"]["normal"][1]
    assert ENVELOPES["vibration"]["normal"][0] <= obs["vibration"] <= ENVELOPES["vibration"]["normal"][1]
    assert ENVELOPES["battery_voltage"]["normal"][0] <= obs["battery_voltage"] <= ENVELOPES["battery_voltage"]["normal"][1]

def test_steady_state_convergence():
    sim = Simulator(seed=42)
    env = {"throttle": 80.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    for _ in range(120): sim.step(1.0, env)
    
    rpms = []
    ffs = []
    for _ in range(10):
        res = sim.step(1.0, env)
        rpms.append(res["true_state"]["rpm"])
        ffs.append(res["true_state"]["fuel_flow"])
    
    assert max(rpms) - min(rpms) < 2.0
    assert max(ffs) - min(ffs) < 0.5

def test_exponential_integration_dt_independence():
    env = {"throttle": 80.0, "load": 50.0, "altitude": 0.0, "ambient_temp": 20.0}
    sim1 = Simulator(seed=42)
    for _ in range(10): sim1.step(1.0, env)
    sim2 = Simulator(seed=42)
    for _ in range(100): sim2.step(0.1, env)
    assert abs(sim1.engine.state["rpm"] - sim2.engine.state["rpm"]) < 50.0

def test_throttle_step():
    sim = Simulator(seed=42)
    env = {"throttle": 20.0, "load": 50.0, "altitude": 0.0, "ambient_temp": 20.0}
    for _ in range(50): sim.step(1.0, env)
    rpm_low = sim.engine.state["rpm"]
    env["throttle"] = 100.0
    for _ in range(50): sim.step(1.0, env)
    rpm_high = sim.engine.state["rpm"]
    assert rpm_high > rpm_low + 1000

def test_thermal_lag_order():
    sim = Simulator(seed=42)
    env = {"throttle": 100.0, "load": 50.0, "altitude": 0.0, "ambient_temp": 20.0}
    for _ in range(10): sim.step(1.0, env)
    egt_progress = (sim.engine.state["egt"] - 20) / (PHYSICAL_BOUNDS["egt"][1] - 20)
    cht_progress = (sim.engine.state["cht"] - 20) / (PHYSICAL_BOUNDS["cht"][1] - 20)
    ot_progress = (sim.engine.state["oil_temp"] - 20) / (PHYSICAL_BOUNDS["oil_temp"][1] - 20)
    assert egt_progress > cht_progress > ot_progress

def test_fault_gradual_onset_and_recovery():
    sim = Simulator(seed=42)
    env = {"throttle": 80.0, "load": 50.0, "altitude": 0.0, "ambient_temp": 20.0}
    for _ in range(50): sim.step(1.0, env)
    op_normal = sim.engine.state["oil_pressure"]
    sim.inject_fault("lubrication", max_severity=1.0, ramp_duration=10.0)
    sim.step(2.0, env)
    op_early = sim.engine.state["oil_pressure"]
    sim.step(10.0, env)
    op_full = sim.engine.state["oil_pressure"]
    assert op_normal > op_early > op_full
    sim.remove_fault("lubrication")
    sim.step(5.0, env)
    op_recovered = sim.engine.state["oil_pressure"]
    assert op_recovered > op_full

def test_no_impossible_values():
    sim = Simulator(seed=42)
    env = {"throttle": 100.0, "load": 0.0, "altitude": 10000.0, "ambient_temp": 50.0}
    sim.inject_fault("overheating", max_severity=1.0, ramp_duration=1.0)
    sim.inject_fault("lubrication", max_severity=1.0, ramp_duration=1.0)
    sim.inject_fault("injector", max_severity=1.0, ramp_duration=1.0)
    for _ in range(100):
        res = sim.step(1.0, env)
        assert res["true_state"]["fuel_flow"] >= 0.0
        for k, v in res["true_state"].items():
            assert PHYSICAL_BOUNDS[k][0] <= v <= PHYSICAL_BOUNDS[k][1]

from backend.simulator.utils import get_envelope
from backend.simulator.config import SENSOR_BOUNDS

def test_envelope_boundaries():
    # Test strict boundaries for a normal/warning/critical param
    assert get_envelope("cht", 100) == "NORMAL"
    assert get_envelope("cht", 180) == "NORMAL"
    assert get_envelope("cht", 180.1) == "WARNING"
    assert get_envelope("cht", 220) == "WARNING"
    assert get_envelope("cht", 220.1) == "CRITICAL"
    assert get_envelope("cht", 300) == "CRITICAL"
    assert get_envelope("cht", 301) == "OUTSIDE HEALTH ENVELOPE / INSIDE SIMULATOR BOUND"
    assert get_envelope("cht", 99) == "OUTSIDE HEALTH ENVELOPE / INSIDE SIMULATOR BOUND"

    # Test strict boundaries for a param with _low and _high
    assert get_envelope("oil_pressure", 29.9) == "CRITICAL_LOW"
    assert get_envelope("oil_pressure", 30.0) == "WARNING_LOW"
    assert get_envelope("oil_pressure", 44.9) == "WARNING_LOW"
    assert get_envelope("oil_pressure", 45.0) == "NORMAL"
    assert get_envelope("oil_pressure", 80.0) == "NORMAL"
    assert get_envelope("oil_pressure", 80.1) == "WARNING_HIGH"
    assert get_envelope("oil_pressure", 95.0) == "WARNING_HIGH"
    assert get_envelope("oil_pressure", 95.1) == "CRITICAL_HIGH"
    assert get_envelope("oil_pressure", 120.0) == "CRITICAL_HIGH"
    assert get_envelope("oil_pressure", 120.1) == "OUTSIDE HEALTH ENVELOPE / INSIDE SIMULATOR BOUND"
    assert get_envelope("oil_pressure", -1) == "OUTSIDE HEALTH ENVELOPE / INSIDE SIMULATOR BOUND"

def test_sensor_bounds_stress():
    sim = Simulator(seed=42)
    env = {"throttle": 100.0, "load": 100.0, "altitude": 10000.0, "ambient_temp": 50.0}
    
    # Inject multiple severe faults simultaneously to push boundaries
    sim.inject_fault("overheating", max_severity=1.0, ramp_duration=1.0)
    sim.inject_fault("lubrication", max_severity=1.0, ramp_duration=1.0)
    sim.inject_fault("injector", max_severity=1.0, ramp_duration=1.0)
    sim.inject_fault("vibration", max_severity=1.0, ramp_duration=1.0)
    
    for _ in range(150):
        res = sim.step(1.0, env)
        obs = res["observed"]
        true = res["true_state"]
        
        for k in SENSOR_BOUNDS:
            assert SENSOR_BOUNDS[k][0] <= obs[k] <= SENSOR_BOUNDS[k][1]
            assert PHYSICAL_BOUNDS[k][0] <= true[k] <= PHYSICAL_BOUNDS[k][1]
