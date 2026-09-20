from backend.simulator.engine_model import EngineModel
from backend.simulator.config import PHYSICAL_BOUNDS

class DigitalTwin:
    def __init__(self, ambient_temp=25.0):
        # The twin maintains its own healthy engine model
        self.healthy_engine = EngineModel(ambient_temp=ambient_temp)
        
    def step(self, dt, env, observed_telemetry):
        # Step the healthy engine model without any faults
        expected_state = self.healthy_engine.step(dt, env, fault_effects={})
        
        residuals = {}
        normalized_residuals = {}
        
        for key in expected_state:
            if key in observed_telemetry:
                obs = observed_telemetry[key]
                exp = expected_state[key]
                res = obs - exp
                residuals[key] = res
                
                vmin, vmax = PHYSICAL_BOUNDS[key]
                span = vmax - vmin
                if span > 0:
                    normalized_residuals[key] = res / span
                else:
                    normalized_residuals[key] = 0.0
                    
        return {
            "expected_state": expected_state,
            "residuals": residuals,
            "normalized_residuals": normalized_residuals
        }
