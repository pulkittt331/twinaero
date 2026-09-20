import pytest
from backend.api import AnalyticalBackend

def test_state_boundary():
    # Verify that the noisy observed telemetry doesn't leak into the mission simulator true state
    api = AnalyticalBackend()
    
    # Send a noisy observation
    fake_obs = {'rpm': 2500, 'fuel_flow': 20, 'egt': 800, 'cht': 200, 'oil_temp': 100, 'oil_pressure': 50, 'vibration': 2, 'battery_voltage': 14}
    env = {"throttle": 80.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    
    api.step(1.0, env, fake_obs)
    
    current_obs = api.get_current_engine_state(debug=False)
    assert current_obs == fake_obs, "API must return the observed state when requested"
    
def test_time_semantics():
    api = AnalyticalBackend()
    start_time = 100.0
    api.current_time = start_time
    
    mission1 = [
        {"T": 150, "e": {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}},
        {"T": 50,  "e": {"throttle": 90, "load": 60, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}}
    ]
    
    risk, margin, f_t, final_time = api.simulate_mission(mission1, "lubrication")
    mission_duration1 = 200.0
    expected_final_time1 = start_time + mission_duration1
    assert final_time == expected_final_time1, f"Expected {expected_final_time1}, got {final_time}"

    # Test another profile
    mission2 = [
        {"T": 30, "e": {"throttle": 100, "load": 80, "altitude": 0, "ambient_temp": 25, "injection_timing": 0}},
        {"T": 120,  "e": {"throttle": 75, "load": 50, "altitude": 2000, "ambient_temp": 15, "injection_timing": 0}}
    ]
    risk2, margin2, f_t2, final_time2 = api.simulate_mission(mission2, "overheating")
    mission_duration2 = 150.0
    expected_final_time2 = start_time + mission_duration2
    assert final_time2 == expected_final_time2, f"Expected {expected_final_time2}, got {final_time2}"

def test_expected_state():
    api = AnalyticalBackend()
    fake_obs = {'rpm': 2500, 'fuel_flow': 20, 'egt': 800, 'cht': 200, 'oil_temp': 100, 'oil_pressure': 50, 'vibration': 2, 'battery_voltage': 14}
    env = {"throttle": 80.0, "load": 50.0, "altitude": 1000.0, "ambient_temp": 25.0, "injection_timing": 0.0}
    api.step(1.0, env, fake_obs)
    
    exp_state = api.get_expected_state()
    assert exp_state is not None, "Expected state should not be None"
    assert "rpm" in exp_state, "Expected state should contain engine keys"
