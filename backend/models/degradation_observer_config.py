"""
Simulator-Calibrated Degradation Proxies.
These coefficients map fault-specific normalized residual evidence (Z-scores)
to a bounded [0, 1] severity estimate.
They are calibrated specifically to the reduced-order WearSimulator.
"""

OBSERVER_CONFIG = {
    "overheating": {
        "primary_residual": "cht",
        "slope": 0.0058,
        "intercept": 0.0041,
        "clip_min": 0.0,
        "clip_max": 1.0,
        "description": "Simulator-calibrated overheating degradation proxy"
    },
    "lubrication": {
        "primary_residual": "oil_temp",
        "slope": 0.0140,
        "intercept": 0.0026,
        "clip_min": 0.0,
        "clip_max": 1.0,
        "description": "Simulator-calibrated lubrication degradation proxy"
    },
    "vibration": {
        "primary_residual": "vibration",
        "slope": 0.0151,
        "intercept": -0.0010,
        "clip_min": 0.0,
        "clip_max": 1.0,
        "description": "Simulator-calibrated vibration degradation proxy"
    }
}
