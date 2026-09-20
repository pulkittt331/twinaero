import math

class FaultInjector:
    def __init__(self):
        self.active_faults = {}

    def inject(self, fault_type, onset_time, max_severity, ramp_duration):
        self.active_faults[fault_type] = {
            "onset_time": onset_time,
            "max_severity": max_severity,
            "ramp_duration": ramp_duration,
            "active": True,
            "end_time": None
        }
        
    def remove(self, fault_type, current_time, ramp_down_duration=5.0):
        if fault_type in self.active_faults and self.active_faults[fault_type]["active"]:
            self.active_faults[fault_type]["active"] = False
            self.active_faults[fault_type]["end_time"] = current_time
            self.active_faults[fault_type]["ramp_down_duration"] = max(0.1, ramp_down_duration)

    def _get_severity(self, fault_info, current_time):
        if current_time < fault_info["onset_time"]:
            return 0.0
            
        if fault_info["active"]:
            if fault_info["ramp_duration"] <= 0:
                return fault_info["max_severity"]
            elapsed = current_time - fault_info["onset_time"]
            return min(fault_info["max_severity"], (elapsed / fault_info["ramp_duration"]) * fault_info["max_severity"])
        else:
            if fault_info["ramp_down_duration"] <= 0:
                return 0.0
            end_elapsed = current_time - fault_info["end_time"]
            if end_elapsed >= fault_info["ramp_down_duration"]:
                return 0.0
            
            active_duration = fault_info["end_time"] - fault_info["onset_time"]
            sev_at_end = fault_info["max_severity"]
            if fault_info["ramp_duration"] > 0:
                sev_at_end = min(fault_info["max_severity"], (active_duration / fault_info["ramp_duration"]) * fault_info["max_severity"])
                
            return max(0.0, sev_at_end * (1.0 - end_elapsed / fault_info["ramp_down_duration"]))

    def get_fault_effects(self, state, current_time, dt):
        effects = {
            "target_rpm_mod": 0.0, "target_ff_mod": 0.0, "target_egt_mod": 0.0, 
            "target_cht_mod": 0.0, "target_oil_temp_mod": 0.0, "target_map_mod": 0.0,
            "afr_mod": 0.0,
            "mult_oil_pressure": 1.0, "add_vibration": 0.0, "add_knock_index": 0.0,
            "cht_cyl_mods": [0.0, 0.0, 0.0, 0.0],
            "egt_cyl_mods": [0.0, 0.0, 0.0, 0.0]
        }
        
        if "overheating" in self.active_faults:
            sev = self._get_severity(self.active_faults["overheating"], current_time)
            effects["target_cht_mod"] += sev * 150.0
            effects["target_egt_mod"] += sev * 200.0

        if "lubrication" in self.active_faults:
            sev = self._get_severity(self.active_faults["lubrication"], current_time)
            effects["mult_oil_pressure"] -= sev * 0.8
            effects["target_oil_temp_mod"] += sev * 80.0
            effects["add_vibration"] += sev * 2.0

        if "vibration" in self.active_faults:
            sev = self._get_severity(self.active_faults["vibration"], current_time)
            effects["add_vibration"] += sev * 15.0
            
        if "injector" in self.active_faults:
            sev = self._get_severity(self.active_faults["injector"], current_time)
            bias = sev * 15.0
            oscillation = sev * 10.0 * math.sin(current_time * 2.0)
            
            effects["target_ff_mod"] += bias + oscillation
            effects["target_rpm_mod"] -= sev * 200.0 * math.sin(current_time * 2.0)
            effects["target_egt_mod"] += sev * 100.0 * math.cos(current_time * 2.0)

        if "injector_cyl3" in self.active_faults:
            sev = self._get_severity(self.active_faults["injector_cyl3"], current_time)
            effects["cht_cyl_mods"][2] += sev * 85.0
            effects["egt_cyl_mods"][2] += sev * 140.0
            effects["target_ff_mod"] += sev * 8.0

        if "overboost" in self.active_faults or "wastegate_stuck" in self.active_faults:
            fault_key = "overboost" if "overboost" in self.active_faults else "wastegate_stuck"
            sev = self._get_severity(self.active_faults[fault_key], current_time)
            effects["target_map_mod"] += sev * 18.0
            effects["add_knock_index"] += sev * 40.0

        if "knock_fault" in self.active_faults:
            sev = self._get_severity(self.active_faults["knock_fault"], current_time)
            effects["add_knock_index"] += sev * 75.0
            effects["add_vibration"] += sev * 25.0

        return effects
