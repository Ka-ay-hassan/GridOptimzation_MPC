import os
import math
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
import cvxpy as cvx
import matplotlib.pyplot as plt
from MPC import MPC_Battery_PCC_RES  # Multi-node-capable MPC class
from grid2DCpf import UG_edges, UG_nodes, UG_load_nodes, RES_nodes, ESS_nodes
#from old_grid2DCpf import UG_load_nodes

class CentralController(MPC_Battery_PCC_RES):
    def __init__(self):
        #DO NOT CHANGE ORDER OF FUNCTION INITIALIZATION!
        super().__init__()
        self.print_parameters()
        # self._compute_F_tilde() # --> prolly not needed as its used in init_pcc_dcpf()
        self.init_res()
        self.init_batt()
        self.init_demand()

        self.init_pcc()
        self.init_pcc_dcpf()
        self.problem = cvx.Problem(cvx.Minimize(self.cost), self.constraints)


    def print_parameters(self):

        factor = 1000

        print("Battery Parameters:")
        print(f"  Battery capacity (c_batt): {self.c_batt/factor} kWh")
        print(f"  Battery cost (batt_cost): {self.batt_cost/factor} €/kWh")
        print(f"  Battery efficiency (eta_batt): {self.eta_batt/factor}")
        print(f"  Maximum battery power (p_batt_max): {self.p_batt_max/factor} kW")
        print(f"  Initial state of charge (soc_init): {self.soc_init/factor}\n")

        print("PV Parameters:")
        print(f"  Maximum net generation of PV (p_res_max): {self.p_res_max} kW")
        print(f"  Curtailment cost (c_curtail): {self.c_curtail} €/kWh\n")

        print("Grid Parameters:")
        print(f"  Maximum grid power (p_grid_max): {self.p_grid_max} kW\n")    



    def step(self, step_config):
        # Update RES for each RES node
        for res in self.res_nodes:
            self.cvx_parameters["p_RES"][res].project_and_assign(step_config["p_RES"][res][:self.n_hor])
        
        # Update demand for each load node
        for loads in self.load_nodes:
            self.cvx_parameters["p_demand"][loads].project_and_assign(step_config["p_demand"][loads][:self.n_hor])
        
        # Cost of feeding in or drawing electricty from grid
        self.cvx_parameters["cost_feedin"].project_and_assign(step_config["cost_feedin"][:self.n_hor])
        self.cvx_parameters["cost_draw"].project_and_assign(step_config["cost_draw"][:self.n_hor])

        # Assign line thermal limits
        self.cvx_parameters["line_limits"].project_and_assign(step_config["line_limits"])

        ## Debug: print the key input values
        # print("\n===== DEBUG: Step Inputs =====")
        # for res in self.res_nodes:
        #     print(f"{res} RES power (first 5): {step_config['p_RES'][res][:5]}")

        # for load in self.load_nodes:
        #     print(f"{load} demand (first 5): {step_config['p_demand'][load][:5]}")

        # print("cost_draw (first 5):", step_config['cost_draw'][:5])
        # print("cost_feedin (first 5):", step_config['cost_feedin'][:5])
        # print("line_limits:", step_config['line_limits'])
        # print("SOC_initial:", step_config.get("SOC_initial", "N/A"))

        # 🔁 Solve
        result = self.problem.solve(solver=cvx.GUROBI, verbose=True, reoptimize=True)

        #  #Handle failure
        # if self.problem.status not in ["optimal", "optimal_inaccurate"]:
        #     print(" Optimization failed.")
        #     print("Problem status:", self.problem.status)
        #     print("Objective value:", self.problem.value)
        #     raise ValueError(f"Optimization failed: {self.problem.status}")



    def post_process(self):
        gamma_grid_rounded = np.round(self.cvx_variables["gamma_grid"].value).astype(int)
        p_grid_draw_final = self.cvx_variables["p_grid_draw"].value * (1 - gamma_grid_rounded)
        p_grid_feedin_final = self.cvx_variables["p_grid_feedin"].value * gamma_grid_rounded
        return p_grid_draw_final, p_grid_feedin_final

    

    def save_results_to_csv(self, start_datetime_str="2023-01-01 00:00", interval_min=15):
        # Create time index
        start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
        time_index = [start_dt + timedelta(minutes=interval_min * i) for i in range(self.n_hor)]
        time_str_index = [dt.strftime("%d.%m.%Y %H:%M") for dt in time_index]

        # --- Battery charge ---
        batt_charge_data = {
            ess: self.cvx_variables["p_batt_charge"][ess].value for ess in self.ess_nodes
        }
        df_batt_charge = pd.DataFrame(batt_charge_data, index=time_str_index)
        df_batt_charge.index.name = "time"
        df_batt_charge.to_csv("C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\1_mpc_timeseries\\battery_charge.csv",sep=',')

        # --- Battery discharge ---
        batt_discharge_data = {
            ess: self.cvx_variables["p_batt_discharge"][ess].value for ess in self.ess_nodes
        }
        df_batt_discharge = pd.DataFrame(batt_discharge_data, index=time_str_index)
        df_batt_discharge.index.name = "time"
        df_batt_discharge.to_csv("C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\1_mpc_timeseries\\battery_discharge.csv",sep=',')

        # --- Net RES output ---
        res_net_data = {
            res: self.cvx_variables["p_RES_net"][res].value for res in self.res_nodes
        }
        df_res_net = pd.DataFrame(res_net_data, index=time_str_index)
        df_res_net.index.name = "time"
        df_res_net.to_csv("C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\1_mpc_timeseries\\res_net_output.csv",sep=',')


        # --- Line flows (pe_e) ---
        # Create line names like "fromNode-toNode"
        line_names = []
        for edge in self.edges:
            # Assuming edge is tuple/list: (from_node, to_node, ...)
            from_node = edge[0]
            to_node = edge[1]
            line_names.append(f"{from_node}-{to_node}")

        pe_e_values = self.cvx_variables["pe_e"].value  # shape: (num_edges, n_hor)
        df_line_flows = pd.DataFrame(pe_e_values.T, columns=line_names, index=time_str_index)
        df_line_flows.index.name = "time"
        df_line_flows.to_csv("C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\1_mpc_timeseries\\line_flows.csv",sep=',')

        # --- Grid powers separately ---
        p_grid_draw = self.cvx_variables["p_grid_draw"].value
        p_grid_feedin = self.cvx_variables["p_grid_feedin"].value
        p_grid = p_grid_draw - p_grid_feedin

        # Save PCC (net grid power)
        df_pcc = pd.DataFrame({"PCC": p_grid}, index=time_str_index)
        df_pcc.index.name = "time"
        df_pcc.to_csv("C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\1_mpc_timeseries\\PCC.csv",sep=',')

        # Save p_grid_draw
        df_draw = pd.DataFrame({"p_grid_draw": p_grid_draw}, index=time_str_index)
        df_draw.index.name = "time"
        df_draw.to_csv("C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\1_mpc_timeseries\\p_grid_draw.csv",sep=',')

        # Save p_grid_feedin
        df_feedin = pd.DataFrame({"p_grid_feedin": p_grid_feedin}, index=time_str_index)
        df_feedin.index.name = "time"
        df_feedin.to_csv("C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\1_mpc_timeseries\\p_grid_feedin.csv",sep=',')

        print("Saved battery charge, discharge and RES net output CSV files.")




    def plot_results(self, p_grid_draw_final, p_grid_feedin_final):

        factor = 1000  # Convert from W to kW

        # ---------------------------------------------
        # Automated Battery plotting in groups of 5 ESS nodes
        # ---------------------------------------------
        chunk_size = 5
        num_ess = len(self.ess_nodes)
        num_chunks = math.ceil(num_ess / chunk_size)

        for chunk_idx in range(num_chunks):
            start_idx = chunk_idx * chunk_size
            end_idx = min(start_idx + chunk_size, num_ess)
            group_ess_nodes = self.ess_nodes[start_idx:end_idx]

            fig_batt, axs_batt = plt.subplots(3, 1, figsize=(12, 10), constrained_layout=True)
            fig_batt.suptitle(f"Battery Performance - Group {chunk_idx + 1}", fontsize=16)

            # State of Charge (SOC)
            for ess in group_ess_nodes:
                axs_batt[0].plot(self.cvx_variables["SOC_batt"][ess].value, label=f"SOC {ess}")
            #axs_batt[0].set_title("State of Charge (SOC)", fontsize=14)
            axs_batt[0].set_ylabel("SOC", fontsize=16)
            axs_batt[0].legend(fontsize=15)
            axs_batt[0].grid(True)
            axs_batt[0].tick_params(axis='both', labelsize=14)

            # Charging Power
            for ess in group_ess_nodes:
                axs_batt[1].plot(self.cvx_variables["p_batt_charge"][ess].value/factor, label=f"Charge {ess}")
            #axs_batt[1].set_title("Charging Power", fontsize=16)
            axs_batt[1].set_ylabel("Charging Power (kW)", fontsize=16)
            axs_batt[1].legend(fontsize=15)
            axs_batt[1].grid(True)
            axs_batt[1].tick_params(axis='both', labelsize=14)

            # Discharging Power
            for ess in group_ess_nodes:
                axs_batt[2].plot(self.cvx_variables["p_batt_discharge"][ess].value/factor, label=f"Discharge {ess}")
            #axs_batt[2].set_title("Discharging Power", fontsize=14)
            axs_batt[2].set_ylabel("Discharge Power (kW)", fontsize=16)
            axs_batt[2].legend(fontsize=15)
            axs_batt[2].grid(True)
            axs_batt[2].tick_params(axis='both', labelsize=14)


        # ---------------------------------------------
        # Automated RES plotting in groups of 5
        # ---------------------------------------------
        chunk_size = 5
        num_res = len(self.res_nodes)
        num_chunks = math.ceil(num_res / chunk_size)

        for chunk_idx in range(num_chunks):
            start_idx = chunk_idx * chunk_size
            end_idx = min(start_idx + chunk_size, num_res)
            group_res_nodes = self.res_nodes[start_idx:end_idx]

            fig_res, axs_res = plt.subplots(3, 1, figsize=(12, 10), constrained_layout=True)
            fig_res.suptitle(f"Renewable Energy (PV) - Group {chunk_idx + 1}", fontsize=16)

            # PV Generation
            for res in group_res_nodes:
                axs_res[0].plot(self.cvx_parameters["p_RES"][res].value/factor, label=f"PV {res}")
            #axs_res[0].set_title("PV Generation", fontsize=14)
            axs_res[0].set_ylabel("PV Generation (kW)", fontsize=16)
            axs_res[0].legend(fontsize=15)
            axs_res[0].grid(True)
            axs_res[0].tick_params(axis='both', labelsize=14)

            # Curtailment
            for res in group_res_nodes:
                axs_res[1].plot(self.cvx_variables["p_curtailment"][res].value/factor, label=f"Curtailment {res}")
            #axs_res[1].set_title("Curtailment", fontsize=14)
            axs_res[1].set_ylabel("Curtailment (kW)", fontsize=16)
            axs_res[1].legend(fontsize=15)
            axs_res[1].grid(True)
            axs_res[1].tick_params(axis='both', labelsize=14)

            # Net Renewable Output
            for res in group_res_nodes:
                axs_res[2].plot(self.cvx_variables["p_RES_net"][res].value/factor, label=f"Net Output {res}")
            #axs_res[2].set_title("Net Renewable Output", fontsize=14)
            axs_res[2].set_ylabel("Net PV (kW)", fontsize=16)
            axs_res[2].legend(fontsize=15)
            axs_res[2].grid(True)
            axs_res[2].tick_params(axis='both', labelsize=14)


        # -----------------------------
        # Figure 2: Aggregated Plots
        # -----------------------------
        fig2, axs2 = plt.subplots(4, 1, figsize=(12, 14))
        fig2.subplots_adjust(hspace=0.8)
        
        sum_demand = np.zeros_like(self.cvx_parameters["p_demand"][self.load_nodes[0]].value, dtype=float)
        for load in self.load_nodes:
            sum_demand += self.cvx_parameters["p_demand"][load].value
        axs2[0].plot(sum_demand/factor, label="Total Demand (kW)", color="black")
        #axs2[0].set_title("Total Load Demand", fontsize=16)
        axs2[0].set_ylabel("Total Demand", fontsize=16)
        axs2[0].legend(fontsize=15)
        axs2[0].grid(True)
        axs2[0].tick_params(axis='both', labelsize=14)

        sum_res = np.zeros_like(self.cvx_variables["p_RES_net"][self.res_nodes[0]].value, dtype=float)
        for res in self.res_nodes:
            sum_res += self.cvx_variables["p_RES_net"][res].value
        axs2[1].plot(sum_res/factor, label="Total RES Generation (kW)", color="green")
        #axs2[1].set_title("Total Renewable Energy Generation", fontsize=16)
        axs2[1].set_ylabel("Total RES", fontsize=16)
        axs2[1].legend(fontsize=15)
        axs2[1].grid(True)
        axs2[1].tick_params(axis='both', labelsize=14)

        sum_charge = np.zeros_like(self.cvx_variables["p_batt_charge"][self.ess_nodes[0]].value, dtype=float)
        sum_discharge = np.zeros_like(self.cvx_variables["p_batt_discharge"][self.ess_nodes[0]].value, dtype=float)
        for ess in self.ess_nodes:
            sum_charge += self.cvx_variables["p_batt_charge"][ess].value
            sum_discharge += self.cvx_variables["p_batt_discharge"][ess].value
        axs2[2].plot(sum_charge/factor, label="Total Battery Charge (kW)", color="blue")
        axs2[2].plot(sum_discharge/factor, label="Total Battery Discharge (kW)", color="red")
        #axs2[2].set_title("Total Battery Power", fontsize=16)
        axs2[2].set_ylabel("Battery Power", fontsize=16)
        axs2[2].legend(fontsize=15)
        axs2[2].grid(True)
        axs2[2].tick_params(axis='both', labelsize=14)

        axs2[3].plot(self.cvx_parameters["cost_feedin"].value/factor, label="Feed-in Price", color="purple")
        axs2[3].plot(self.cvx_parameters["cost_draw"].value/factor, label="Draw Price", color="orange")
        #axs2[3].set_title("Electricity Prices", fontsize=16)
        axs2[3].set_ylabel("Prices (€/kWh)", fontsize=16)
        axs2[3].legend(fontsize=15)
        axs2[3].grid(True)
        axs2[3].tick_params(axis='both', labelsize=14)

        plt.tight_layout(pad=3.0)

        # -------------------------------------------------
        # Figure 3: Line Flows (pe_e) in subplots
        # -------------------------------------------------
        num_edges = self.cvx_variables["pe_e"].value.shape[0]
        edges_per_subplot = [15, 15, 15, 15, num_edges - 60]
        fig3, axs3 = plt.subplots(5, 1, figsize=(14, 16), constrained_layout=True)
        fig3.suptitle("Line Flows", fontsize=18)

        edge_idx = 0
        for i, num in enumerate(edges_per_subplot):
            for _ in range(num):
                axs3[i].plot(self.cvx_variables["pe_e"].value[edge_idx, :]/factor, label=f"Line {edge_idx}")
                edge_idx += 1
            axs3[i].set_title("", fontsize=14)  # empty title but increased font size for consistency
            axs3[i].set_ylabel("Flow (kW)", fontsize=14)
            axs3[i].legend(fontsize=11, ncol=4)
            axs3[i].grid(True)
            axs3[i].tick_params(axis='both', labelsize=12)

        plt.tight_layout(pad=3.0)

        # ---------------------------------------------
        # Figure 4: Grid Power Overview
        # ---------------------------------------------
        p_grid = p_grid_draw_final - p_grid_feedin_final

        fig4, axs4 = plt.subplots(2, 1, figsize=(12, 8), constrained_layout=True)
        fig4.suptitle("Grid Power Overview", fontsize=16)

        # Net Grid Power
        axs4[0].plot(p_grid/factor, label="Net Grid Power")
        axs4[0].set_title("", fontsize=14)
        axs4[0].set_ylabel("Power (kW)", fontsize=20)
        axs4[0].legend(fontsize=18)
        axs4[0].grid(True)
        axs4[0].tick_params(axis='both', labelsize=18)

        # Grid Draw and Feed-in
        axs4[1].plot(p_grid_draw_final/factor, label="Grid Power Drawp")
        axs4[1].plot(-p_grid_feedin_final/factor, label="Grid Power Feed-in")
        axs4[1].set_title("", fontsize=14)
        axs4[1].set_ylabel("Power (kW)", fontsize=20)
        axs4[1].legend(fontsize=18)
        axs4[1].grid(True)
        axs4[1].tick_params(axis='both', labelsize=18)

        plt.show()


