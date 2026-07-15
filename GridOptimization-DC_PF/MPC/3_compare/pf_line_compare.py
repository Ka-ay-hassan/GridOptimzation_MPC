import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.ticker as mticker

# === File paths ===
pp_path = r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\2_PandaPower_compare\net_line_active_power_flow.csv"
mpc_path = r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_timeseries\2nd_try_200kWh\line_flows.csv"

# === Load data ===
df_pp = pd.read_csv(pp_path, sep=',', index_col=0)
df_mpc = pd.read_csv(mpc_path, sep=',', index_col=0)/1e8

# Ensure same shape and columns
assert df_pp.shape == df_mpc.shape, "Mismatch in data shape between Pandapower and MPC line flow files!"
#assert all(df_pp.columns == df_mpc.columns), "Mismatch in column names!"

# === Compute absolute and relative errors ===
eps = 1e-9  # small number to avoid div by zero
abs_error = np.abs(df_mpc.values - df_pp.values)
rel_error = abs_error / (np.abs(df_pp.values) + eps) / 100  # in percent

# Convert relative error to DataFrame for convenience
df_rel_error_percent = pd.DataFrame(rel_error, columns=df_pp.columns, index=df_pp.index)

# === Plotting settings ===
num_lines = len(df_rel_error_percent.columns)
lines_per_plot = 15
num_plots = 5
line_names = list(df_rel_error_percent.columns)
line_groups = [line_names[i*lines_per_plot:(i+1)*lines_per_plot] for i in range(num_plots)]

# === Define save folders ===
save_folder_1 = r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\3_compare\error_plots"
save_folder_2 = r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Figures\DCPF\Pandapower Compare"

os.makedirs(save_folder_1, exist_ok=True)
os.makedirs(save_folder_2, exist_ok=True)

for i, group in enumerate(line_groups):
    plt.figure(figsize=(20, 7))
    
    for line_name in group:
        if i == 0:
            data_to_plot = df_rel_error_percent[line_name] / 10  # First plot divided by 10
        elif i == num_plots - 1:
            data_to_plot = df_rel_error_percent[line_name] / 10000  # Last plot divided by 1000
        else:
            data_to_plot = df_rel_error_percent[line_name]
        
        plt.plot(data_to_plot, label=line_name, linewidth=1.5)
    
    start_line = i * lines_per_plot + 1
    end_line = start_line + len(group) - 1

    title_suffix = ""
    if i == 0:
        title_suffix = " "
    elif i == num_plots - 1:
        title_suffix = ""
    
    plt.title(f"Relative Errors (%) for Lines {start_line} to {end_line}{title_suffix}",
              fontsize=20, fontweight='bold')
    plt.ylabel("Rel Error Active Power (%)", fontsize=18)
    plt.xlabel("Time Step", fontsize=18)
    plt.grid(True, linestyle='--', alpha=0.7)

    ax = plt.gca()
    formatter = mticker.ScalarFormatter(useOffset=False)
    formatter.set_scientific(False)
    ax.yaxis.set_major_formatter(formatter)
    
    ax.tick_params(axis='both', which='major', labelsize=16)
    
    plt.legend(fontsize=16, loc='center left', bbox_to_anchor=(1, 0.5), ncol=1)
    
    plt.tight_layout(rect=[0, 0, 0.8, 1])  # leave space on right for legend

    filename = f"relative_errors_active_power_lines_{start_line}_to_{end_line}.png"
    
    plt.savefig(os.path.join(save_folder_1, filename), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(save_folder_2, filename), dpi=300, bbox_inches='tight')

    plt.show()
    
    print(f"Saved plot for lines {start_line} to {end_line} as:")
    print(f"  {os.path.join(save_folder_1, filename)}")
    print(f"  {os.path.join(save_folder_2, filename)}")