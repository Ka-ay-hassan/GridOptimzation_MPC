import pandas as pd
import numpy as np

file_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\uni_grid_mod.xlsx'

# Check sheet names
xls = pd.ExcelFile(file_path)
print("Available sheets:", xls.sheet_names)

# Load the correct sheet (update sheet_name accordingly)
df_lines = pd.read_excel(file_path, sheet_name='line')  # change 'Lines' to your sheet name

# Clean column names
df_lines.columns = df_lines.columns.str.strip().str.lower()
print("Columns in sheet:", df_lines.columns)

def calculate_power_limits_mva(df, voltage_kv):
    V = voltage_kv * 1e3
    results = []
    
    for idx, row in df.iterrows():
        length = row['length_km']
        r = row['r_ohm_per_km'] * length
        x = row['x_ohm_per_km'] * length
        max_i = row['max_i_ka'] * 1e3
        
        Z = np.sqrt(r**2 + x**2)
        S_max_va = np.sqrt(3) * V * max_i
        
        cos_phi = r / Z if Z != 0 else 1
        P_max_w = S_max_va * cos_phi
        Q_max_var = S_max_va * (x / Z) if Z != 0 else 0
        
        results.append({
            'line_index': idx,
            'S_max_MVA': S_max_va / 1e6,
            'P_max_MW': P_max_w / 1e6,
            'Q_max_MVAr': Q_max_var / 1e6
        })
    return pd.DataFrame(results)

nominal_voltage_kv = 10

df_results = calculate_power_limits_mva(df_lines, nominal_voltage_kv)

print(df_results)

df_results.to_csv('max_line_power_limits_MVA.csv', index=False)


