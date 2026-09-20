import random
from .config import SENSOR_CONFIG, SENSOR_BOUNDS

class SensorModel:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
            
    def get_observed(self, true_state):
        observed = {}
        for key, val in true_state.items():
            if key in SENSOR_CONFIG:
                cfg = SENSOR_CONFIG[key]
                noisy = val + self.rng.gauss(0, cfg["noise_std"])
                vmin, vmax = SENSOR_BOUNDS[key]
                noisy = max(vmin, min(vmax, noisy))
                q = cfg["quantize"]
                if q > 0:
                    noisy = round(noisy / q) * q
                observed[key] = noisy
            else:
                observed[key] = val
        return observed
