import numpy as np
import copy
import pandas as pd
from typing import Dict, Any, List, Optional
from .simulator.wear_simulator import WearSimulator
from .digital_twin.twin_model import DigitalTwin
from .xai_engine import XAIEngine
from .advisory_engine import AdvisoryEngine
from .edge_optimizer import EdgeOptimizer
from .cyber_security_engine import CyberSecurityEngine
from .fdr_logger import FlightDataRecorder
import math
import joblib
import os

keys = ['rpm', 'fuel_flow', 'egt', 'cht', 'oil_temp', 'oil_pressure', 'vibration', 'battery_voltage']
extended_keys = ['rpm', 'fuel_flow', 'egt', 'cht', 'oil_temp', 'oil_pressure', 'vibration', 'battery_voltage', 'map', 'knock_index', 'afr', 'lambda_val', 'cht1', 'cht2', 'cht3', 'cht4', 'egt1', 'egt2', 'egt3', 'egt4', 'energy_balance_error', 'thermal_efficiency']

def calculate_hi(df, preproc_stats=None):
    if len(df) == 0:
        return 100.0
    if preproc_stats:
        z_df = pd.DataFrame()
        for k in keys:
            rm = preproc_stats[k]["mean"]
            rs = preproc_stats[k]["std"]
            z_df[k] = (df[f"res_{k}"] - rm) / rs
        M = np.sqrt((z_df ** 2).mean(axis=1))
    else:
        M = np.sqrt((df[[f"res_{k}" for k in keys]] ** 2).mean(axis=1))
    S = M.ewm(alpha=0.1, adjust=False).mean()
    HI = 100 * np.exp(-0.03 * S)
    return HI.iloc[-1]

from .models.degradation_observer_config import OBSERVER_CONFIG

def estimate_degradation(wear_type, z_scores):
    if wear_type not in OBSERVER_CONFIG:
        return 0.0
    config = OBSERVER_CONFIG[wear_type]
    z_val = z_scores.get(config["primary_residual"], 0.0)
    sev = config["slope"] * z_val + config["intercept"]
    return min(config["clip_max"], max(config["clip_min"], sev))

def get_normalized_margin(state, wear_type):
    if wear_type == "lubrication": return (state.get("oil_pressure", 70.0) - 15.0) / 15.0
    if wear_type in ["overheating", "injector_cyl3", "injector"]: return (270.0 - state.get("cht", 100.0)) / 70.0
    if wear_type in ["vibration", "knock_fault"]: return (15.0 - state.get("vibration", 0.0)) / 10.0
    if wear_type in ["overboost", "wastegate_stuck"]: return (50.0 - state.get("map", 29.92)) / 10.0
    return 1.0

def eval_risk(min_margin):
    if min_margin <= 0.0: return "RED"
    if min_margin < 0.2: return "AMBER" # <20% safety buffer
    return "GREEN"

