import pandas as pd

# Load your Excel or CSV file here — update the file path and sheet name accordingly
file_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\uni_grid_mod.xlsx'  # Change to your actual file path
sheet_name = 'line'        # Change to your actual sheet name if Excel

# Load data from Excel
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Nominal system voltage in Volts (10 kV)
nominal_voltage = 10_000

# Calculate total resistance and reactance for each line
df['R_total'] = df['r_ohm_per_km'] * df['length_km']
df['X_total'] = df['x_ohm_per_km'] * df['length_km']

# Convert max current from kA to A
df['I_max_A'] = df['max_i_ka'] * 1000

# Calculate maximum apparent power limit in Watts (3-phase system)
df['P_max_W'] = (3**0.5) * nominal_voltage * df['I_max_A']

# Select columns to save, including the line name
#output_columns = ['name', 'length_km', 'R_total', 'X_total', 'I_max_A', 'P_max_W']
output_columns = ['name', 'P_max_W']

# Save to CSV
output_file = 'line_max_power_limits.csv'
df.to_csv(output_file, columns=output_columns, index=False)

print(f"Results saved to {output_file}")