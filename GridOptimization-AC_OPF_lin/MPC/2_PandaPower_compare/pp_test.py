import pandapower as pp
import pandas as pd
import os


# save plot path
plot_path = r'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\ACOPF.html'

# Load path
agg_load_path = r'C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\grid_sim\results\aggregated_bus_time_series.csv'

# RES path
pv_path = r'C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_results\3rd_try\res_net_active.csv'
pv_reactive_path = r'C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_results\3rd_try\res_net_reactive.csv'

# ESS path
ess_active_path = r'C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_results\3rd_try\batt_total_active.csv'
ess_reactive_path= r'C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_results\3rd_try\batt_total_reactive.csv'


# Load CSV data into DataFrames
df_load = pd.read_csv(agg_load_path, sep=',', index_col=0)  # or adjust sep if needed
pv_active_df = pd.read_csv(pv_path, sep=',', index_col=0)
pv_reactive_df = pd.read_csv(pv_reactive_path, sep=',', index_col=0)
ess_active_df = pd.read_csv(ess_active_path, sep=',', index_col=0)
ess_reactive_df = pd.read_csv(ess_reactive_path, sep=',', index_col=0)


# print("ESS active shape:", ess_active_df.shape)
# print(ess_active_df.head())





net = pp.create_empty_network(name='acopf')

pcc = pp.create_bus(net, vn_kv = 10., name ='PCC')

load1 = pp.create_bus(net, vn_kv = 10., name ='Load1')
load2 = pp.create_bus(net, vn_kv = 10., name ='Load2')

res1 = pp.create_bus(net, vn_kv = 10., name ='RES1')
res2 = pp.create_bus(net, vn_kv = 10., name ='RES2')

ess1 = pp.create_bus(net, vn_kv = 10., name ='ESS1')
ess2 = pp.create_bus(net, vn_kv = 10., name ='ESS2')


pp.create_ext_grid(net, pcc, vm_pu=1.0, name='external grid')

pp.create_line_from_parameters(net, pcc, load1, length_km=0.929 , r_ohm_per_km =0.0601,x_ohm_per_km=0.103358, c_nf_per_km=495, max_i_ka =0.588,  name = 'PCC-Load1')
pp.create_line_from_parameters(net, pcc, load2, length_km=0.929 , r_ohm_per_km =0.0601,x_ohm_per_km=0.103358, c_nf_per_km=495, max_i_ka =0.588,  name = 'PCC-Load2')

pp.create_line_from_parameters(net, ess1, load1, length_km=0.46 , r_ohm_per_km =0.1,x_ohm_per_km=0.103358, c_nf_per_km=495, max_i_ka =0.467,  name = 'ESS1-Load1')
pp.create_line_from_parameters(net, res1, load1, length_km=0.31 , r_ohm_per_km =0.1,x_ohm_per_km=0.100531, c_nf_per_km=500, max_i_ka =0.435,  name = 'RES1-Load1')
pp.create_line_from_parameters(net, res1, ess1, length_km=0.25 , r_ohm_per_km =0.1,x_ohm_per_km=0.103358, c_nf_per_km=495, max_i_ka =0.467,  name = 'RES1-ESS1')

pp.create_line_from_parameters(net, ess2, load2, length_km=0.34 , r_ohm_per_km =0.1,x_ohm_per_km=0.103358, c_nf_per_km=495, max_i_ka =0.467,  name = 'ESS2-Load2')
pp.create_line_from_parameters(net, res2, load2, length_km=0.38 , r_ohm_per_km =0.1,x_ohm_per_km=0.100531, c_nf_per_km=500, max_i_ka =0.435,  name = 'RES2-Load2')
pp.create_line_from_parameters(net, res2, ess2, length_km=0.1 , r_ohm_per_km =0.1,x_ohm_per_km=0.100531, c_nf_per_km=500, max_i_ka =0.435,  name = 'RES2-ESS2')

pp.create_line_from_parameters(net, load1, load2, length_km=0.31 , r_ohm_per_km =0.1,x_ohm_per_km=0.100531, c_nf_per_km=500, max_i_ka =0.435,  name = 'Load1-Load2')



# --- Create all elements once before the loop ---
pp.create_load(net, load1, p_mw=0, q_mvar=0)
pp.create_load(net, load2, p_mw=0, q_mvar=0)

pp.create_sgen(net, res1, p_mw=0, q_mvar=0, in_service=True, max_p_mw=5.0)
pp.create_sgen(net, res2, p_mw=0, q_mvar=0, in_service=True, max_p_mw=5.0)

pp.create_storage(net, ess1, p_mw=0, q_mvar=0, max_e_mwh=4.95)
pp.create_storage(net, ess2, p_mw=0, q_mvar=0, max_e_mwh=4.95)


