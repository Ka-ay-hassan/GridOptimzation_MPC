import pandas as pd
import numpy as np

# --- Step 1: Load grid data from Excel ---
grid_info = "C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\uni_grid_mod.xlsx"

# Load bus and line sheets
bus_df = pd.read_excel(grid_info, sheet_name='bus', usecols=[0, 1])
line_df = pd.read_excel(grid_info, sheet_name='line', usecols=[1, 3, 4, 8, 5])

# --- Step 2: Move PCC (ES4) to the top ---
pcc_index = bus_df[bus_df.iloc[:, 1] == 'ES4'].index[0]
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
        length_km = row['length_km']
        c_nf_per_km = row['c_nf_per_km']
        susceptance = 2 * np.pi * 50 * c_nf_per_km * length_km * 1e-9
        UG_edges.append((from_bus_name, to_bus_name, susceptance))

# --- Step 6: Filter out unconnected buses ---
connected_buses = set()
for from_bus, to_bus, _ in UG_edges:
    connected_buses.add(from_bus)
    connected_buses.add(to_bus)

bus_df = bus_df[bus_df.iloc[:, 1].isin(connected_buses)].reset_index(drop=True)
bus_index_to_name = dict(zip(bus_df.iloc[:, 0], bus_df.iloc[:, 1]))

excluded_nodes = ['ES4', 'Muff_AW-INFO', 'Muff_INFO-ETI', 'Muff_AW-ZHI', 'Muff_HKW-DLR', 'Muff_DLR-ATRIUM',
                'Muff_ZHI-HdM', 'Muff_AW-KZS1', 'Muff_AW-KZS2', 'Muff_IFF-ZAQ', 'Muff_ZAQ-IFKB',
                'Batt1_Muff_AW-INFO', 'Batt2_Muff_INFO-ETI', 'Batt3_Muff_AW-ZHI', 'Batt4_Muff_HKW-DLR',
                'Batt5_Muff_DLR-ATRIUM', 'Batt6_Muff_ZHI-HdM', 'Batt7_Muff_AW-KZS1', 'Batt8_Muff_AW-KZS2',
                'Batt9_Muff_IFF-ZAQ', 'Batt10_Muff_ZAQ-IFKB'
]

# Filter out the excluded nodes
UG_load_nodes = [node for node in bus_df.iloc[:, 1].tolist() if node not in excluded_nodes]

# # Only original connected buses (excluding the PCC --> ES4)
# UG_load_nodes = [node for node in bus_df.iloc[:, 1].tolist() if node != 'ES4']

# --- Step 7: Add RES and ESS nodes with calculated susceptance ---
RES_nodes = [ 'Muff_AW-INFO', 'Muff_INFO-ETI', 'Muff_AW-ZHI', 'Muff_HKW-DLR', 'Muff_DLR-ATRIUM',
                'Muff_ZHI-HdM', 'Muff_AW-KZS1', 'Muff_AW-KZS2', 'Muff_IFF-ZAQ', 'Muff_ZAQ-IFKB'
]

ESS_nodes = [
    'Batt1_Muff_AW-INFO', 'Batt2_Muff_INFO-ETI', 'Batt3_Muff_AW-ZHI', 'Batt4_Muff_HKW-DLR',
    'Batt5_Muff_DLR-ATRIUM', 'Batt6_Muff_ZHI-HdM', 'Batt7_Muff_AW-KZS1', 'Batt8_Muff_AW-KZS2',
    'Batt9_Muff_IFF-ZAQ', 'Batt10_Muff_ZAQ-IFKB'
]

added_nodes = RES_nodes + ESS_nodes


# ###############################################################################
# # Define manual connections with capacitance data (length_km, c_nf_per_km)
# ###############################################################################

# manual_edge_data = [
#     ('PV1', 'ARENA', 0.05, 200),
#     ('PV1', 'ESS1', 0.15, 100),
#     ('ESS1', 'ARENA', 0.05, 120),

#     ('PV2', 'HdM', 0.1, 180),
#     ('PV2', 'ESS2', 0.12, 200),
#     ('ESS2', 'HdM', 0.14, 190),

#     ('PV3', 'DLR', 0.4, 245),
#     ('PV3', 'ESS3', 0.3, 140),
#     ('ESS3', 'DLR', 0.08, 220),
# ]
# ###################################################################################
# ###################################################################################



# for from_node, to_node, length_km, c_nf_per_km in manual_edge_data:
#     susceptance = 2 * np.pi * 50 * c_nf_per_km * length_km * 1e-9
#     UG_edges.append((from_node, to_node, susceptance))

# --- Step 8: Final combined node list ---
UG_nodes = UG_load_nodes + added_nodes

# Ensure 'ES4' is the first node if it's in the connected graph
if 'ES4' in connected_buses:
    UG_nodes = ['ES4'] + [node for node in UG_nodes if node != 'ES4']


# #--- Output the results ---
# print("Number of nodes:", len(UG_nodes))
# print("\nComplete Nodes:", UG_nodes)

# print("\nNumber of load nodes:", len(UG_load_nodes))
# print("Load Nodes:", UG_load_nodes)

# print("\nNumber of edges:", len(UG_edges))
# print("Edges:", UG_edges)
