
import pandas as pd
import numpy as np

# Define the path to your Grid on the Excel file
grid_info = "C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\grid_sim\\data\\uni_grid.xlsx"


# Load data from the Excel sheets
bus_df = pd.read_excel(grid_info, sheet_name='bus', usecols=[0, 1])  
line_df = pd.read_excel(grid_info, sheet_name='line', usecols=[1, 3, 4, 8, 5])


# Move PCC as first element DataFrame
pcc_index = bus_df[bus_df.iloc[:, 1] == 'ES4'].index[0] #PCC is 'ES4' in this case. Change if must
bus_df = pd.concat([bus_df.loc[[pcc_index]], bus_df.drop(pcc_index)]).reset_index(drop=True)

# Create a dictionary to map bus indexes to bus names using bus data
bus_index_to_name = dict(zip(bus_df.iloc[:, 0], bus_df.iloc[:, 1]))

# Initialize nodes list using bus names from the bus dataframe
UG_load_nodes = bus_df.iloc[:, 1].tolist()

# Initialize edges list
UG_edges = []
for index, row in line_df.iterrows():
    from_bus_name = bus_index_to_name.get(row['from_bus'])
    to_bus_name = bus_index_to_name.get(row['to_bus'])
    susceptance = 2* np.pi * 50 * row['c_nf_per_km'] * row['length_km'] * 1e-9  #       2*pi*50Hz* C_nf * km * 10^-9
    # Append tuple to edges list if both bus names are found
    if from_bus_name and to_bus_name:
        UG_edges.append((from_bus_name, to_bus_name, susceptance))





# Output the nodes and edges
print("Number of nodes:", len(UG_load_nodes))
print("\n")
print("Nodes:", UG_load_nodes)
print("\n")
print("Number of edges:", len(UG_edges))
print("\n")
print("Edges:", UG_edges)
print("\n")