import math
from .config import PHYSICAL_BOUNDS, IDLE_RPM, MAX_RPM, BASE_CHT, BASE_EGT, BASE_OIL_TEMP, NOMINAL_OIL_PRESSURE, BASE_VOLTAGE, RPM_INERTIA, FF_INERTIA, EGT_INERTIA, CHT_INERTIA, OIL_TEMP_INERTIA

class EngineModel:
    def __init__(self, ambient_temp=25.0):
        self.state = {
            "rpm": 0.0,
            "fuel_flow": 0.0,
            "egt": ambient_temp,
            "cht": ambient_temp,
            "oil_temp": ambient_temp,
            "oil_pressure": 0.0,
            "vibration": 0.0,
            "battery_voltage": BASE_VOLTAGE,
            "map": 29.92,
            "knock_index": 0.0,
            "afr": 14.7,
            "lambda_val": 1.0,
            "cht1": ambient_temp,
            "cht2": ambient_temp,
            "cht3": ambient_temp,
            "cht4": ambient_temp,
            "egt1": ambient_temp,
            "egt2": ambient_temp,
            "egt3": ambient_temp,
            "egt4": ambient_temp
        }
        
    def _clamp(self, val, key):
        vmin, vmax = PHYSICAL_BOUNDS[key]
        return max(vmin, min(vmax, val))
        
    def get_healthy_targets(self, env):
        throttle = env.get("throttle", 0.0)
        load = env.get("load", 0.0)
        altitude = env.get("altitude", 0.0) # ft MSL (up to 30,000 ft)
        ambient_temp = env.get("ambient_temp", 25.0)
        injection_timing = env.get("injection_timing", 0.0)
        
        # ICAO Standard Atmosphere (ISA) Lapse Rate Model up to 30,000 ft
        t_isa_ambient = ambient_temp - (0.0019812 * altitude)
        
        # Atmospheric Pressure (inHg) as a function of Altitude (ft)
        p_amb = 29.92 * math.pow(max(0.1, 1.0 - 6.875e-6 * altitude), 5.2558)
        
        # Air Density ratio rho_ratio
        t_kelvin = max(200.0, ambient_temp + 273.15)
        rho_ratio = max(0.5, 1.0 - altitude / 10000.0)
        
        # Turbocharger MAP (Manifold Absolute Pressure) & Wastegate dynamics
        max_boost = 15.0 # max turbo boost in inHg for Rotax 914/915iS
        target_map = p_amb + (throttle / 100.0) * max_boost if self.state["rpm"] > 100 else p_amb
        
        # Intercooler Thermal Efficiency Model (eta_ic = 0.82)
        pi_compressor = max(1.0, target_map / max(5.0, p_amb))
        t_compressor_out = t_kelvin * math.pow(pi_compressor, 0.286)
        eta_ic = 0.82
        t_intercooler_out = (ambient_temp + 273.15) + (1.0 - eta_ic) * (t_compressor_out - t_kelvin) - 273.15
        
        temp_effect = max(0.9, 1.0 - (ambient_temp - 20) / 200.0)
        
        target_rpm = IDLE_RPM + (throttle / 100.0) * (MAX_RPM - IDLE_RPM) * rho_ratio * temp_effect
        target_rpm = target_rpm - (load / 100.0) * 500.0
        target_rpm = max(0.0, target_rpm)
        if throttle <= 1.0 and self.state["rpm"] < IDLE_RPM / 2:
            target_rpm = 0.0
            
        target_ff = 2.0 + (self.state["rpm"] / MAX_RPM) * 30.0 + (throttle / 100.0) * 10.0 + (load / 100.0) * 5.0
        target_ff *= rho_ratio
        if self.state["rpm"] < 100: target_ff = 0.0
        
        # Air-Fuel Ratio (AFR) & Lambda Target Calculations
        if self.state["rpm"] > 100:
            target_afr = 14.7 - (throttle / 100.0) * 1.2 + (load / 100.0) * 0.5
        else:
            target_afr = 14.7
        target_lambda = target_afr / 14.7
        
        target_egt = ambient_temp
        if self.state["rpm"] > 100:
            target_egt = BASE_EGT + (self.state["rpm"] / MAX_RPM) * 100.0 + (self.state["fuel_flow"] / 50.0) * 50.0
            target_egt += ambient_temp + (altitude / 1000.0) * 2.0 + injection_timing * 2.0 + (load / 100.0) * 20.0
            
        target_cht = ambient_temp
        if self.state["rpm"] > 100:
            target_cht = BASE_CHT + (self.state["egt"] - BASE_EGT) * 0.1 + (self.state["rpm"] / MAX_RPM) * 30.0 + ambient_temp/2.0
            
        target_oil_temp = ambient_temp
        if self.state["rpm"] > 100:
            target_oil_temp = BASE_OIL_TEMP + (self.state["cht"] - BASE_CHT) * 0.2 + (self.state["rpm"] / MAX_RPM) * 10.0
            
        # Individual Cylinder Targets
        target_cht1 = target_cht
        target_cht2 = target_cht
        target_cht3 = target_cht
        target_cht4 = target_cht
        
        target_egt1 = target_egt
        target_egt2 = target_egt
        target_egt3 = target_egt
        target_egt4 = target_egt
            
        return {
            "rpm": target_rpm,
            "fuel_flow": target_ff,
            "egt": target_egt,
            "cht": target_cht,
            "oil_temp": target_oil_temp,
            "map": target_map,
            "afr": target_afr,
            "lambda_val": target_lambda,
            "cht1": target_cht1, "cht2": target_cht2, "cht3": target_cht3, "cht4": target_cht4,
            "egt1": target_egt1, "egt2": target_egt2, "egt3": target_egt3, "egt4": target_egt4
        }

    def step(self, dt, env, fault_effects):
        targets = self.get_healthy_targets(env)
        
        targets["rpm"] += fault_effects.get("target_rpm_mod", 0.0)
        targets["fuel_flow"] += fault_effects.get("target_ff_mod", 0.0)
        targets["egt"] += fault_effects.get("target_egt_mod", 0.0)
        targets["cht"] += fault_effects.get("target_cht_mod", 0.0)
        targets["oil_temp"] += fault_effects.get("target_oil_temp_mod", 0.0)
        targets["map"] += fault_effects.get("target_map_mod", 0.0)
        
        # Apply cylinder-specific fault modifications
        cyl_cht_mods = fault_effects.get("cht_cyl_mods", [0.0, 0.0, 0.0, 0.0])
        cyl_egt_mods = fault_effects.get("egt_cyl_mods", [0.0, 0.0, 0.0, 0.0])
        
        targets["cht1"] += fault_effects.get("target_cht_mod", 0.0) + cyl_cht_mods[0]
        targets["cht2"] += fault_effects.get("target_cht_mod", 0.0) + cyl_cht_mods[1]
        targets["cht3"] += fault_effects.get("target_cht_mod", 0.0) + cyl_cht_mods[2]
        targets["cht4"] += fault_effects.get("target_cht_mod", 0.0) + cyl_cht_mods[3]
        
        targets["egt1"] += fault_effects.get("target_egt_mod", 0.0) + cyl_egt_mods[0]
        targets["egt2"] += fault_effects.get("target_egt_mod", 0.0) + cyl_egt_mods[1]
        targets["egt3"] += fault_effects.get("target_egt_mod", 0.0) + cyl_egt_mods[2]
        targets["egt4"] += fault_effects.get("target_egt_mod", 0.0) + cyl_egt_mods[3]
        
        alpha_rpm = 1.0 - math.exp(-dt / RPM_INERTIA)
        alpha_ff = 1.0 - math.exp(-dt / FF_INERTIA)
        alpha_egt = 1.0 - math.exp(-dt / EGT_INERTIA)
        alpha_cht = 1.0 - math.exp(-dt / CHT_INERTIA)
        alpha_ot = 1.0 - math.exp(-dt / OIL_TEMP_INERTIA)
        alpha_map = 1.0 - math.exp(-dt / 1.2) # Turbo lag constant
        
        self.state["rpm"] += alpha_rpm * (targets["rpm"] - self.state["rpm"])
        self.state["fuel_flow"] += alpha_ff * (targets["fuel_flow"] - self.state["fuel_flow"])
        self.state["oil_temp"] += alpha_ot * (targets["oil_temp"] - self.state["oil_temp"])
        self.state["map"] += alpha_map * (targets["map"] - self.state["map"])
        
        for idx, k in enumerate(["cht1", "cht2", "cht3", "cht4"]):
            self.state[k] += alpha_cht * (targets[k] - self.state[k])
        for idx, k in enumerate(["egt1", "egt2", "egt3", "egt4"]):
            self.state[k] += alpha_egt * (targets[k] - self.state[k])

        true_state = dict(self.state)
        
        # Aggregate CHT and EGT updated from cylinder array
        true_state["cht"] = (true_state["cht1"] + true_state["cht2"] + true_state["cht3"] + true_state["cht4"]) / 4.0
        true_state["egt"] = (true_state["egt1"] + true_state["egt2"] + true_state["egt3"] + true_state["egt4"]) / 4.0
        
        # Detonation & Knock Index Calculation
        # Knock occurs if MAP is high (>42 inHg) AND peak CHT is high (>185°C)
        max_cht = max(true_state["cht1"], true_state["cht2"], true_state["cht3"], true_state["cht4"])
        knock_risk = 0.0
        if true_state["rpm"] > 100:
            map_overboost = max(0.0, true_state["map"] - 45.0)
            cht_overtemp = max(0.0, max_cht - 230.0)
            knock_risk = (map_overboost * 5.0) + (cht_overtemp * 2.0)
        knock_risk += fault_effects.get("add_knock_index", 0.0)
        true_state["knock_index"] = max(0.0, min(100.0, knock_risk))
        
        base_op = (true_state["rpm"] / MAX_RPM) * NOMINAL_OIL_PRESSURE * 1.2 if true_state["rpm"] > 100 else 0.0
        viscosity_factor = math.exp(-0.01 * max(0, true_state["oil_temp"] - BASE_OIL_TEMP))
        true_state["oil_pressure"] = base_op * viscosity_factor * fault_effects.get("mult_oil_pressure", 1.0)
        
        base_vib = 0.5 + 4.0 * (true_state["rpm"] / MAX_RPM)**2 if true_state["rpm"] > 100 else 0.0
        # High knock index directly induces high-frequency structural vibration spikes
        knock_vibration = (true_state["knock_index"] / 100.0) * 20.0
        true_state["vibration"] = base_vib + knock_vibration + fault_effects.get("add_vibration", 0.0)
        
        target_batt = BASE_VOLTAGE + 4.0 * min(1.0, max(0.0, (true_state["rpm"] - 800) / 1000.0))
        alpha_batt = 1.0 - math.exp(-dt / 5.0)
        self.state["battery_voltage"] += alpha_batt * (target_batt - self.state["battery_voltage"])
        true_state["battery_voltage"] = self.state["battery_voltage"]
        
        true_state["fuel_flow"] += fault_effects.get("ff_bias", 0.0) + fault_effects.get("ff_oscillation", 0.0)
        
        # AFR and Lambda dynamics
        afr_mod = fault_effects.get("afr_mod", 0.0)
        true_state["afr"] = targets["afr"] + afr_mod
        true_state["lambda_val"] = true_state["afr"] / 14.7
        
        # Thermodynamic Energy Balance & Thermal Efficiency (PINN Logic)
        lhv_fuel = 44.0  # LHV of aviation gasoline in MJ/kg (or kW per g/s)
        ff_g_per_s = max(0.001, true_state["fuel_flow"] / 3.6)
        q_in_kw = ff_g_per_s * lhv_fuel
        
        # Mechanical Shaft Power (kW): ~ (RPM / MAX_RPM)^2.5 * 85 kW
        power_mech_kw = 85.0 * math.pow(true_state["rpm"] / MAX_RPM, 2.5) if true_state["rpm"] > 100 else 0.0
        
        # Exhaust Heat Loss (kW): m_dot_exhaust * Cp * (EGT - Ambient)
        m_dot_exhaust_g_s = ff_g_per_s * (1.0 + true_state["afr"])
        cp_exhaust = 1.05  # kJ/kg*K
        amb_temp = env.get("ambient_temp", 25.0)
        q_exhaust_kw = (m_dot_exhaust_g_s / 1000.0) * cp_exhaust * max(0.0, true_state["egt"] - amb_temp)
        
        # Cooling Jacket Heat Loss (kW)
        q_cooling_kw = 0.25 * max(0.0, true_state["cht"] - amb_temp)
        
        # Total accounted energy
        q_accounted_kw = power_mech_kw + q_exhaust_kw + q_cooling_kw
        
        # First-Law Thermodynamic Energy Balance Closure Error (%)
        if q_in_kw > 0.5:
            energy_error = abs(q_in_kw - q_accounted_kw) / q_in_kw * 100.0
            thermal_eff = (power_mech_kw / q_in_kw) * 100.0
        else:
            energy_error = 0.0
            thermal_eff = 0.0
            
        true_state["energy_balance_error"] = max(0.0, min(100.0, energy_error))
        true_state["thermal_efficiency"] = max(0.0, min(100.0, thermal_eff))
        
        for k in true_state:
            true_state[k] = self._clamp(true_state[k], k)
            if k in ["oil_pressure", "vibration", "battery_voltage", "map", "knock_index", "afr", "lambda_val", "cht", "egt", "cht1", "cht2", "cht3", "cht4", "egt1", "egt2", "egt3", "egt4", "energy_balance_error", "thermal_efficiency"]:
                self.state[k] = true_state[k]
                
        return true_state
