from .config import ENVELOPES

def get_envelope(key, val):
    if key not in ENVELOPES: return "UNKNOWN"
    env = ENVELOPES[key]
    
    if "critical_low" in env and env["critical_low"][0] <= val < env["critical_low"][1]: return "CRITICAL_LOW"
    if "warning_low" in env and env["warning_low"][0] <= val < env["warning_low"][1]: return "WARNING_LOW"
    
    if "normal" in env and env["normal"][0] <= val <= env["normal"][1]: return "NORMAL"
    
    if "warning" in env and env["warning"][0] < val <= env["warning"][1]: return "WARNING"
    if "critical" in env and env["critical"][0] < val <= env["critical"][1]: return "CRITICAL"
    
    if "warning_high" in env and env["warning_high"][0] < val <= env["warning_high"][1]: return "WARNING_HIGH"
    if "critical_high" in env and env["critical_high"][0] < val <= env["critical_high"][1]: return "CRITICAL_HIGH"
    
    return "OUTSIDE HEALTH ENVELOPE / INSIDE SIMULATOR BOUND"