class AnalyticalBackend:
    def __init__(self):
        self.twin = DigitalTwin()
        self.obs_history = []
        self.res_history = []
        self.last_observed = None
        self.last_true_state_debug = None
        self.last_expected_state = None
        self.current_time = 0.0
        
        # Load models
        model_dir = os.path.join(os.path.dirname(__file__), "models")
        if os.path.exists(os.path.join(model_dir, "iso.pkl")):
            self.iso = joblib.load(os.path.join(model_dir, "iso.pkl"))
            self.rf_fault = joblib.load(os.path.join(model_dir, "rf_fault.pkl"))
            self.rf_rul = joblib.load(os.path.join(model_dir, "rf_rul.pkl"))
            self.preproc_stats = joblib.load(os.path.join(model_dir, "preproc_stats.pkl"))
        else:
            self.iso = None
            self.rf_fault = None
            self.rf_rul = None
            self.preproc_stats = None
        
        self.anomaly_history = []
        self.edge_opt = EdgeOptimizer()
        self.cyber_sec = CyberSecurityEngine()
        self.fdr = FlightDataRecorder()

        
    def step(self, dt, env, observed_telemetry, true_state_debug=None):
        self.current_time += dt
        self.last_observed = copy.deepcopy(observed_telemetry)
        self.last_true_state_debug = copy.deepcopy(true_state_debug)
        self.obs_history.append(self.last_observed)
        
        tw = self.twin.step(dt, env, observed_telemetry)
        self.last_expected_state = copy.deepcopy(tw["expected_state"])
        row = {}
        for k in extended_keys:
            if k in tw["residuals"]:
                row[f"res_{k}"] = tw["residuals"][k]
        self.res_history.append(row)
        
        # Evaluate step anomaly using IsolationForest & 3-sigma outlier threshold
        if self.iso is not None and self.preproc_stats is not None:
            z_feats = []
            for k in keys:
                rm = self.preproc_stats[k]["mean"]
                rs = self.preproc_stats[k]["std"]
                z = (row[f"res_{k}"] - rm) / rs
                z_feats.append(z)
            is_anom = bool(self.iso.predict([z_feats])[0] == -1)
            if hasattr(self.iso, 'estimators_') and any(abs(z) > 2.5 for z in z_feats):
                is_anom = True
            self.anomaly_history.append(is_anom)
            
        diag = self.get_diagnostic_status()
        adv = self.get_emergency_advisory(env)
        self.fdr.record_step(
            time_step=self.current_time,
            env=env,
            observed=observed_telemetry,
            expected=self.last_expected_state if self.last_expected_state else observed_telemetry,
            health_index=self.get_health_index(),
            fault=diag.get("fault", "NORMAL"),
            advisory=adv
        )
        
    def get_current_engine_state(self, debug=False):
        if debug:
            return self.last_true_state_debug
        return self.last_observed
        
    def get_expected_state(self):
        return self.last_expected_state
        
    def get_residuals(self):
        if len(self.res_history) == 0:
            return {f"res_{k}": 0.0 for k in extended_keys}
        return self.res_history[-1]
        
    def get_diagnostic_status(self):
        if len(self.res_history) < 1 or self.iso is None or self.preproc_stats is None:
            return {"anomaly": "NO", "fault": "NORMAL", "model_probability": None, "evidence": {}, "confirmed": False, "xai_attribution": {}}
        
        df = pd.DataFrame(self.res_history[-1:])
        z_feats = []
        for k in keys:
            rm = self.preproc_stats[k]["mean"]
            rs = self.preproc_stats[k]["std"]
            z = (df.iloc[-1][f"res_{k}"] - rm) / rs
            z_feats.append(z)
            
        z_dict = {k: z_feats[i] for i, k in enumerate(keys)}
        xai_attr = XAIEngine.compute_feature_attribution(z_dict, self.rf_fault)
            
        is_anom = len(self.anomaly_history) > 0 and self.anomaly_history[-1]
        
        # 3-Sample Temporal Confirmation
        recent_anomalies = self.anomaly_history[-3:]
        confirmed = len(recent_anomalies) == 3 and all(recent_anomalies)
        
        if not is_anom or not confirmed:
            return {"anomaly": "NO", "fault": "NORMAL", "model_probability": None, "evidence": {}, "confirmed": confirmed, "xai_attribution": xai_attr}
            
        probs = self.rf_fault.predict_proba([z_feats])[0]
        classes = self.rf_fault.classes_
        idx = np.argmax(probs)
        fault = classes[idx]
        conf = probs[idx]
        
        # Evidence
        evidence = {}
        if self.last_expected_state and self.last_observed:
            max_res_k = max(keys, key=lambda k: abs(self.last_observed[k] - self.last_expected_state[k]) / max(1.0, self.last_expected_state[k]))
            evidence = {
                "key": max_res_k,
                "observed": self.last_observed[max_res_k],
                "expected": self.last_expected_state[max_res_k],
                "residual": self.last_observed[max_res_k] - self.last_expected_state[max_res_k]
            }
            
        return {
            "anomaly": "YES",
            "fault": fault.upper(),
            "model_probability": round(conf, 2),
            "evidence": evidence,
            "confirmed": confirmed,
            "xai_attribution": xai_attr
        }
        
    def get_health_index(self):
        df = pd.DataFrame(self.res_history)
        return calculate_hi(df, self.preproc_stats)
        
    def get_rul_estimate(self, wear_type, future_env):
        if wear_type is None or wear_type == "NORMAL" or wear_type not in ["lubrication", "overheating", "vibration"]:
            return None
        if self.rf_rul is None or len(self.res_history) < 2 or self.preproc_stats is None:
            return None
            
        hi_current = self.get_health_index()
        
        # Actual HI slope calculation
        df_prev = pd.DataFrame(self.res_history[:-1])
        hi_prev = calculate_hi(df_prev, self.preproc_stats)
        hi_slope = hi_current - hi_prev
        
        z_feats = []
        df = pd.DataFrame(self.res_history[-1:])
        for k in keys:
            rm = self.preproc_stats[k]["mean"]
            rs = self.preproc_stats[k]["std"]
            z = (df.iloc[-1][f"res_{k}"] - rm) / rs
            z_feats.append(z)
            
        feats = [hi_current, hi_slope] + z_feats + [future_env["throttle"], future_env["altitude"], future_env["ambient_temp"]]
        rul = self.rf_rul.predict([feats])[0]
        return max(0, rul)

    def get_rul_confidence_interval(self, wear_type, future_env):
        if wear_type is None or wear_type == "NORMAL" or wear_type not in ["lubrication", "overheating", "vibration"]:
            return None
        if self.rf_rul is None or len(self.res_history) < 2 or self.preproc_stats is None:
            return None
            
        hi_current = self.get_health_index()
        df_prev = pd.DataFrame(self.res_history[:-1])
        hi_prev = calculate_hi(df_prev, self.preproc_stats)
        hi_slope = hi_current - hi_prev
        
        z_feats = []
        df = pd.DataFrame(self.res_history[-1:])
        for k in keys:
            rm = self.preproc_stats[k]["mean"]
            rs = self.preproc_stats[k]["std"]
            z = (df.iloc[-1][f"res_{k}"] - rm) / rs
            z_feats.append(z)
            
        feats = [hi_current, hi_slope] + z_feats + [future_env["throttle"], future_env["altitude"], future_env["ambient_temp"]]
        return XAIEngine.compute_rul_confidence_interval(self.rf_rul, feats)
        
    def get_degradation_proxy(self, wear_type):
        if wear_type is None or wear_type == "NORMAL" or wear_type == "normal":
            return 0.0
        z_scores = {k: 0.0 for k in keys}
        if self.preproc_stats and len(self.res_history) > 0:
            last_res = self.res_history[-1]
            for k in keys:
                z_scores[k] = (last_res[f"res_{k}"] - self.preproc_stats[k]["mean"]) / self.preproc_stats[k]["std"]
        return estimate_degradation(wear_type, z_scores)
        
    def get_z_scores(self):
        z_scores = {k: 0.0 for k in keys}
        if self.preproc_stats and len(self.res_history) > 0:
            last_res = self.res_history[-1]
            for k in keys:
                z_scores[k] = (last_res[f"res_{k}"] - self.preproc_stats[k]["mean"]) / self.preproc_stats[k]["std"]
        return z_scores
        
    def simulate_mission(self, mission_profile, wear_type):
        """
        mission_profile: list of dicts [{"T": 20, "e": env_dict}, ...]
        """
        estimated_state = {}
        window = self.obs_history[-10:] if len(self.obs_history) >= 10 else self.obs_history
        for k in keys:
            if len(window) > 0:
                estimated_state[k] = np.mean([obs[k] for obs in window])
            else:
                estimated_state[k] = 0.0
                
        if wear_type is None or wear_type == "NORMAL":
            est_sev = 0.0
            wear_type = "normal"
        else:
            # Need z_scores for the observer
            z_scores = {k: 0.0 for k in keys}
            if self.preproc_stats and len(self.res_history) > 0:
                last_res = self.res_history[-1]
                for k in keys:
                    z_scores[k] = (last_res[f"res_{k}"] - self.preproc_stats[k]["mean"]) / self.preproc_stats[k]["std"]
            est_sev = estimate_degradation(wear_type, z_scores)
        
        # CURRENT CONDITION
        current_margin = get_normalized_margin(estimated_state, wear_type)
        current_risk = "RED" if current_margin <= 0.0 else eval_risk(current_margin)
                
        f_sim = WearSimulator(seed=999)
        f_sim.time = self.current_time
        f_sim.set_wear(wear_type, est_sev)
        
        for k in extended_keys:
            if k in estimated_state:
                f_sim.engine.state[k] = estimated_state[k]
        for k in ["cht1", "cht2", "cht3", "cht4"]:
            f_sim.engine.state[k] = estimated_state.get("cht", 100.0)
        for k in ["egt1", "egt2", "egt3", "egt4"]:
            f_sim.engine.state[k] = estimated_state.get("egt", 600.0)
            
        future_min_margin = 999.0
        fail_t = None
        
        for seg in mission_profile:
            for _ in range(seg["T"]):
                res = f_sim.step(1.0, seg["e"])
                m = get_normalized_margin(res["true_state"], wear_type)
                if m < future_min_margin: future_min_margin = m
                if m <= 0 and fail_t is None: fail_t = f_sim.time
                
        future_risk = eval_risk(future_min_margin)
        
        risk_str = f"Current Risk: {current_risk} | Future Mission Risk: {future_risk}"
        return risk_str, future_min_margin, fail_t, f_sim.time
        
    def get_mission_risk(self, mission_profile, wear_type):
        risk, _, _, _ = self.simulate_mission(mission_profile, wear_type)
        return risk
        
    def get_advisory(self, mission_profile, wear_type):
        risk_str, m, f_t, _ = self.simulate_mission(mission_profile, wear_type)
        if "Current Risk: RED" in risk_str:
            return "ADVISORY: CURRENT RED: Prototype-defined simulated criterion crossed. Mission rejected."
        if "Future Mission Risk: RED" in risk_str:
            return f"ADVISORY: Mission crosses prototype-defined simulated failure criterion (Fail at t={f_t}). Abort/replan."
        return "ADVISORY: Prototype simulation completed without crossing failure criterion."

    def get_emergency_advisory(self, env: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        if env is None:
            env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
            
        altitude = env.get("altitude", 1000.0)
        diag = self.get_diagnostic_status()
        fault = diag.get("fault", "NORMAL")
        deg_proxy = self.get_degradation_proxy(fault.lower() if fault != "NORMAL" else "normal")
        
        footprint = AdvisoryEngine.calculate_glide_footprint(altitude, deg_proxy)
        airfields = AdvisoryEngine.evaluate_diversion_airfields(altitude, self.current_time, fault, deg_proxy)
        rec_throttle = AdvisoryEngine.recommend_throttle_cap(fault)
        
        advisory_payload = {
            "glide_footprint": footprint,
            "airfields": airfields,
            "recommended_throttle_cap": rec_throttle
        }
        
        mavlink_text = AdvisoryEngine.format_mavlink_statustext(diag, advisory_payload)
        advisory_payload["mavlink_statustext"] = mavlink_text
        
        return advisory_payload

    def simulate_what_if_trajectory(self, throttle_cap: float, target_altitude: float, duration_sec: int = 60) -> Dict[str, Any]:
        diag = self.get_diagnostic_status()
        wear_type = diag.get("fault", "NORMAL").lower() if diag.get("fault") != "NORMAL" else "normal"
        
        what_if_env = {"throttle": throttle_cap, "load": 50, "altitude": target_altitude, "ambient_temp": 25, "injection_timing": 0}
        mission_profile = [{"T": duration_sec, "e": what_if_env}]
        
        risk_str, min_margin, fail_t, _ = self.simulate_mission(mission_profile, wear_type)
        rul_ci = self.get_rul_confidence_interval(wear_type, what_if_env) if wear_type != "normal" else None
        
        return {
            "throttle_cap": throttle_cap,
            "target_altitude": target_altitude,
            "duration_sec": duration_sec,
            "safety_margin": round(min_margin, 2),
            "risk_assessment": risk_str,
            "failure_time": fail_t,
            "forecast_rul_ci": rul_ci
        }

    def get_edge_benchmark(self, target_device: str = "NVIDIA Jetson Orin Nano") -> Dict[str, Any]:
        return self.edge_opt.benchmark_hardware(target_device)

    def export_onnx_model(self, model_name: str = "twinaero_pinn_diagnostic") -> Dict[str, Any]:
        return self.edge_opt.export_onnx_model(model_name)

    def get_security_status(self, env: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        if env is None:
            env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
        obs = self.last_observed if self.last_observed else {"egt": 650.0, "altitude": 1000.0, "fuel_flow": 20.0}
        exp = self.last_expected_state if self.last_expected_state else {"egt": 650.0, "altitude": 1000.0, "fuel_flow": 20.0}
        return self.cyber_sec.audit_telemetry(obs, exp, env)

    def simulate_cyber_attack(self, attack_type: Optional[str]) -> Dict[str, Any]:
        return self.cyber_sec.simulate_attack(attack_type)

    def get_fdr_replay(self, start_idx: int = 0, end_idx: Optional[int] = None) -> Dict[str, Any]:
        return self.fdr.get_replay_slice(start_idx, end_idx)

    def get_post_flight_report(self, uav_id: str = "UAV-ALPHA") -> Dict[str, Any]:
        return self.fdr.generate_post_flight_report(uav_id)

    def download_fdr_csv(self) -> str:
        return self.fdr.export_csv_telemetry()



