import pandas as pd
import numpy as np

# Load the CSV file
file_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\PVSim-main\\aggregated_with_pv.csv'
df = pd.read_csv(file_path)

# Convert all columns to numeric, coercing errors to NaN
df_numeric = df.apply(pd.to_numeric, errors='coerce')

# List of column names to extract
columns_to_extract = [
    "Muff_AW-INFO", "Muff_INFO-ETI", "Muff_AW-ZHI", "Muff_HKW-DLR",
    "Muff_DLR-ATRIUM", "Muff_ZHI-HdM", "Muff_AW-KZS1", "Muff_AW-KZS2",
    "Muff_IFF-ZAQ", "Muff_ZAQ-IFKB", "PV_HLRS 1", "PV_NWZ", "PV_KZS", "PV_HKW", "PV_ETI"
]

# Extract specified columns
df_selected = df_numeric[columns_to_extract]

# Multiply all values by -1 and clip negatives to 0
df_transformed = (-1 * df_selected).clip(lower=0)

# Create random scaling factors for each individual value (same shape as df_transformed)
random_factors = np.random.uniform(0.8, 1.2, size=df_transformed.shape)

# Multiply each value by a different random factor
df_scaled = df_transformed * random_factors

# Optional: Show the result
print(df_scaled.head())

# Save to a new CSV file (optional)
df_scaled.to_csv('new_pv_processed.csv', index=False)
