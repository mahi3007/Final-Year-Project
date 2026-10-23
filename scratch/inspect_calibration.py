import json

with open('reports/stage6m/power_simulation_results.json', 'r') as f:
    data = json.load(f)

cal = data.get('disparity_calibration_investigation', {})
print("=== Disparity Calibration Investigation Keys ===")
print(list(cal.keys()))
for k, v in cal.items():
    if isinstance(v, list):
        print(f"\n[{k}] ({len(v)} items):")
        for item in v:
            print("  ", item)
    elif isinstance(v, dict):
        print(f"\n[{k}]:", json.dumps(v, indent=2))

sens = data.get('dgp_sensitivity_investigation', {})
print("\n=== DGP Sensitivity Investigation Keys ===")
print(list(sens.keys()))
for k, v in sens.items():
    if isinstance(v, list):
        print(f"\n[{k}] ({len(v)} items):")
        for item in v:
            print("  ", item)
