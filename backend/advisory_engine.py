import math
from typing import Dict, Any, List, Optional

class AdvisoryEngine:
    """
    Autonomous Emergency Re-Routing, Safe Glide Radius & Pilot Advisory Engine for TwinAero-X.
    Designed for MALE UAV Ground Control Station (GCS) integration (QGroundControl / Mission Planner).
    """

    # Reference emergency recovery airfields (DRDO TAPAS / Rustom-II operational theater mockup)
    AIRFIELDS = [
        {"id": "AF-01", "name": "Aeronautical Test Range (Challakere)", "dist_nm": 12.4, "bearing_deg": 315, "runway_ft": 9800},
        {"id": "AF-02", "name": "Forward Operating Base Bravo", "dist_nm": 24.8, "bearing_deg": 45, "runway_ft": 6500},
        {"id": "AF-03", "name": "Tactical Emergency Airstrip Charlie", "dist_nm": 38.2, "bearing_deg": 180, "runway_ft": 4200},
        {"id": "AF-04", "name": "Regional Airport Delta", "dist_nm": 56.0, "bearing_deg": 225, "runway_ft": 8000}
    ]

    LIFT_TO_DRAG_RATIO = 12.0  # Standard MALE UAV L/D glide ratio

    @staticmethod
    def calculate_glide_footprint(altitude_ft: float, degradation_proxy: float = 0.0) -> Dict[str, float]:
        """
        Calculates maximum safe engine-out and degraded power glide radius.
        1 NM = 6076.12 ft.
        """
        alt_ft = max(0.0, altitude_ft)
        
        # Engine-out pure glide distance (NM) = (Altitude_ft / 6076.12) * L/D
        pure_glide_nm = (alt_ft / 6076.12) * AdvisoryEngine.LIFT_TO_DRAG_RATIO
        
        # Power factor bonus based on residual engine health (1.0 - degradation_proxy)
        health_factor = max(0.0, 1.0 - degradation_proxy)
        powered_extension_nm = pure_glide_nm * (1.0 + 0.6 * health_factor)
        
        glide_km = powered_extension_nm * 1.852
        
        return {
            "pure_glide_nm": round(pure_glide_nm, 1),
            "powered_glide_nm": round(powered_extension_nm, 1),
            "glide_km": round(glide_km, 1)
        }

    @staticmethod
    def recommend_throttle_cap(fault_type: str, current_state: Optional[Dict[str, float]] = None) -> int:
        """
        Recommends maximum safe throttle cap (%) to prevent catastrophic engine failure.
        """
        if fault_type is None or fault_type == "NORMAL" or fault_type == "normal":
            return 100

        fault_lower = fault_type.lower()
        if "overheating" in fault_lower:
            return 55
        if "lubrication" in fault_lower:
            return 45
        if "vibration" in fault_lower or "knock" in fault_lower:
            return 60
        if "injector" in fault_lower or "overboost" in fault_lower:
            return 65

        return 50

    @staticmethod
    def evaluate_diversion_airfields(altitude_ft: float, current_time: float, fault_type: str, degradation_proxy: float = 0.0) -> List[Dict[str, Any]]:
        """
        Evaluates reachability status for all regional diversion airfields.
        """
        footprint = AdvisoryEngine.calculate_glide_footprint(altitude_ft, degradation_proxy)
        max_reach_nm = footprint["powered_glide_nm"]
        
        req_throttle = AdvisoryEngine.recommend_throttle_cap(fault_type)
        
        evaluations = []
        for af in AdvisoryEngine.AIRFIELDS:
            dist = af["dist_nm"]
            
            if dist <= max_reach_nm * 0.7:
                status = "REACHABLE"
                status_color = "#00e676"  # Bright Green
            elif dist <= max_reach_nm:
                status = "MARGINAL"
                status_color = "#ff9100"  # Orange
            else:
                status = "UNREACHABLE"
                status_color = "#ff1744"  # Red
                
            # Estimated time en route (mins) assuming 110 knots cruising speed
            ete_min = round((dist / 110.0) * 60.0, 1)
            
            evaluations.append({
                "id": af["id"],
                "name": af["name"],
                "dist_nm": dist,
                "bearing_deg": af["bearing_deg"],
                "runway_ft": af["runway_ft"],
                "ete_min": ete_min,
                "status": status,
                "status_color": status_color,
                "recommended_throttle": req_throttle
            })
            
        return evaluations

    @staticmethod
    def format_mavlink_statustext(diagnostic_status: Dict[str, Any], advisory_data: Dict[str, Any]) -> str:
        """
        Formats a standardized MAVLink STATUSTEXT / MAV_SEVERITY alert packet string for Ground Control Station display.
        """
        anomaly = diagnostic_status.get("anomaly", "NO")
        fault = diagnostic_status.get("fault", "NORMAL")
        confirmed = diagnostic_status.get("confirmed", False)
        
        if anomaly == "NO" or fault == "NORMAL":
            return "[MAV_SEVERITY_INFO] TWINAERO-X: Engine systems nominal. Altitude lapse & PINN thermal balance verified."
            
        throttle_cap = advisory_data.get("recommended_throttle_cap", 50)
        footprint = advisory_data.get("glide_footprint", {})
        glide_nm = footprint.get("powered_glide_nm", 0.0)
        
        airfields = advisory_data.get("airfields", [])
        reachable_af = [af["name"] for af in airfields if af["status"] == "REACHABLE"]
        best_af = reachable_af[0] if len(reachable_af) > 0 else "Emergency Off-Field Drop"
        
        if confirmed:
            return (
                f"[MAV_SEVERITY_ALERT] TWINAERO-X: CRITICAL {fault} FAULT CONFIRMED! "
                f"CAP THROTTLE AT {throttle_cap}% | SAFE GLIDE: {glide_nm} NM | DIVERSION: {best_af}"
            )
        else:
            return (
                f"[MAV_SEVERITY_WARNING] TWINAERO-X: ANOMALY DETECTED ({fault}). "
                f"MONITORING THERMAL SPREAD | RECOM. THROTTLE CAP: {throttle_cap}%"
            )
