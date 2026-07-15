import pandapower as pp
import pandas as pd
import pandapower.plotting as plot
import matplotlib.pyplot as plt
import os
import numpy as np



excel_file = r'C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\uni_grid_mod.xlsx'
loads_ts_path =r'C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\grid_sim\results\aggregated_bus_time_series.csv'
pv_ts_path =r'C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_timeseries\2nd_try_200kWh\res_net_output.csv'
storage_ts_path = r'C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_timeseries\2nd_try_200kWh\battery_total.csv'
# --- Create empty network ---
net = pp.create_empty_network()

# --- Load bus and line sheets ---
bus_df = pd.read_excel(excel_file, sheet_name='bus', index_col=0)
line_df = pd.read_excel(excel_file, sheet_name='line', index_col=0)


# --- Create buses and mappings ---
bus_map = {}    # bus_id -> pandapower bus index
bus_names = {}  # bus_id -> bus name
for bus_id in bus_df.index:
    vn_kv = bus_df.at[bus_id, 'vn_kv']
    name = bus_df.at[bus_id, 'name']
    bus_idx = pp.create_bus(net, vn_kv=vn_kv, name=name)
    bus_map[bus_id] = bus_idx
    bus_names[bus_id] = name

# --- Remove buses 55 and 56 ---
for bus_to_drop in [65, 66]:
    if bus_to_drop in bus_map:
        pp.drop_buses(net, [bus_map[bus_to_drop]])

# --- Create external grid at bus 33 (index 32 in net.bus) ---
pp.create_ext_grid(net, bus=net.bus.index[32], vm_pu=1.0, name="External Grid")

# --- Create lines (skip those connected to removed buses) ---
removed_buses = [65, 66]
for line_id in line_df.index:
    from_bus = line_df.at[line_id, 'from_bus']
    to_bus = line_df.at[line_id, 'to_bus']
    if from_bus in removed_buses or to_bus in removed_buses:
        continue

    from_bus_idx = bus_map[from_bus]
    to_bus_idx = bus_map[to_bus]

    pp.create_line_from_parameters(
        net,
        from_bus=from_bus_idx,
        to_bus=to_bus_idx,
        length_km=line_df.at[line_id, 'length_km'],
        r_ohm_per_km=line_df.at[line_id, 'r_ohm_per_km'],
        x_ohm_per_km=line_df.at[line_id, 'x_ohm_per_km'],
        c_nf_per_km=line_df.at[line_id, 'c_nf_per_km'],
        max_i_ka=line_df.at[line_id, 'max_i_ka'],
        name=line_df.at[line_id, 'name']
    )

# --- Load time series ---
loads_ts_df = pd.read_csv(loads_ts_path, sep=';')
pv_ts_df = pd.read_csv(pv_ts_path, sep=';')
storage_ts_df = pd.read_csv(storage_ts_path, sep=',')


# --- Create loads (buses 0-32 and 34-44) ---
load_bus_ids = list(range(0, 33)) + list(range(34, 45))
load_map = {}
for bus_id in load_bus_ids:
    if bus_id in bus_map:
        load_idx = pp.create_load(net, bus=bus_map[bus_id], p_mw=0, q_mvar=0, name=f"Load_{bus_id}")
        load_map[bus_id] = load_idx

# --- Create PV generators (buses 45-54) ---
pv_bus_ids = list(range(45, 54))
pv_map = {}
for bus_id in pv_bus_ids:
    if bus_id in bus_map:
        sgen_idx = pp.create_sgen(net, bus=bus_map[bus_id], p_mw=0, q_mvar=0, name=f"PV_{bus_id}")
        pv_map[bus_id] = sgen_idx

storage_bus_ids = list(range(55, 64))
storage_map = {}

for bus_id in storage_bus_ids:
    bus_idx = bus_map.get(bus_id)
    if bus_idx is not None:
        storage_idx = pp.create_storage(
            net,
            bus=bus_idx,
            p_mw=0,
            max_e_mwh=0.2,
            soc_percent=50,
            max_p_mw=0.2,
            min_p_mw=-0.2,
            efficiency_percent=100,
            name=f"Storage_{bus_id}"
        )
        storage_map[bus_id] = storage_idx

