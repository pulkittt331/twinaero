"""
TwinAero-X MAVLink & Avionics Telemetry Stream Decoder
Decodes MAVLink v2 HIGH_LATENCY2 / ENGINE_STATUS / SCALED_PRESSURE / RAW_IMU packets
into TwinAero-X standard digital twin telemetry format.
"""

from typing import Dict, Any

class MAVLinkDecoder:
    def __init__(self):
        self.last_parsed_packet = None

    def decode_mavlink_json(self, mav_packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses a MAVLink message structure (such as HIGH_LATENCY2 or ENGINE_STATUS).
        """
        msg_type = mav_packet.get("mavpackettype", "HIGH_LATENCY2")
        
        telemetry = {}
        
        if msg_type in ["HIGH_LATENCY2", "ENGINE_STATUS"]:
            # MAVLink field mappings
            telemetry["rpm"] = float(mav_packet.get("engine_rpm", mav_packet.get("rpm", 2400.0)))
            telemetry["fuel_flow"] = float(mav_packet.get("fuel_flow", 18.5))
            telemetry["egt"] = float(mav_packet.get("egt", 680.0))
            telemetry["cht"] = float(mav_packet.get("cht", 145.0))
            telemetry["oil_temp"] = float(mav_packet.get("temperature", mav_packet.get("oil_temp", 92.0)))
            telemetry["oil_pressure"] = float(mav_packet.get("press", mav_packet.get("oil_pressure", 72.0)))
            telemetry["vibration"] = float(mav_packet.get("vibration", mav_packet.get("vibe", 1.2)))
            telemetry["battery_voltage"] = float(mav_packet.get("battery_remaining", mav_packet.get("battery_voltage", 26.4)))
            telemetry["map"] = float(mav_packet.get("manifold_pressure", mav_packet.get("map", 29.92)))
            telemetry["knock_index"] = float(mav_packet.get("knock_index", 0.0))
            telemetry["afr"] = float(mav_packet.get("afr", 14.7))
            telemetry["lambda_val"] = float(mav_packet.get("lambda_val", 1.0))
            
            # Individual cylinder channels if present, else fallback
            telemetry["cht1"] = float(mav_packet.get("cht1", telemetry["cht"]))
            telemetry["cht2"] = float(mav_packet.get("cht2", telemetry["cht"]))
            telemetry["cht3"] = float(mav_packet.get("cht3", telemetry["cht"]))
            telemetry["cht4"] = float(mav_packet.get("cht4", telemetry["cht"]))
            
            telemetry["egt1"] = float(mav_packet.get("egt1", telemetry["egt"]))
            telemetry["egt2"] = float(mav_packet.get("egt2", telemetry["egt"]))
            telemetry["egt3"] = float(mav_packet.get("egt3", telemetry["egt"]))
            telemetry["egt4"] = float(mav_packet.get("egt4", telemetry["egt"]))
            
        else:
            # General fallback mapping
            for key in ["rpm", "fuel_flow", "egt", "cht", "oil_temp", "oil_pressure", "vibration", "battery_voltage", "map", "knock_index", "afr", "lambda_val"]:
                telemetry[key] = float(mav_packet.get(key, 0.0))

        self.last_parsed_packet = telemetry
        return telemetry

    def generate_sample_mavlink_packet(self, throttle: float = 80.0, altitude: float = 5000.0) -> Dict[str, Any]:
        """
        Generates a synthetic MAVLink HIGH_LATENCY2 packet for testing GCS stream ingestion.
        """
        return {
            "mavpackettype": "HIGH_LATENCY2",
            "custom_mode": 0,
            "latitude": 28.6139,
            "longitude": 77.2090,
            "altitude": int(altitude),
            "target_altitude": int(altitude),
            "heading": 90,
            "target_heading": 90,
            "target_distance": 1500,
            "throttle": int(throttle),
            "airspeed": 120,
            "groundspeed": 115,
            "engine_rpm": int(1200 + (throttle / 100.0) * 4300),
            "fuel_flow": 15.0 + (throttle / 100.0) * 12.0,
            "egt": 650.0 + (throttle / 100.0) * 100.0,
            "cht": 130.0 + (throttle / 100.0) * 40.0,
            "temperature": 90.0 + (throttle / 100.0) * 15.0,
            "press": 70.0,
            "vibration": 1.5,
            "battery_voltage": 26.5,
            "manifold_pressure": 29.92 + (throttle / 100.0) * 12.0,
            "knock_index": 2.0,
            "afr": 14.5,
            "lambda_val": 0.98,
            "cht1": 132.0, "cht2": 131.0, "cht3": 133.0, "cht4": 130.0,
            "egt1": 655.0, "egt2": 652.0, "egt3": 658.0, "egt4": 650.0
        }
