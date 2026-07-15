import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# Constants
nhor = 576        # number of time steps
dt = 300          # time step duration in seconds (5 min)

# Base directory on your PC
base_dir = "C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC"

files = {
    "Battery B1": "batb1.csv",
    "Battery B2": "batb2.csv",
    "Battery B3": "batb3.csv",
    "Battery B4": "batb4.csv"
}

total_charge_kWh = {}
total_discharge_kWh = {}

plt.figure(figsize=(12, 6))
for label, filename in files.items():
    full_path = os.path.join(base_dir, filename)
    df = pd.read_csv(full_path)
    
    # Check length
    if len(df) != nhor:
        print(f"Warning: {label} has {len(df)} rows, expected {nhor}")
    
    # Convert power to kW
    p_charge_kW = df['p_batt_charge'] / 1000
    p_discharge_kW = df['p_batt_discharge'] / 1000
    
    # Calculate total energy (kWh)
    energy_charge = np.sum(p_charge_kW) * (dt / 3600)
    energy_discharge = np.sum(p_discharge_kW) * (dt / 3600)
    
    total_charge_kWh[label] = energy_charge
    total_discharge_kWh[label] = energy_discharge
    
    # Plot charge and discharge power for this battery
    plt.plot(p_charge_kW, linestyle='-', label=f"{label} Charge")
    plt.plot(p_discharge_kW, linestyle='--', label=f"{label} Discharge")

plt.title('Battery Charge and Discharge Power Over Time', fontsize=16)
plt.xlabel('Time Step (5 min intervals)', fontsize=14)
plt.ylabel('Power [kW]', fontsize=14)
plt.legend(fontsize=10)
plt.grid(True)
plt.tight_layout()
plt.show()

# Print summary table
print("Total charged energy per battery (kWh):")
for b, e in total_charge_kWh.items():
    print(f"{b}: {e:.2f} kWh")

print("\nTotal discharged energy per battery (kWh):")
for b, e in total_discharge_kWh.items():
    print(f"{b}: {e:.2f} kWh")
