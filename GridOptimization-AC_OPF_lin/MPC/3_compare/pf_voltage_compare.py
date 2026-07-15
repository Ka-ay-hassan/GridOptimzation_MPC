import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.ticker as mticker

# Paths - adjust to your folders
pp_path = r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\3_compare\\"
mpc_path = r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_results\3rd_try\\"
save_path = r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Figures\ACOPF\PandaPower compare\Voltages\\"
os.makedirs(save_path, exist_ok=True)

# Load voltage magnitudes (p.u.) from pandapower and MPC CSVs
df_pp_voltages = pd.read_csv(pp_path + "pp_bus_voltages_pu.csv", sep=',', index_col=0)
df_mpc_delta_v = pd.read_csv(mpc_path + "delta_V.csv", sep=',', index_col=0)

print("Pandapower voltages shape:", df_pp_voltages.shape)
print("MPC voltages shape:", df_mpc_delta_v.shape)


# Convert MPC delta voltages (ΔV) to absolute voltages
df_mpc_voltages = df_mpc_delta_v + 1.0

# Ensure matching shape and bus order
assert df_pp_voltages.shape == df_mpc_voltages.shape, "Voltage data shapes do not match!"
assert list(df_pp_voltages.columns) == list(df_mpc_voltages.columns), "Bus names do not match!"

# Compute absolute and relative errors
abs_error_v = np.abs(df_mpc_voltages.values - df_pp_voltages.values)
rel_error_v = abs_error_v / (np.abs(df_pp_voltages.values) + 1e-6)
rel_error_v_percent = rel_error_v * 100

# Convert errors to DataFrames
df_abs_error_v = pd.DataFrame(abs_error_v, columns=df_pp_voltages.columns, index=df_pp_voltages.index)
df_rel_error_v_percent = pd.DataFrame(rel_error_v_percent, columns=df_pp_voltages.columns, index=df_pp_voltages.index)

# Save error CSVs
df_abs_error_v.to_csv(save_path + "abs_error_bus_voltages.csv", sep=',')
df_rel_error_v_percent.to_csv(save_path + "rel_error_bus_voltages_percent.csv", sep=',')

# Plot relative voltage errors per bus and save plots
for bus_name in df_pp_voltages.columns:
    plt.figure(figsize=(12,6))
    x_vals = pd.to_numeric(df_rel_error_v_percent.index, errors='coerce')
    
    plt.plot(x_vals, df_rel_error_v_percent[bus_name], label='Rel Voltage Error (%)', linewidth=2)
    
    plt.title(f"Relative Voltage Error (%) at Bus '{bus_name}'", fontsize=20, fontweight='bold')
    plt.xlabel("Time Step", fontsize=16)
    plt.ylabel("Relative Voltage Error (%)", fontsize=16)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    
    ax = plt.gca()
    formatter = mticker.ScalarFormatter(useOffset=False)
    formatter.set_scientific(False)
    ax.yaxis.set_major_formatter(formatter)
    
    plt.legend(fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    filename = save_path + f"rel_voltage_error_bus_{bus_name.replace(' ', '_')}.png"
    plt.savefig(filename)
    plt.close()
    
    print(f"Saved voltage error plot for bus '{bus_name}' as {filename}")