# --- Prepare name-to-bus_id dict ---
name_to_bus_id = {name: bus_id for bus_id, name in bus_names.items()}

# --- Map CSV columns to bus IDs, only columns that exist in bus names ---
load_columns_map = {col: name_to_bus_id[col] for col in loads_ts_df.columns if col in name_to_bus_id}
pv_columns_map = {col: name_to_bus_id[col] for col in pv_ts_df.columns if col in name_to_bus_id}
storage_columns_map = {col: name_to_bus_id[col] for col in storage_ts_df.columns if col in name_to_bus_id}


# --- Prepare results storage ---
voltage_results = pd.DataFrame(index=loads_ts_df.index, columns=net.bus['name'])


# Prepare lists outside the loop to store results
line_flows_from_all_p = []
line_flows_to_all_p = []
line_flows_from_all_q = []
line_flows_to_all_q = []


# --- Simulation loop ---
for timestep in range(288):
    # Update loads (assumed already in MW)
    for csv_name, bus_id in load_columns_map.items():
        if bus_id in load_map:
            net.load.at[load_map[bus_id], 'p_mw'] = loads_ts_df.at[timestep, csv_name]

    # Update PVs (convert W to MW)
    for csv_name, bus_id in pv_columns_map.items():
        if bus_id in pv_map:
            raw_p = pv_ts_df.at[timestep, csv_name]
            net.sgen.at[pv_map[bus_id], 'p_mw'] = raw_p / 1e6
    
    for csv_name, bus_id in storage_columns_map.items():
        storage_idx = storage_map.get(bus_id)
        if storage_idx is not None:
            p_mw = storage_ts_df.at[timestep, csv_name]
            net.storage.at[storage_idx, 'p_mw'] = p_mw/ 1e6

    # Run power flow
    pp.runpp(net)

    # Collect active power line flows
    line_flows_from_all_p.append(net.res_line["p_from_mw"].values)
    line_flows_to_all_p.append(net.res_line["p_to_mw"].values)

    # Collect reactive power line flows
    line_flows_from_all_q.append(net.res_line["q_from_mvar"].values)
    line_flows_to_all_q.append(net.res_line["q_to_mvar"].values)


    # Optional: detailed line flows printout
    for line_idx, line_data in net.line.iterrows():
        from_bus_name = net.bus.at[line_data["from_bus"], "name"]
        to_bus_name = net.bus.at[line_data["to_bus"], "name"]
        p_from = net.res_line.at[line_idx, "p_from_mw"]
        p_to = net.res_line.at[line_idx, "p_to_mw"]
        q_from = net.res_line.at[line_idx, "q_from_mvar"]
        q_to = net.res_line.at[line_idx, "q_to_mvar"]
        print(f"Line '{line_data['name']}': {from_bus_name} -> {to_bus_name} | "
              f"P_from = {p_from:.3f} MW, P_to = {p_to:.3f} MW, "
              f"Q_from = {q_from:.3f} MVAr, Q_to = {q_to:.3f} MVAr")




output_folder = r'C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\2_PandaPower_compare'
os.makedirs(output_folder, exist_ok=True)

# Convert lists to DataFrames
line_flows_from_p_df = pd.DataFrame(np.array(line_flows_from_all_p), columns=net.line['name'], index=range(len(line_flows_from_all_p)))
line_flows_to_p_df = pd.DataFrame(np.array(line_flows_to_all_p), columns=net.line['name'], index=range(len(line_flows_to_all_p)))

# Save CSVs
line_flows_from_p_df.to_csv(os.path.join(output_folder, 'line_flows_from_p.csv'), sep=',')
line_flows_to_p_df.to_csv(os.path.join(output_folder, 'line_flows_to_p.csv'), sep=',')

print(f"Results saved to {output_folder}")

# Calculate net active power flow per line
net_line_flow_p_df = line_flows_from_p_df - line_flows_to_p_df

# Save the net line flows CSV
net_line_flow_p_df.to_csv(os.path.join(output_folder, 'net_line_active_power_flow.csv'), sep=',')

print(f"Net active power line flows saved to {os.path.join(output_folder, 'net_line_active_power_flow.csv')}")