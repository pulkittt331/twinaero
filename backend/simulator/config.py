"""
TwinAero-X Simulator Configuration
All equations, coefficients, and bounds are PROTOTYPE ENGINEERING ASSUMPTIONS.
They do not imply validation against a specific real aero-piston engine.
"""

MAX_RPM = 5500.0
IDLE_RPM = 1200.0
BASE_CHT = 100.0
BASE_EGT = 600.0
BASE_OIL_TEMP = 80.0
NOMINAL_OIL_PRESSURE = 70.0
BASE_VOLTAGE = 24.0

RPM_INERTIA = 2.0
FF_INERTIA = 0.5
EGT_INERTIA = 1.0
CHT_INERTIA = 10.0
OIL_TEMP_INERTIA = 15.0

# 1. PHYSICAL PLAUSIBILITY BOUNDS (Absolute reality limits)
PHYSICAL_BOUNDS = {
    "rpm": (0.0, 7000.0),
    "fuel_flow": (0.0, 120.0),
    "egt": (10.0, 1300.0),
    "cht": (10.0, 400.0),
    "oil_temp": (10.0, 220.0),
    "oil_pressure": (0.0, 150.0),
    "vibration": (0.0, 80.0),
    "battery_voltage": (0.0, 40.0),
    "map": (10.0, 60.0),
    "knock_index": (0.0, 100.0),
    "afr": (8.0, 22.0),
    "lambda_val": (0.5, 1.5),
    "cht1": (10.0, 400.0),
    "cht2": (10.0, 400.0),
    "cht3": (10.0, 400.0),
    "cht4": (10.0, 400.0),
    "egt1": (10.0, 1300.0),
    "egt2": (10.0, 1300.0),
    "egt3": (10.0, 1300.0),
    "egt4": (10.0, 1300.0),
    "energy_balance_error": (0.0, 100.0),
    "thermal_efficiency": (0.0, 100.0)
}

# 2. SENSOR MEASUREMENT BOUNDS (Instrument clipping)
SENSOR_BOUNDS = {
    "rpm": (0.0, 6000.0),
    "fuel_flow": (0.0, 100.0),
    "egt": (0.0, 1200.0),
    "cht": (0.0, 350.0),
    "oil_temp": (0.0, 200.0),
    "oil_pressure": (0.0, 120.0),
    "vibration": (0.0, 50.0),
    "battery_voltage": (0.0, 32.0),
    "map": (10.0, 50.0),
    "knock_index": (0.0, 100.0),
    "afr": (8.0, 20.0),
    "lambda_val": (0.5, 1.4),
    "cht1": (0.0, 350.0),
    "cht2": (0.0, 350.0),
    "cht3": (0.0, 350.0),
    "cht4": (0.0, 350.0),
    "egt1": (0.0, 1200.0),
    "egt2": (0.0, 1200.0),
    "egt3": (0.0, 1200.0),
    "egt4": (0.0, 1200.0),
    "energy_balance_error": (0.0, 100.0),
    "thermal_efficiency": (0.0, 100.0)
}

# 3. OPERATING ENVELOPES (Healthy/Warning/Critical limits for analytics and UI)
ENVELOPES = {
    "rpm": {"normal": (1000, 4500), "warning": (4500, 5000), "critical": (5000, 6000)},
    "fuel_flow": {"normal": (0, 40), "warning": (40, 55), "critical": (55, 100)},
    "egt": {"normal": (600, 800), "warning": (800, 950), "critical": (950, 1200)},
    "cht": {"normal": (100, 180), "warning": (180, 220), "critical": (220, 300)},
    "oil_temp": {"normal": (80, 115), "warning": (115, 130), "critical": (130, 180)},
    "oil_pressure": {"critical_low": (0, 30), "warning_low": (30, 45), "normal": (45, 80), "warning_high": (80, 95), "critical_high": (95, 120)},
    "vibration": {"normal": (0, 4), "warning": (4, 8), "critical": (8, 50)},
    "battery_voltage": {"critical_low": (0, 22), "warning_low": (22, 24), "normal": (24, 29), "warning_high": (29, 30), "critical_high": (30, 40)},
    "map": {"normal": (25, 38), "warning": (38, 43), "critical": (43, 50)},
    "knock_index": {"normal": (0, 15), "warning": (15, 35), "critical": (35, 100)},
    "afr": {"normal": (13.5, 15.5), "warning": (15.5, 17.0), "critical": (17.0, 20.0)},
    "lambda_val": {"normal": (0.92, 1.05), "warning": (1.05, 1.15), "critical": (1.15, 1.40)},
    "cht1": {"normal": (100, 180), "warning": (180, 220), "critical": (220, 300)},
    "cht2": {"normal": (100, 180), "warning": (180, 220), "critical": (220, 300)},
    "cht3": {"normal": (100, 180), "warning": (180, 220), "critical": (220, 300)},
    "cht4": {"normal": (100, 180), "warning": (180, 220), "critical": (220, 300)},
    "egt1": {"normal": (600, 800), "warning": (800, 950), "critical": (950, 1200)},
    "egt2": {"normal": (600, 800), "warning": (800, 950), "critical": (950, 1200)},
    "egt3": {"normal": (600, 800), "warning": (800, 950), "critical": (950, 1200)},
    "egt4": {"normal": (600, 800), "warning": (800, 950), "critical": (950, 1200)},
    "energy_balance_error": {"normal": (0, 5), "warning": (5, 15), "critical": (15, 100)},
    "thermal_efficiency": {"normal": (25, 42), "warning": (18, 25), "critical": (0, 18)}
}

SENSOR_CONFIG = {
    "rpm": {"noise_std": 10.0, "quantize": 1.0},
    "fuel_flow": {"noise_std": 0.5, "quantize": 0.1},
    "egt": {"noise_std": 2.0, "quantize": 0.1},
    "cht": {"noise_std": 1.0, "quantize": 0.1},
    "oil_temp": {"noise_std": 1.0, "quantize": 0.1},
    "oil_pressure": {"noise_std": 1.5, "quantize": 0.1},
    "vibration": {"noise_std": 0.2, "quantize": 0.01},
    "battery_voltage": {"noise_std": 0.1, "quantize": 0.1},
    "map": {"noise_std": 0.2, "quantize": 0.1},
    "knock_index": {"noise_std": 0.5, "quantize": 0.1},
    "afr": {"noise_std": 0.1, "quantize": 0.01},
    "lambda_val": {"noise_std": 0.007, "quantize": 0.001},
    "cht1": {"noise_std": 1.0, "quantize": 0.1},
    "cht2": {"noise_std": 1.0, "quantize": 0.1},
    "cht3": {"noise_std": 1.0, "quantize": 0.1},
    "cht4": {"noise_std": 1.0, "quantize": 0.1},
    "egt1": {"noise_std": 2.0, "quantize": 0.1},
    "egt2": {"noise_std": 2.0, "quantize": 0.1},
    "egt3": {"noise_std": 2.0, "quantize": 0.1},
    "egt4": {"noise_std": 2.0, "quantize": 0.1},
    "energy_balance_error": {"noise_std": 0.2, "quantize": 0.1},
    "thermal_efficiency": {"noise_std": 0.3, "quantize": 0.1}
}
