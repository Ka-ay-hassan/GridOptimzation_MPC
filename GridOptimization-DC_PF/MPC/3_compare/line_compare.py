import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# Load data
df_line_flows = pd.read_csv(r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_timeseries\1st_try_200kWh\line_flows.csv", delimiter=';')
df_pp_line = pd.read_csv(r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\2_PandaPower_compare\pp_line.csv")


# print("line_flows.csv shape:", df_line_flows.shape)  # (rows, columns)
# print("pp_line.csv shape:", df_pp_line.shape)        # (rows, columns)

# # Additionally, print first few rows if you want to verify content:
# print("\nline_flows.csv preview:")
# print(df_line_flows.head())

# print("\npp_line.csv preview:")
# print(df_pp_line.head())

data_line_flows = df_line_flows.iloc[:, 1:]
data_line_flows_MW = data_line_flows.abs() / 1e6

assert data_line_flows_MW.shape == df_pp_line.shape, "Data dimensions mismatch!"

results = []

for idx in range(data_line_flows_MW.shape[1]):
    series_line = data_line_flows_MW.iloc[:, idx]
    series_pp = df_pp_line.iloc[:, idx]
    
    # Drop rows with zero in series_line to avoid division errors in percentage deviation
    valid_idx = series_line != 0
    s_line_valid = series_line[valid_idx]
    s_pp_valid = series_pp[valid_idx]
    
    # Percentage deviation (%)
    pct_deviation = ((s_line_valid - s_pp_valid).abs() / s_line_valid.abs()) * 100
    
    # Mean Absolute Error (MW)
    mae = np.mean((series_line - series_pp).abs())
    
    # Root Mean Squared Error (MW)
    rmse = np.sqrt(np.mean((series_line - series_pp)**2))
    
    # Correlation coefficient (Pearson r)
    corr = s_line_valid.corr(s_pp_valid)
    
    results.append({
        'Column_Index': idx,
        'Max_Deviation_%': pct_deviation.max(),
        'Min_Deviation_%': pct_deviation.min(),
        'Avg_Deviation_%': pct_deviation.mean(),
        'MAE_MW': mae,
        'RMSE_MW': rmse,
        'Correlation': corr
    })

results_df = pd.DataFrame(results)
print(results_df)


# Plot settings
fig, axs = plt.subplots(3, 2, figsize=(14, 12))
axs = axs.flatten()

# Column indices for x-axis
x = results_df['Column_Index']

# Max Percentage Deviation
axs[0].bar(x, results_df['Max_Deviation_%'])
axs[0].set_title('Max % Deviation')
axs[0].set_xlabel('Column Index')
axs[0].set_ylabel('%')

# Min Percentage Deviation
axs[1].bar(x, results_df['Min_Deviation_%'])
axs[1].set_title('Min % Deviation')
axs[1].set_xlabel('Column Index')
axs[1].set_ylabel('%')

# Average Percentage Deviation
axs[2].bar(x, results_df['Avg_Deviation_%'])
axs[2].set_title('Average % Deviation')
axs[2].set_xlabel('Column Index')
axs[2].set_ylabel('%')

# Mean Absolute Error
axs[3].bar(x, results_df['MAE_MW'])
axs[3].set_title('Mean Absolute Error (MW)')
axs[3].set_xlabel('Column Index')
axs[3].set_ylabel('MW')

# Root Mean Squared Error
axs[4].bar(x, results_df['RMSE_MW'])
axs[4].set_title('Root Mean Squared Error (MW)')
axs[4].set_xlabel('Column Index')
axs[4].set_ylabel('MW')

# Correlation Coefficient
axs[5].bar(x, results_df['Correlation'])
axs[5].set_title('Correlation Coefficient')
axs[5].set_xlabel('Column Index')
axs[5].set_ylabel('Correlation')

plt.tight_layout()
plt.show()