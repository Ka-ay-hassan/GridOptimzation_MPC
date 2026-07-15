import pandas as pd

# Updated file paths
charge_path = r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_timeseries\2nd_try_200kWh\battery_charge.csv"
discharge_path = r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_timeseries\2nd_try_200kWh\battery_discharge.csv"

# Load data (auto separator)
charge_df = pd.read_csv(charge_path, sep=None, engine='python')
discharge_df = pd.read_csv(discharge_path, sep=None, engine='python')

# Extract time steps column
time_steps = charge_df.iloc[:, 0]

# Subtract discharge from charge (skip first column)
total_df = charge_df.iloc[:, 1:].subtract(discharge_df.iloc[:, 1:], fill_value=0)

# Insert time column back
total_df.insert(0, charge_df.columns[0], time_steps)

# Save to CSV (semicolon delimiter)
output_path = r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_timeseries\2nd_try_200kWh\battery_total.csv"
total_df.to_csv(output_path, index=False, sep=',')

print("Charge minus discharge calculated and saved to:", output_path)

