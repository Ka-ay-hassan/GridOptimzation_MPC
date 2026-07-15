import pandas as pd
import numpy as np

# --- Step 1: Load grid data from Excel ---
grid_info = "C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\uni_grid_mod.xlsx"

# Load bus and line sheets
bus_df = pd.read_excel(grid_info, sheet_name='bus', usecols=[0, 1])
line_df = pd.read_excel(grid_info, sheet_name='line', usecols=[1, 3, 4, 5, 6, 7, 8])

# --- Step 2: Move PCC (ES4) to the top ---
pcc_index = bus_df[bus_df.iloc[:, 1] == 'PCC'].index[0]
bus_df = pd.concat([bus_df.loc[[pcc_index]], bus_df.drop(pcc_index)]).reset_index(drop=True)

# --- Step 3: Create mapping from bus index to name ---
bus_index_to_name = dict(zip(bus_df.iloc[:, 0], bus_df.iloc[:, 1]))

# --- Step 4: Initialize UG_load_nodes and edges ---
UG_load_nodes = bus_df.iloc[:, 1].tolist()
UG_edges = []

# --- Step 5: Build edges from line data with susceptance calculation ---
for _, row in line_df.iterrows():
    from_bus_name = bus_index_to_name.get(row['from_bus'])
    to_bus_name = bus_index_to_name.get(row['to_bus'])
    if from_bus_name and to_bus_name:

        length_km = row['length_km'] # l

        c_nf_per_km = row['c_nf_per_km'] # C'
        x_ohm_per_km = row['x_ohm_per_km'] # X'
        r_ohm_per_km = row['r_ohm_per_km'] # R'

        C_nf = c_nf_per_km * length_km
        X_ohm = x_ohm_per_km * length_km
        R_ohm = r_ohm_per_km * length_km

        shunt_susceptance = 2 * np.pi * 50 * C_nf * 1e-9 # b_shunt
        susceptance = - X_ohm/(np.square(R_ohm) + np.square(X_ohm)) # X/(X^2 + R^2)
        admittance = R_ohm/(np.square(R_ohm) + np.square(X_ohm)) # R/(X^2 + R^2)

        UG_edges.append((from_bus_name, to_bus_name, shunt_susceptance, susceptance, admittance))

# --- Step 6: Filter out unconnected buses ---
connected_buses = set()
for from_bus, to_bus, _, _, _ in UG_edges:
    connected_buses.add(from_bus)
    connected_buses.add(to_bus)

bus_df = bus_df[bus_df.iloc[:, 1].isin(connected_buses)].reset_index(drop=True)
bus_index_to_name = dict(zip(bus_df.iloc[:, 0], bus_df.iloc[:, 1]))

# Only original connected buses (excluding the PCC --> ES4)
UG_load_nodes = [node for node in bus_df.iloc[:, 1].tolist() if node != 'ES4']

# # --- Step 7: Add RES and ESS nodes with calculated susceptance ---
# RES_nodes = ['PV1', 'PV2', 'PV3']
# ESS_nodes = ['ESS1', 'ESS2', 'ESS3']
# added_nodes = RES_nodes + ESS_nodes


# ###############################################################################
# # Define manual connections with capacitance data (length_km, c_nf_per_km, x_ohm_per_km, r_ohm_per_km)
# ###############################################################################

# manual_edge_data = [
#     ('PV1', 'ARENA', 0.05, 495, 0.1 , 0.1),
#     ('PV1', 'ESS1', 0.15, 495, 0.1, 0.1),
#     ('ESS1', 'ARENA', 0.05, 495, 0.1, 0.1),

#     ('PV2', 'HdM', 0.1, 500, 0.1, 0.1),
#     ('PV2', 'ESS2', 0.12, 500, 0.1, 0.1),
#     ('ESS2', 'HdM', 0.14, 500, 0.1, 0.1),

#     ('PV3', 'DLR', 0.4, 310, 0.1, 0.1),
#     ('PV3', 'ESS3', 0.3, 310, 0.1, 0.1),
#     ('ESS3', 'DLR', 0.08, 456, 0.1, 0.1),
# ]
# ###################################################################################
# ###################################################################################



# for from_node, to_node, length_km, c_nf_per_km, x_ohm_per_km, r_ohm_per_km in manual_edge_data:

#     C_nf = c_nf_per_km * length_km
#     X_ohm = x_ohm_per_km * length_km
#     R_ohm = r_ohm_per_km * length_km

#     shunt_susceptance = 2 * np.pi * 50 * c_nf_per_km * length_km * 1e-9
#     susceptance = - X_ohm/(np.square(R_ohm) + np.square(X_ohm)) # X/(X^2 + R^2)
#     admittance = R_ohm/(np.square(R_ohm) + np.square(X_ohm)) # R/(X^2 + R^2)

#     UG_edges.append((from_node, to_node, shunt_susceptance, susceptance, admittance))

# # --- Step 8: Final combined node list ---
# UG_nodes = UG_load_nodes + added_nodes

# # Ensure 'ES4' is the first node if it's in the connected graph
# if 'ES4' in connected_buses:
#     UG_nodes = ['ES4'] + [node for node in UG_nodes if node != 'ES4']


# #--- Output the results ---
# print("Number of nodes:", len(UG_nodes))
# print("\nComplete Nodes:", UG_nodes)

# print("\nNumber of load nodes:", len(UG_load_nodes))
# print("Load Nodes:", UG_load_nodes)

print("\nNumber of edges:", len(UG_edges))
print("Edges:", UG_edges)
