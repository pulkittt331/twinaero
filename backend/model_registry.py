import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier, RandomForestRegressor
from backend.simulator.simulator import Simulator
from backend.digital_twin.twin_model import DigitalTwin
import math

keys = ['rpm', 'fuel_flow', 'egt', 'cht', 'oil_temp', 'oil_pressure', 'vibration', 'battery_voltage']
res_cols = [f"res_{k}" for k in keys]
z_cols = [f"z_{k}" for k in keys]

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
                wear_effects["target_ff_mod"] += sev * 30.0
                
        merged = {}
        for k in fault_effects:
            if k == "mult_oil_pressure": merged[k] = fault_effects[k] * wear_effects.get("mult_oil_pressure", 1.0)
            else: merged[k] = fault_effects[k] + wear_effects.get(k, 0.0)
                
        true_state = self.engine.step(dt, env, merged)
        return {"time": self.time, "true_state": true_state, "observed": self.sensors.get_observed(true_state)}

def calculate_hi(df):
    if len(df) == 0: return 100.0
    M = np.sqrt((df[[f"res_{k}" for k in keys]] ** 2).mean(axis=1))
    S = M.ewm(alpha=0.1, adjust=False).mean()
    HI = 100 * np.exp(-0.03 * S)
    return HI

# Simplified generator for Diagnostic Models
def train_diagnostic_models():
    env_base = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    records = []
    faults = ["normal", "overheating", "lubrication", "injector", "vibration"]
    for i, f in enumerate(faults):
        sim = Simulator(seed=42+i)
        twin = DigitalTwin()
        if f != "normal":
            sim.inject_fault(f, max_severity=1.0, ramp_duration=10.0)
        for t in range(1, 40):
            res = sim.step(1.0, env_base)
            tw = twin.step(1.0, env_base, res["observed"])
            row = {"fault_type": f, "t": t}
            row.update({f"res_{k}": tw["residuals"][k] for k in keys})
            records.append(row)
    df = pd.DataFrame(records)
    
    # 1. RESTORE CONSISTENT DIAGNOSTIC PREPROCESSING
    healthy = df[df["fault_type"] == "normal"]
    preproc_stats = {}
    for k in keys:
        mean_val = healthy[f"res_{k}"].mean()
        std_val = healthy[f"res_{k}"].std()
        if pd.isna(std_val) or std_val == 0: std_val = 0.01
        preproc_stats[k] = {"mean": mean_val, "std": std_val}
        
    for k in keys:
        df[f"z_{k}"] = (df[f"res_{k}"] - preproc_stats[k]["mean"]) / preproc_stats[k]["std"]
        
    df["is_anomaly"] = (df["fault_type"] != "normal") & (df["t"] >= 25)
    
    healthy = df[df["fault_type"] == "normal"]
    iso = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    iso.fit(healthy[z_cols].fillna(0))
    
    faulty = df[df["is_anomaly"] == True]
    rf_fault = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=10)
    rf_fault.fit(faulty[z_cols].fillna(0), faulty["fault_type"])
    
    return iso, rf_fault, preproc_stats

# Simplified generator for RUL Models
def train_rul_model(preproc_stats):
    # To keep it quick, we just train a basic RUL RF on linear profiles
    env_base = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    faults = ["lubrication", "overheating", "vibration"]
    records = []
    for f in faults:
        for seed in [10, 11]:
            sim = WearSimulator(seed=seed)
            twin = DigitalTwin()
            fail_t = None
            limit = {"lubrication": ("oil_pressure", 15.0, -1), "overheating": ("cht", 270.0, 1), "vibration": ("vibration", 15.0, 1)}
            l_k, l_v, sign = limit[f]
            
            traj = []
            for t in range(1, 151):
                sev = min(1.0, t / 150.0)
                sim.set_wear(f, sev)
                r = sim.step(1.0, env_base)
                tw = twin.step(1.0, env_base, r["observed"])
                row = {"t": t, "fault": f}
                row.update({f"res_{k}": tw["residuals"][k] for k in keys})
                
                # Check fail
                val = r["true_state"][l_k]
                if (sign == 1 and val > l_v) or (sign == -1 and val < l_v):
                    fail_t = t
                    break
                traj.append(row)
            
            if fail_t is not None:
                df_t = pd.DataFrame(traj)
                df_t["HI"] = calculate_hi(df_t)
                df_t["HI_slope"] = df_t["HI"].diff().fillna(0)
                for k in keys:
                    df_t[f"z_{k}"] = (df_t[f"res_{k}"] - preproc_stats[k]["mean"]) / preproc_stats[k]["std"]
                df_t["RUL"] = fail_t - df_t["t"]
                records.extend(df_t.to_dict("records"))
                
    df = pd.DataFrame(records)
    feats = ["HI", "HI_slope"] + z_cols + ["env_throttle", "env_altitude", "env_ambient_temp"]
    for env_k in ["throttle", "altitude", "ambient_temp"]:
        df[f"env_{env_k}"] = env_base[env_k]
        
    rf_rul = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=10)
    rf_rul.fit(df[feats].fillna(0), df["RUL"])
    return rf_rul

import joblib
import os

class ModelRegistry:
    def __init__(self):
        self.iso = None
        self.rf_fault = None
        self.rf_rul = None
        self.load_or_train()
        
    def load_or_train(self):
        if not os.path.exists("backend/models"):
            os.makedirs("backend/models")
            
        if os.path.exists("backend/models/iso.pkl"):
            self.iso = joblib.load("backend/models/iso.pkl")
            self.rf_fault = joblib.load("backend/models/rf_fault.pkl")
            self.rf_rul = joblib.load("backend/models/rf_rul.pkl")
            self.preproc_stats = joblib.load("backend/models/preproc_stats.pkl")
        else:
            print("Training diagnostic models...")
            self.iso, self.rf_fault, self.preproc_stats = train_diagnostic_models()
            print("Training RUL model...")
            self.rf_rul = train_rul_model(self.preproc_stats)
            joblib.dump(self.iso, "backend/models/iso.pkl")
            joblib.dump(self.rf_fault, "backend/models/rf_fault.pkl")
            joblib.dump(self.rf_rul, "backend/models/rf_rul.pkl")
            joblib.dump(self.preproc_stats, "backend/models/preproc_stats.pkl")
            
registry = ModelRegistry()
