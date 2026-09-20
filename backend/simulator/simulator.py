from .engine_model import EngineModel
from .fault_injector import FaultInjector
from .sensor_model import SensorModel

class Simulator:
    def __init__(self, seed=42):
        self.engine = EngineModel()
        self.faults = FaultInjector()
        self.sensors = SensorModel(seed=seed)
        self.time = 0.0
        
    def step(self, dt, env):
        self.time += dt
        fault_effects = self.faults.get_fault_effects(self.engine.state, self.time, dt)
        true_state = self.engine.step(dt, env, fault_effects)
        observed = self.sensors.get_observed(true_state)
        
        fault_metadata = {k: v["active"] for k, v in self.faults.active_faults.items()}
        
        return {
            "time": self.time,
            "true_state": true_state,
            "observed": observed,
            "faults": fault_metadata
        }
        
    def inject_fault(self, fault_type, max_severity=1.0, ramp_duration=10.0):
        self.faults.inject(fault_type, self.time, max_severity, ramp_duration)
        
    def remove_fault(self, fault_type):
        self.faults.remove(fault_type, self.time)
