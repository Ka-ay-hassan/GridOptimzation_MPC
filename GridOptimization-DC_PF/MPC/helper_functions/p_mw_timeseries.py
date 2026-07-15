# This code aggregates the multiple loads to its corresponding bus/node


import pandas as pd

df = pd.read_csv("C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\grid_sim\\results\\aggregated_bus_time_series.csv")
print("Dimensions (rows, columns):", df.shape)



# Slice the DataFrame to exclude the first column and get the next 57 columns
subset_df = df.iloc[:, :len(df)] *1000

# Print the dimensions of the subset
print("Dimensions of subset (rows, columns):", subset_df.shape)

# Set pandas to display all rows
pd.set_option('display.max_rows', None)
print(subset_df)