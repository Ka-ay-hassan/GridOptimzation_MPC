# This code aggregates the loads to the corresponding busses and removes loads of ES4/ES1/EnBW


import pandas as pd

# --- Step 1: Load and prepare CSV time series data ---
csv_path = "C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\grid_sim\\results\\timeseries_mw_2023.csv"
csv_df = pd.read_csv(csv_path)

# Drop the extra "Unnamed: 0" column if it exists (often an index)
if csv_df.columns[0].startswith('Unnamed'):
    csv_df = csv_df.drop(csv_df.columns[0], axis=1)

# Convert all CSV columns to numeric (in case they are read as strings)
for col in csv_df.columns:
    csv_df[col] = pd.to_numeric(csv_df[col], errors='coerce').fillna(0)

# --- Step 2: Read Excel data and build mapping from load to bus name ---
excel_path = "C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\grid_sim\\data\\uni_grid.xlsx"

# Read the "load" sheet from the Excel file, which contains load names and their bus IDs.
load_df = pd.read_excel(excel_path, sheet_name='load')
load_df['name'] = load_df['name'].astype(str).str.strip()
load_df['bus'] = pd.to_numeric(load_df['bus'], errors='coerce').fillna(-1).astype(int)
# Create mapping: load name -> bus id
load_to_busid = dict(zip(load_df['name'], load_df['bus']))

# Read the "bus" sheet from the Excel file, which contains all buses.
bus_df = pd.read_excel(excel_path, sheet_name='bus')
bus_df['bus_id'] = pd.to_numeric(bus_df.iloc[:, 0], errors='coerce').fillna(-1).astype(int)
bus_df['bus_name'] = bus_df.iloc[:, 1].astype(str).str.strip()
# Create mapping: bus id -> bus name
bus_mapping = dict(zip(bus_df['bus_id'], bus_df['bus_name']))

# Build final mapping: load name -> bus name (if available)
load_to_busname = {}
for load_name, bus_id in load_to_busid.items():
    bus_name = bus_mapping.get(bus_id)
    if bus_name is not None:
        load_to_busname[load_name] = bus_name
    else:
        print(f"Warning: No bus found for load '{load_name}' with bus id {bus_id}")

# Get the list of bus names in the proper order (sorted by bus id)
bus_list = bus_df.sort_values('bus_id')['bus_name'].tolist()

# --- Step 3: Aggregate the CSV load time series data by bus ---
# Create a DataFrame with the same index as csv_df and columns as the bus names, initializing with zeros.
agg_df = pd.DataFrame(0, index=csv_df.index, columns=bus_list)

# For each load (column in csv_df), add its time series to the corresponding bus column.
for col in csv_df.columns:
    load_name = str(col).strip()
    bus_name = load_to_busname.get(load_name)
    if bus_name:
        agg_df[bus_name] += csv_df[col]
    else:
        print(f"Warning: Load '{load_name}' not found in the Excel load mapping.")

# --- Step 3.5: Move 'ES4' column to the front if it exists ---
if 'ES4' in agg_df.columns:
    cols = ['ES4'] + [col for col in agg_df.columns if col != 'ES4']
    agg_df = agg_df[cols]

# --- Step 3.6: Remove specific buses (e.g., EnBW and ES1) if they exist ---
buses_to_remove = ['EnBW', 'ES1', 'ES4']
#buses_to_remove = ['ES1', 'ES4']
#buses_to_remove = ['EnBW', 'ES1']
#buses_to_remove = ['ES4']

agg_df = agg_df.drop(columns=[bus for bus in buses_to_remove if bus in agg_df.columns])

# --- Step 4: Save the aggregated time series to CSV ---
output_path = "C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\grid_sim\\results\\aggregated_bus_time_series.csv"
agg_df.to_csv(output_path, index=False)
print(f"Aggregation completed and saved to {output_path}")
