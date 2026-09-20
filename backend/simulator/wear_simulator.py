import math
from .simulator import Simulator

class WearSimulator(Simulator):
    def __init__(self, seed=42):
        super().__init__(seed)
        self.wear_state = {"type": None, "severity": 0.0}
        
    def set_wear(self, wear_type, severity):
        self.wear_state = {"type": wear_type, "severity": severity}
        
    def step(self, dt, env):
        self.time += dt
        fault_effects = self.faults.get_fault_effects(self.engine.state, self.time, dt)
        wear_effects = {
            "target_rpm_mod": 0.0, "target_ff_mod": 0.0, "target_egt_mod": 0.0, 
            "target_cht_mod": 0.0, "target_oil_temp_mod": 0.0,
            "mult_oil_pressure": 1.0, "add_vibration": 0.0
        }
        w_type, sev = self.wear_state["type"], self.wear_state["severity"]
        if sev > 0:
            if w_type == "overheating":
                wear_effects["target_cht_mod"] += sev * 150.0
                wear_effects["target_egt_mod"] += sev * 200.0
            elif w_type == "lubrication":
                wear_effects["mult_oil_pressure"] -= sev * 0.8
                wear_effects["target_oil_temp_mod"] += sev * 80.0
                wear_effects["add_vibration"] += sev * 2.0
            elif w_type == "vibration":
                wear_effects["add_vibration"] += sev * 15.0
            elif w_type == "injector":
                bias = sev * 15.0
                oscillation = sev * 10.0 * math.sin(self.time * 2.0)
                wear_effects["target_ff_mod"] += bias + oscillation
                wear_effects["target_rpm_mod"] -= sev * 200.0 * math.sin(self.time * 2.0)
                wear_effects["target_egt_mod"] += sev * 100.0 * math.cos(self.time * 2.0)
                
        merged = {}
        all_keys = set(fault_effects.keys()) | set(wear_effects.keys())
        for k in all_keys:
            if k == "mult_oil_pressure":
                merged[k] = fault_effects.get(k, 1.0) * wear_effects.get(k, 1.0)
            elif k in ["cht_cyl_mods", "egt_cyl_mods"]:
                f_arr = fault_effects.get(k, [0.0, 0.0, 0.0, 0.0])
                w_arr = wear_effects.get(k, [0.0, 0.0, 0.0, 0.0])
                merged[k] = [f + w for f, w in zip(f_arr, w_arr)]
            else:
                merged[k] = fault_effects.get(k, 0.0) + wear_effects.get(k, 0.0)
                
        true_state = self.engine.step(dt, env, merged)
        return {"time": self.time, "true_state": true_state, "observed": self.sensors.get_observed(true_state)}