def test_electrical_side_of_mpc():
    demand_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\grid_sim\\results\\aggregated_bus_time_series.csv'
    #res_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\mpc_el_data_pv_only_cleaned.csv'
    res_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\combined_pv_outputs.csv'
    market_data_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\market_analysis_15min_converted.csv'
    line_lim_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\grid_sim\\data\\line_limits_dcpf.csv'


    # Define the time for the simulation
    time_intervals = 288                    # 24 hours
    #time_intervals = 10                  # 24 hours


 
    # Extract demand data 
    df_demand = pd.read_csv(demand_path)
    subset_df = df_demand.iloc[:, :len(UG_load_nodes)] # take the values stored up until the n-th load_node
    #print(subset_df.head())
    p_demand_data = subset_df * 1000   # Convert MW to kW
    

    ########################################### MARKET PRICE ASSIGNMENT ###################################################
    # Extract market price data
    df_market = pd.read_csv(market_data_path)
    # Adjust dimesnions of market data
    market_prices = df_market['Intraday_Auktion [Euro/MWh]'].values
    index_range = np.arange(0, len(market_prices) * 15, 5)
    draw_prices = np.interp(index_range, np.arange(0, len(market_prices) * 15, 15), market_prices)[:time_intervals] / 1000
    feedin_prices = -draw_prices

    df_prices = pd.DataFrame({
    'cost_feedin': feedin_prices,
    'cost_draw': draw_prices
    })

    cost_feedin = df_prices['cost_feedin'].values[:time_intervals]
    cost_draw = df_prices['cost_draw'].values[:time_intervals]


    ######################################### ADJUST RES DATA HERE!#######################################################
    # res_data = pd.read_csv(res_path)
    # p_res_data1 = res_data['pv_power'].values[:time_intervals] /1000  # W --> kW
    # p_res_data2 = res_data['pv_power'].values[:time_intervals] /1000
    # p_res_data3 = res_data['pv_power'].values[:time_intervals] /1000
    # p_res_data4 = res_data['pv_power'].values[:time_intervals] /1000  # W --> kW
    # p_res_data5 = res_data['pv_power'].values[:time_intervals] /1000
    # p_res_data6 = res_data['pv_power'].values[:time_intervals] /1000
    # p_res_data7 = res_data['pv_power'].values[:time_intervals] /1000  # W --> kW
    # p_res_data8 = res_data['pv_power'].values[:time_intervals] /1000
    # p_res_data9 = res_data['pv_power'].values[:time_intervals] /1000
    # p_res_data10 = res_data['pv_power'].values[:time_intervals] /1000



    # p_res_data = np.column_stack((p_res_data1, p_res_data2, p_res_data3,p_res_data4, p_res_data5, p_res_data6, p_res_data7,
    #                                p_res_data8, p_res_data9, p_res_data10))
    

    res_df = pd.read_csv(res_path)
    p_res_data = res_df.iloc[:, 1:11]/3

    


    controller = CentralController()

    ################################# SET LINE LIMITS: one value for each edge ##########################################
    line_lim_df = pd.read_csv(line_lim_path)
    line_limits = line_lim_df.iloc[:, 1]
    #line_limits = np.full(len(controller.edges), 10000.0) #this case all line values get 10000

    ############################################# STEP CONFIG FOR ONE NODE ##############################################
    # step_config = {
    #     "p_RES": p_res_data,
    #     "SOC_initial": 0.7,
    #     "p_demand": p_demand_data,
    #     "cost_feedin": cost_feedin,
    #     "cost_draw": cost_draw
    # }


    ################################### STEP CONFIG FOR MULTIPLE NODES! ###############################################
    step_config = {
    
    #"p_RES": {res: p_res_data[:, i] for i, res in enumerate(controller.res_nodes)},
    "p_RES": {res: p_res_data.iloc[:, i].values for i, res in enumerate(controller.res_nodes)},

    "p_demand": {load: p_demand_data.iloc[:, idx].values for idx, load in enumerate(controller.load_nodes)},
    "SOC_initial": {ess: 0.5 for ess in controller.ess_nodes},

    # Cost parameters provided as full time series arrays.
    "cost_feedin": cost_feedin,  # This array will be sliced inside step() if necessary.
    "cost_draw": cost_draw,       # Same here

    # Assignemt of line limits parameters
    "line_limits": line_limits,
    }

    controller.step(step_config)

    p_grid_draw_final, p_grid_feedin_final = controller.post_process()

    controller.save_results_to_csv()

    controller.plot_results(p_grid_draw_final, p_grid_feedin_final)

    


    print("MPC run complete!")

if __name__ == "__main__":
    test_electrical_side_of_mpc()