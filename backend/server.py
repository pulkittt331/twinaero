from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import copy

from backend.api import AnalyticalBackend, keys, extended_keys, estimate_degradation, get_normalized_margin, eval_risk
from backend.simulator.wear_simulator import WearSimulator
from backend.swarm_manager import SwarmManager

swarm_instance = SwarmManager()
backend_instance = swarm_instance.get_active_backend()

app = FastAPI(title="TwinAero-X API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

backend_instance = AnalyticalBackend()

class FaultRequest(BaseModel):
    fault_type: str

class MissionRequest(BaseModel):
    profile: str

class WhatIfRequest(BaseModel):
    throttle_cap: float
    altitude: float
    duration: int = 60

def get_current_status_dict() -> Dict[str, Any]:
    api = backend_instance
    if api.current_time == 0:
        return {
            "uninitialized": True,
            "current_time": 0.0,
            "health_index": 100.0,
            "diagnostic_status": {"anomaly": "NO", "fault": "NORMAL", "model_probability": None, "evidence": {}, "confirmed": False},
            "z_scores": {k: 0.0 for k in keys},
            "degradation_proxy": 0.0,
            "rul_estimate": None,
            "rul_ci_95": None,
            "advisory": {},
            "obs_history": [],
            "res_history": []
        }
    
    diag = api.get_diagnostic_status()
    hi = api.get_health_index()
    f_type = diag["fault"].lower() if diag["fault"] != "NORMAL" else "normal"
    z_scores = api.get_z_scores()
    proxy_val = api.get_degradation_proxy(f_type)
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    rul = api.get_rul_estimate(f_type, env) if f_type not in ["normal", "injector"] else None
    rul_ci = api.get_rul_confidence_interval(f_type, env) if f_type not in ["normal", "injector"] else None
    advisory = api.get_emergency_advisory(env)

    return {
        "uninitialized": False,
        "current_time": api.current_time,
        "health_index": round(hi, 1),
        "diagnostic_status": diag,
        "z_scores": z_scores,
        "degradation_proxy": round(proxy_val, 3),
        "rul_estimate": round(rul, 1) if rul is not None else None,
        "rul_ci_95": rul_ci,
        "advisory": advisory,
        "obs_history": api.obs_history,
        "res_history": api.res_history
    }

@app.get("/api/status")
def status():
    return get_current_status_dict()

@app.post("/api/start-healthy")
def start_healthy():
    global backend_instance
    backend_instance = AnalyticalBackend()
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    for _ in range(25):
        backend_instance.step(1.0, env, backend_instance.twin.healthy_engine.step(1.0, env, {}))
    return get_current_status_dict()

@app.post("/api/inject-fault")
def inject_fault(req: FaultRequest):
    global backend_instance
    env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    sim = WearSimulator(seed=42)
    sim.time = backend_instance.current_time
    sim.set_wear(req.fault_type, 0.8)
    for _ in range(15):
        res = sim.step(1.0, env)
        backend_instance.step(1.0, env, res["observed"], res["true_state"])
    
    status_data = get_current_status_dict()
    status_data["current_fault"] = req.fault_type
    return status_data

@app.post("/api/simulate-mission")
def simulate_mission(req: MissionRequest):
    global backend_instance
    missions = {
        "Conservative": [
            {"T": 20, "e": {"throttle": 85, "load": 50, "altitude": 0, "ambient_temp": 25, "injection_timing": 0}},
            {"T": 50, "e": {"throttle": 60, "load": 40, "altitude": 2000, "ambient_temp": 15, "injection_timing": 0}}
        ],
        "Nominal": [
            {"T": 20, "e": {"throttle": 85, "load": 50, "altitude": 0, "ambient_temp": 25, "injection_timing": 0}},
            {"T": 50, "e": {"throttle": 75, "load": 50, "altitude": 2000, "ambient_temp": 15, "injection_timing": 0}}
        ],
        "Aggressive": [
            {"T": 20, "e": {"throttle": 100, "load": 80, "altitude": 0, "ambient_temp": 25, "injection_timing": 0}},
            {"T": 50, "e": {"throttle": 95, "load": 80, "altitude": 2000, "ambient_temp": 15, "injection_timing": 0}}
        ]
    }
    
    if req.profile not in missions:
        raise HTTPException(status_code=400, detail="Invalid mission profile")
        
    diag = backend_instance.get_diagnostic_status()
    f = diag["fault"].lower() if diag["fault"] != "NORMAL" else "normal"
    try:
        risk_str, m, f_t, _ = backend_instance.simulate_mission(missions[req.profile], f)
        adv = backend_instance.get_advisory(missions[req.profile], f)
        return {
            "success": True,
            "risk": risk_str,
            "margin": round(m, 2),
            "fail_time": f_t,
            "advisory": adv,
            "profile": req.profile
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

from backend.simulator.mavlink_decoder import MAVLinkDecoder
mav_decoder = MAVLinkDecoder()

class MAVLinkRequest(BaseModel):
    mav_packet: Dict[str, Any]

@app.post("/api/ingest-mavlink")
def ingest_mavlink(req: MAVLinkRequest):
    global backend_instance
    telemetry = mav_decoder.decode_mavlink_json(req.mav_packet)
    env = {
        "throttle": req.mav_packet.get("throttle", 80),
        "load": 50,
        "altitude": req.mav_packet.get("altitude", 1000),
        "ambient_temp": 25,
        "injection_timing": 0
    }
    expected = backend_instance.twin.healthy_engine.step(1.0, env, {})
    backend_instance.step(1.0, env, telemetry, expected)
    return get_current_status_dict()

@app.post("/api/what-if-simulate")
def what_if_simulate(req: WhatIfRequest):
    return backend_instance.simulate_what_if_trajectory(req.throttle_cap, req.altitude, req.duration)

class EdgeBenchmarkRequest(BaseModel):
    target_device: str = "NVIDIA Jetson Orin Nano"

@app.get("/api/edge-benchmark")
def edge_benchmark(target_device: str = "NVIDIA Jetson Orin Nano"):
    return backend_instance.get_edge_benchmark(target_device)

@app.post("/api/edge-export-onnx")
def edge_export_onnx(model_name: str = "twinaero_pinn_diagnostic"):
    return backend_instance.export_onnx_model(model_name)

class SelectUAVRequest(BaseModel):
    uav_id: str

class SwarmFaultRequest(BaseModel):
    uav_id: str
    fault_type: str

@app.get("/api/swarm/status")
def swarm_status():
    return swarm_instance.get_swarm_status()

@app.post("/api/swarm/select")
def swarm_select(req: SelectUAVRequest):
    global backend_instance
    success = swarm_instance.select_uav(req.uav_id)
    if not success:
        raise HTTPException(status_code=404, detail="UAV ID not found in swarm")
    backend_instance = swarm_instance.get_active_backend()
    return swarm_instance.get_swarm_status()

@app.post("/api/swarm/inject-fault")
def swarm_inject_fault(req: SwarmFaultRequest):
    global backend_instance
    res = swarm_instance.inject_uav_fault(req.uav_id, req.fault_type)
    backend_instance = swarm_instance.get_active_backend()
    return res

class AttackSimulationRequest(BaseModel):
    attack_type: Optional[str] = "EGT_TAMPERING"

@app.get("/api/security/status")
def security_status():
    return backend_instance.get_security_status()

@app.post("/api/security/simulate-attack")
def security_simulate_attack(req: AttackSimulationRequest):
    return backend_instance.simulate_cyber_attack(req.attack_type)

@app.get("/api/fdr/replay")
def fdr_replay(start_idx: int = 0, end_idx: Optional[int] = None):
    return backend_instance.get_fdr_replay(start_idx, end_idx)

@app.get("/api/fdr/report")
def fdr_report(uav_id: str = "UAV-ALPHA"):
    return backend_instance.get_post_flight_report(uav_id)

@app.get("/api/fdr/download-csv")
def fdr_download_csv():
    csv_str = backend_instance.download_fdr_csv()
    return Response(content=csv_str, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=twinaero_fdr_telemetry.csv"})

@app.post("/api/reset")
def reset():
    global backend_instance, swarm_instance
    swarm_instance = SwarmManager()
    backend_instance = swarm_instance.get_active_backend()
    return get_current_status_dict()

import os
from fastapi.staticfiles import StaticFiles
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

