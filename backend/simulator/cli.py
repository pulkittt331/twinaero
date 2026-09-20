import argparse
import csv
from .simulator import Simulator

def main():
    parser = argparse.ArgumentParser(description="TwinAero-X Telemetry Simulator")
    parser.add_argument("--duration", type=float, default=60.0, help="Simulation duration in seconds")
    parser.add_argument("--dt", type=float, default=1.0, help="Time step")
    parser.add_argument("--fault", type=str, choices=["none", "injector", "lubrication", "overheating", "vibration"], default="none")
    parser.add_argument("--fault-time", type=float, default=30.0, help="When to inject the fault")
    parser.add_argument("--severity", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default="telemetry.csv")
    
    args = parser.parse_args()
    
    sim = Simulator(seed=args.seed)
    
    env = {
        "throttle": 80.0,
        "load": 50.0,
        "altitude": 1000.0,
        "ambient_temp": 25.0,
        "injection_timing": 0.0
    }
    
    records = []
    fault_injected = False
    
    for _ in range(int(args.duration / args.dt)):
        if args.fault != "none" and sim.time >= args.fault_time and not fault_injected:
            sim.inject_fault(args.fault, max_severity=args.severity, ramp_duration=5.0)
            fault_injected = True
            
        result = sim.step(args.dt, env)
        
        row = {"timestamp": result["time"]}
        row.update(result["observed"])
        row["throttle"] = env["throttle"]
        row["load"] = env["load"]
        row["altitude"] = env["altitude"]
        row["ambient_temp"] = env["ambient_temp"]
        
        records.append(row)
        
    if records:
        with open(args.out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        print(f"Generated {len(records)} rows to {args.out}")

if __name__ == "__main__":
    main()
