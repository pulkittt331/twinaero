import copy
from typing import Dict, Any, List, Optional
from backend.api import AnalyticalBackend, keys
from backend.simulator.wear_simulator import WearSimulator

SQUAD_UAVS = [
    {
        "id": "UAV-ALPHA",
        "name": "Alpha Recon",
        "role": "Reconnaissance & Patrol",
        "engine": "Rotax 914 iS Turbocharged",
        "lat": 28.6139,
        "lon": 77.2090,
        "alt_ft": 10000,
        "sector": "Sector-1 (North Recon)"
    },
    {
        "id": "UAV-BRAVO",
        "name": "Bravo Scout",
        "role": "High-Altitude Surveillance",
        "engine": "Rotax 915 iS Intercooled",
        "lat": 28.6250,
        "lon": 77.2200,
        "alt_ft": 14000,
        "sector": "Sector-2 (High Altitude)"
    },
    {
        "id": "UAV-CHARLIE",
        "name": "Charlie Cargo",
        "role": "Heavy Cargo Transport",
        "engine": "Rotax 914 iS Turbocharged",
        "lat": 28.6000,
        "lon": 77.1950,
        "alt_ft": 8000,
        "sector": "Sector-3 (Supply Route)"
    },
    {
        "id": "UAV-DELTA",
        "name": "Delta Escort",
        "role": "Tactical Escort",
        "engine": "Rotax 915 iS Intercooled",
        "lat": 28.6350,
        "lon": 77.2400,
        "alt_ft": 12000,
        "sector": "Sector-4 (Perimeter Escort)"
    }
]

class SwarmManager:
    """
    Manages multi-UAV tactical squad telemetry, digital twin state isolation,
    and autonomous mission target re-allocation.
    """
    def __init__(self):
        self.uav_backends: Dict[str, AnalyticalBackend] = {}
        self.uav_meta: Dict[str, Dict[str, Any]] = {}
        self.active_uav_id: str = "UAV-ALPHA"
        
        for config in SQUAD_UAVS:
            u_id = config["id"]
            self.uav_backends[u_id] = AnalyticalBackend()
            self.uav_meta[u_id] = copy.deepcopy(config)
            self.uav_meta[u_id]["assigned_objective"] = config["sector"]
            self.uav_meta[u_id]["reallocated_from"] = None
            self.uav_meta[u_id]["injected_fault"] = "NORMAL"

    def select_uav(self, uav_id: str) -> bool:
        if uav_id in self.uav_backends:
            self.active_uav_id = uav_id
            return True
        return False

    def get_active_backend(self) -> AnalyticalBackend:
        return self.uav_backends[self.active_uav_id]

    def inject_uav_fault(self, uav_id: str, fault_type: str) -> Dict[str, Any]:
        if uav_id not in self.uav_backends:
            uav_id = self.active_uav_id
            
        b = self.uav_backends[uav_id]
        meta = self.uav_meta[uav_id]
        meta["injected_fault"] = fault_type.upper()
        
        env = {"throttle": 80, "load": 50, "altitude": meta["alt_ft"], "ambient_temp": 25, "injection_timing": 0}
        
        sim = WearSimulator(seed=42)
        sim.time = b.current_time
        sim.set_wear(fault_type, 0.8)
        for _ in range(15):
            res = sim.step(1.0, env)
            b.step(1.0, env, res["observed"], res["true_state"])
            
        return self.get_swarm_status()

    def evaluate_swarm_reallocation(self) -> List[Dict[str, Any]]:
        return []

    def get_swarm_status(self) -> Dict[str, Any]:
        uav_statuses = {}
        reallocation_notices = []
        health_scores = []
        active_fault_count = 0
        
        # Collect individual UAV twin data
        for u_id, b in self.uav_backends.items():
            meta = self.uav_meta[u_id]
            hi = round(b.get_health_index(), 1)
            diag = b.get_diagnostic_status()
            
            fault = meta.get("injected_fault", "NORMAL")
            if fault != "NORMAL":
                hi = min(hi, 42.5)
                diag["fault"] = fault
                diag["anomaly"] = "YES"
                active_fault_count += 1
                
            health_scores.append(hi)
                
            env = {"throttle": 80, "load": 50, "altitude": meta["alt_ft"], "ambient_temp": 25, "injection_timing": 0}
            f_type = fault.lower() if fault != "NORMAL" else "normal"
            rul = b.get_rul_estimate(f_type, env) if f_type not in ["normal", "injector"] else None
            
            uav_statuses[u_id] = {
                "id": u_id,
                "name": meta["name"],
                "role": meta["role"],
                "engine": meta["engine"],
                "sector": meta["sector"],
                "assigned_objective": meta["assigned_objective"],
                "reallocated_from": meta["reallocated_from"],
                "health_index": hi,
                "diagnostic_status": diag,
                "fault": fault,
                "rul_estimate": round(rul, 1) if rul is not None else None,
                "is_active": (u_id == self.active_uav_id)
            }

        # Check for autonomous mission target re-allocation
        # If any UAV has HI < 50 or active fault, assign its sector to the healthiest operational UAV
        degraded_uavs = [u for u in uav_statuses.values() if u["health_index"] < 50.0 or u["fault"] != "NORMAL"]
        healthy_uavs = sorted([u for u in uav_statuses.values() if u["health_index"] >= 75.0 and u["fault"] == "NORMAL"], key=lambda x: x["health_index"], reverse=True)
        
        for deg in degraded_uavs:
            if healthy_uavs:
                takeover_uav = healthy_uavs[0]
                notices_str = f"⚡ RE-ALLOCATION: {deg['id']} ({deg['fault']}) health dropped to {deg['health_index']}%. Sector '{deg['sector']}' re-assigned to {takeover_uav['id']}."
                reallocation_notices.append({
                    "from_uav": deg["id"],
                    "to_uav": takeover_uav["id"],
                    "reason": f"Fault: {deg['fault']} (Health: {deg['health_index']}%)",
                    "transferred_sector": deg["sector"],
                    "notice": notices_str
                })
                # Update metadata notice
                self.uav_meta[takeover_uav["id"]]["assigned_objective"] = f"{takeover_uav['sector']} + {deg['sector']} (Combined)"
                self.uav_meta[takeover_uav["id"]]["reallocated_from"] = deg["id"]

        avg_health = round(sum(health_scores) / len(health_scores), 1) if health_scores else 100.0
        
        return {
            "active_uav_id": self.active_uav_id,
            "swarm_health_avg": avg_health,
            "total_uavs": len(self.uav_backends),
            "active_faults_count": active_fault_count,
            "uavs": uav_statuses,
            "reallocation_notices": reallocation_notices
        }
