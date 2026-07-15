# This file pre-processes PV-Data by adjusting them to realistic values


import pandas as pd

# File path
res_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\mpc_el_data.csv'

# Read the CSV file
df = pd.read_csv(res_path)

# Replace negative values in 'pv_power' column with 0
df['pv_power'] = df['pv_power'].apply(lambda x: max(x, 0))

# Create new DataFrame with only the 'pv_power' column
pv_only_df = df[['pv_power']]

# Save to a new CSV
cleaned_path = res_path.replace('.csv', '_pv_only_cleaned.csv')
pv_only_df.to_csv(cleaned_path, index=False)

