import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.ticker as mticker


# === Set your save path where the pandapower CSV results are stored ===
pp_path = r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\3_compare\\"
os.makedirs(pp_path, exist_ok=True)

# === Set your save path where the pandapower CSV results are stored ===
mpc_path = r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_results\3rd_try\\"
os.makedirs(mpc_path, exist_ok=True)

# === Load pandapower ACOPF line flow results (active and reactive) ===
df_pp_p_from = pd.read_csv(pp_path + "pp_line_flows_from_active.csv", sep=',', index_col=0)
df_pp_q_from = pd.read_csv(pp_path + "pp_line_flows_from_reactive.csv", sep=',', index_col=0)

# === Load MPC ACOPF line flow results (active and reactive) ===
df_mpc_p_from = pd.read_csv(mpc_path + "line_active_power.csv", sep=',', index_col=0)
df_mpc_q_from = pd.read_csv(mpc_path + "line_reactive_power.csv", sep=',', index_col=0)

# === Load or define your MPC results ===
# Replace this dummy data with your actual MPC results arrays or DataFrames
mpc_p_line = df_mpc_p_from.values #* 0.95
mpc_q_line = df_mpc_q_from.values #* 1.05

assert mpc_p_line.shape == df_pp_p_from.values.shape, "Mismatch in MPC and pandapower active power line flow shape!"
assert mpc_q_line.shape == df_pp_q_from.values.shape, "Mismatch in MPC and pandapower reactive power line flow shape!"

# === Compute absolute errors ===
abs_error_p = np.abs(mpc_p_line - df_pp_p_from.values)
abs_error_q = np.abs(mpc_q_line - df_pp_q_from.values)

# === Compute relative errors as fractions ===
eps = 0#1e-6

rel_error_p = abs_error_p / (np.abs(df_pp_p_from.values) + eps)
rel_error_q = abs_error_q / (np.abs(df_pp_q_from.values) + eps)

rel_error_p_percent = rel_error_p / 100
rel_error_q_percent = rel_error_q / 100

# === Convert to DataFrames ===
df_abs_error_p = pd.DataFrame(abs_error_p, columns=df_pp_p_from.columns, index=df_pp_p_from.index)
df_abs_error_q = pd.DataFrame(abs_error_q, columns=df_pp_q_from.columns, index=df_pp_q_from.index)

df_rel_error_p_frac = pd.DataFrame(rel_error_p, columns=df_pp_p_from.columns, index=df_pp_p_from.index)
df_rel_error_q_frac = pd.DataFrame(rel_error_q, columns=df_pp_q_from.columns, index=df_pp_q_from.index)

df_rel_error_p_percent = pd.DataFrame(rel_error_p_percent, columns=df_pp_p_from.columns, index=df_pp_p_from.index)
df_rel_error_q_percent = pd.DataFrame(rel_error_q_percent, columns=df_pp_q_from.columns, index=df_pp_q_from.index)

# # === Save CSV files ===
# df_abs_error_p.to_csv(pp_path + "abs_error_active_power_lines.csv", sep=',')
# df_abs_error_q.to_csv(pp_path + "abs_error_reactive_power_lines.csv", sep=',')

# df_rel_error_p_frac.to_csv(pp_path + "rel_error_active_power_lines_fraction.csv", sep=',')
# df_rel_error_q_frac.to_csv(pp_path + "rel_error_reactive_power_lines_fraction.csv", sep=',')

# df_rel_error_p_percent.to_csv(pp_path + "rel_error_active_power_lines_percent.csv", sep=',')
# df_rel_error_q_percent.to_csv(pp_path + "rel_error_reactive_power_lines_percent.csv", sep=',')

# === Plotting ===
line_name = df_pp_p_from.columns[0]

# plt.figure(figsize=(14, 7))
# plt.subplot(2,1,1)
# plt.plot(df_abs_error_p[line_name], label='Abs Error Active Power (MW)')
# plt.plot(df_abs_error_q[line_name], label='Abs Error Reactive Power (MVAr)')
# plt.title(f"Absolute Errors for Line '{line_name}'")
# plt.xlabel("Time Step")
# plt.ylabel("Error")
# plt.legend()
# plt.grid(True)

# plt.subplot(2,1,2)
# plt.plot(df_rel_error_p_percent[line_name], label='Rel Error Active Power (%)')
# plt.plot(df_rel_error_q_percent[line_name], label='Rel Error Reactive Power (%)')
# plt.title(f"Relative Errors (%) for Line '{line_name}'")
# plt.xlabel("Time Step")
# plt.ylabel("Relative Error (%)")
# plt.legend()
# plt.grid(True)

# plt.tight_layout()
# plt.show()

# Original save folder
plot_save_folder_1 = pp_path + "error_plots\\"
os.makedirs(plot_save_folder_1, exist_ok=True)

# Additional save folder
plot_save_folder_2 = r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Figures\ACOPF\PandaPower compare\Lines\\"
os.makedirs(plot_save_folder_2, exist_ok=True)

for line_name in df_pp_p_from.columns:
    plt.figure(figsize=(14, 7))
    
    plt.plot(df_rel_error_p_percent[line_name], label='Rel Error Active Power (%)', linewidth=2)
    plt.plot(df_rel_error_q_percent[line_name], label='Rel Error Reactive Power (%)', linewidth=2)
    
    plt.title(f"Relative Errors (%) for Line '{line_name}'", fontsize=24, fontweight='bold')
    plt.xlabel("Time Step", fontsize=22)
    plt.ylabel("Relative Error (%)", fontsize=22)
    
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    
    ax = plt.gca()
    formatter = mticker.ScalarFormatter(useOffset=False)
    formatter.set_scientific(False)
    ax.yaxis.set_major_formatter(formatter)
    
    plt.legend(fontsize=13, loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    filename1 = plot_save_folder_1 + f"rel_error_line_{line_name.replace(' ', '_')}.png"
    filename2 = plot_save_folder_2 + f"rel_error_line_{line_name.replace(' ', '_')}.png"
    
    plt.savefig(filename1)
    plt.savefig(filename2)
    plt.close()
    
    print(f"Saved relative error plot for line '{line_name}' as:")
    print(f"  {filename1}")
    print(f"  {filename2}")