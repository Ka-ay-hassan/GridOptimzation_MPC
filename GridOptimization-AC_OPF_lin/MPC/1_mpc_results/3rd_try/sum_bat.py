import pandas as pd


# #active power
# charge_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\1_mpc_results\\3rd_try\\batt_charge_active.csv'
# discharge_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\1_mpc_results\\3rd_try\\batt_discharge_active.csv'
# output_file = "C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\1_mpc_results\\3rd_try\\batt_total_active.csv"

# reactive power
charge_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\1_mpc_results\\3rd_try\\batt_charge_reactive.csv'
discharge_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\1_mpc_results\\3rd_try\\batt_discharge_reactive.csv'
output_file = "C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\1_mpc_results\\3rd_try\\batt_total_reactive.csv"



# Read CSV files
df1 = pd.read_csv(charge_path, sep=',')
df2 = pd.read_csv(discharge_path, sep=',')

# Check if the first columns are identical
if not df1.iloc[:, 0].equals(df2.iloc[:, 0]):
    raise ValueError("The first columns in the two CSV files are not identical!")

# Sum the 2nd and 3rd columns
df_combined = pd.DataFrame()
df_combined[df1.columns[0]] = df1.iloc[:, 0]  # keep first column as is
df_combined[df1.columns[1]] = df1.iloc[:, 1] - df2.iloc[:, 1]
df_combined[df1.columns[2]] = df1.iloc[:, 2] - df2.iloc[:, 2]

# Save to new CSV with semicolon delimiter
df_combined.to_csv(output_file, sep=',', index=False)

print(f"Combined CSV saved as {output_file}")