# --- Loop over time steps and update powers ---
n_steps = min(len(df_load), len(pv_active_df), len(ess_active_df))  # Safety limit

line_flows_from_all_p = []
line_flows_to_all_p = []
line_flows_from_all_q = []
line_flows_to_all_q = []
voltage_all = []
voltage_angle_all = []


for i in range(n_steps):
    # Update loads
    net.load.at[0, 'p_mw'] = df_load.iloc[i, 1] *10
    net.load.at[1, 'p_mw'] = df_load.iloc[i, 2] *10
    net.load.at[0, 'q_mvar'] = df_load.iloc[i, 1] * 0.05 *10 # Adjust if needed
    net.load.at[1, 'q_mvar'] = df_load.iloc[i, 2] * 0.05 *10
    
    # Update PV generators (sgen)
    net.sgen.at[0, 'p_mw'] = pv_active_df.iloc[i, 0]
    net.sgen.at[1, 'p_mw'] = pv_active_df.iloc[i, 1]
    net.sgen.at[0, 'q_mvar'] = pv_reactive_df.iloc[i, 0]
    net.sgen.at[1, 'q_mvar'] = pv_reactive_df.iloc[i, 1]
    
    # Update ESS (storage)
    net.storage.at[0, 'p_mw'] = ess_active_df.iloc[i, 0]
    net.storage.at[1, 'p_mw'] = ess_active_df.iloc[i, 1]
    net.storage.at[0, 'q_mvar'] = ess_reactive_df.iloc[i, 0]
    net.storage.at[1, 'q_mvar'] = ess_reactive_df.iloc[i, 1]
    
    # Run power flow
    pp.runpp(net)
    
    # Collect active power line flows
    line_flows_from_all_p.append(net.res_line["p_from_mw"].values)
    line_flows_to_all_p.append(net.res_line["p_to_mw"].values)
    
    # Collect reactive power line flows
    line_flows_from_all_q.append(net.res_line["q_from_mvar"].values)
    line_flows_to_all_q.append(net.res_line["q_to_mvar"].values)
    
    # Optionally print bus voltages and line loadings
    #print(f"Timestep {i} voltages (pu):\n", net.res_bus.vm_pu)
    # Collect voltages (in pu) for all buses
    voltage_all.append(net.res_bus["vm_pu"].values)

    # Collect voltage angles in degrees
    voltage_angle_all.append(net.res_bus["va_degree"].values)
    
    # Optional detailed line flows print
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

# After the loop, convert collected data to DataFrames for saving or analysis
df_line_flows_from_p = pd.DataFrame(line_flows_from_all_p, columns=net.line["name"])
df_line_flows_to_p = pd.DataFrame(line_flows_to_all_p, columns=net.line["name"])
df_line_flows_from_q = pd.DataFrame(line_flows_from_all_q, columns=net.line["name"])
df_line_flows_to_q = pd.DataFrame(line_flows_to_all_q, columns=net.line["name"])


save_path = r"C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\3_compare\\"
os.makedirs(save_path, exist_ok=True)

# Example: save to CSV files
df_line_flows_from_p.to_csv(save_path + "pp_line_flows_from_active.csv", sep=',')
df_line_flows_to_p.to_csv(save_path + "pp_line_flows_to_active.csv", sep=',')
df_line_flows_from_q.to_csv(save_path + "pp_line_flows_from_reactive.csv", sep=',')
df_line_flows_to_q.to_csv(save_path + "pp_line_flows_to_reactive.csv", sep=',')




df_voltages = pd.DataFrame(voltage_all, columns=net.bus["name"])
df_voltages.to_csv(save_path + "pp_bus_voltages_pu.csv", sep=',')

df_voltage_angles = pd.DataFrame(voltage_angle_all, columns=net.bus["name"])
df_voltage_angles.to_csv(save_path + "pp_bus_voltage_angles_deg.csv", sep=',')




# print(net)
# print(net.res_bus.vm_pu)
# print(net.res_line.loading_percent)




#pp.plotting.to_html(net, plot_path)

# pp.plotting.plotly.simple_plotly(net,
#                                      respect_switches=True,
#                                      map_style='basic',
#                                      figsize=1.0,
#                                      aspectratio='auto', 
#                                      line_width=1.0, 
#                                      bus_size=10.0, 
#                                      ext_grid_size=20.0, 
#                                      bus_color='blue', 
#                                      line_color='grey', 
#                                      trafo_color='green', 
#                                      trafo3w_color='dark green', 
#                                      ext_grid_color='yellow', 
#                                      filename= plot_path, 
#                                      auto_open=True, 
#                                      showlegend=True, 
#                                      additional_traces=None)
