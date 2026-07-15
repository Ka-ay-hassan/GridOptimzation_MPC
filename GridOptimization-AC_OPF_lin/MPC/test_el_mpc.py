import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import cvxpy as cvx
import matplotlib.pyplot as plt
from MPC import MPC_Battery_PCC_RES  # Multi-node-capable MPC class
from grid2DCpf import UG_load_nodes


class CentralController(MPC_Battery_PCC_RES):
    def __init__(self):
        #DO NOT CHANGE ORDER OF FUNCTION INITIALIZATION!
        super().__init__()
        self.print_parameters()

        self.init_res()
        self.init_batt()
        self.init_demand()

        self.angle_constraints()
        self.voltage_constraints()
    

        
        self.acopf_pcc()

        self.problem = cvx.Problem(cvx.Minimize(self.cost), self.constraints)


    def print_parameters(self):
        print("Battery Parameters:")
        print(f"  Battery capacity (c_batt): {self.c_batt} MWh")
        print(f"  Battery cost (batt_cost): {self.batt_cost} €/kWh")
        print(f"  Battery efficiency (eta_batt): {self.eta_batt}")
        print(f"  Maximum battery power (p_batt_max): {self.p_batt_max} MW")
        print(f"  Initial state of charge (soc_init): {self.soc_init}\n")

        print("PV Parameters:")
        print(f"  Maximum net generation of PV (p_res_max): {self.p_res_max} MW")
        print(f"  Curtailment cost (c_curtail): {self.c_curtail} €/kWh\n")

        print("Grid Parameters:")
        print(f"  Maximum grid power (p_grid_max): {self.p_grid_max} MW\n")    



    def step(self, step_config):
        # 1) Load in all step parameters
        for res in self.res_nodes:
            self.cvx_parameters["p_RES"][res].project_and_assign(
                step_config["p_RES"][res][: self.n_hor]
            )
        for load in self.load_nodes:
            self.cvx_parameters["p_demand"][load].project_and_assign(
                step_config["p_demand"][load][: self.n_hor]
            )
        self.cvx_parameters["cost_feedin"].project_and_assign(
            step_config["cost_feedin"][: self.n_hor]
        )
        self.cvx_parameters["cost_draw"].project_and_assign(
            step_config["cost_draw"][: self.n_hor]
        )
        self.cvx_parameters["line_limits"].project_and_assign(
            step_config["line_limits"]
        )

        # 2) Solve the MPC
        result = self.problem.solve(
            solver=cvx.GUROBI,
            verbose=True,
            reoptimize=True,
          
        )

        # # === DEBUGGING: Inspect values ===
        # print("======== Debug: Active and Reactive Power Outputs ========")
        # for i in range(self.n_hor):
        #     print(f"\nStep {i}:")
        #     for res in self.res_nodes:
        #         p_res = self.cvx_variables["p_RES_net"][res].value[i] if res in self.cvx_variables["p_RES_net"] else 0
        #         q_res = self.cvx_variables["q_RES_net"][res].value[i] if res in self.cvx_variables["q_RES_net"] else 0
        #         print(f"  RES {res}: P = {p_res:.2f} kW, Q = {q_res:.2f} kVAr")
            
        #     for ess in self.ess_nodes:
        #         p_chg = self.cvx_variables["p_batt_charge"][ess].value[i]
        #         p_dch = self.cvx_variables["p_batt_discharge"][ess].value[i]
        #         q_chg = self.cvx_variables["q_batt_charge"][ess].value[i]
        #         q_dch = self.cvx_variables["q_batt_discharge"][ess].value[i]
        #         print(f"  ESS {ess}: P_chg = {p_chg:.2f} kW, P_dch = {p_dch:.2f} kW, Q_chg = {q_chg:.2f} kVAr, Q_dch = {q_dch:.2f} kVAr")

        #     q_grid = self.cvx_variables["q_grid"].value[i]
        #     print(f"  Grid Q: {q_grid:.2f} kVAr")

                

        # # 3) Check for infeasibility right away
        # # Add this after the solve attempt to get more detailed infeasibility info
        # if self.problem.status == "infeasible":
        #     print("Infeasible constraints:")
        #     for c in self.constraints:
        #         if not c.is_dcp():
        #             print("Non-convex constraint:", c)
        #         elif not c.is_dpp():
        #             print("Non-DPP constraint:", c)


        
        # # Inside the step method (test_el_mpc.py):
        # if self.problem.status in ["optimal", "optimal_inaccurate"]:
        #     print("\n--- Debug: Power Injections and Flows ---")
        #     t = 0  # First time step
        #     for node in self.nodes:
        #         p_bus_var = self.cvx_variables['p_bus'][node][t]
        #         p_bus_val = p_bus_var.value if p_bus_var is not None else None
        #         if p_bus_val is not None:
        #             print(f"p_bus[{node}][{t}] = {p_bus_val:.2f} kW")
        #         else:
        #             print(f"p_bus[{node}][{t}] is None (Check constraints!)")

        #         return result

        # # Inside step() or wherever you solve the MPC
        # if self.problem.status in ["optimal", "optimal_inaccurate"]:
        #     for t in range(min(5, self.n_hor)):
        #         grid_val = self.cvx_variables['p_grid'][t].value
        #         bus_sum = sum(self.cvx_variables['p_bus'][node][t].value for node in self.nodes if node != "PCC")
        #         print(f"[t={t}] Grid power (PCC): {grid_val:.3f} W, Sum of other p_bus: {bus_sum:.3f} W")
        # else:
        #     print("⚠️ Optimization did not succeed. Status:", self.problem.status)




    def post_process(self):
        gamma_grid_rounded = np.round(self.cvx_variables["gamma_grid"].value).astype(int)
    #    # first make sure the solver actually found a solution
    #     status = self.problem.status
    #     if status not in ["optimal", "optimal_inaccurate"]:
    #         raise RuntimeError(f"Cannot post_process(): problem status is {status!r}")

    #     # next, pull out the raw value and guard against None
    #     gamma_val = self.cvx_variables["gamma_grid"].value
    #     if gamma_val is None:
    #         raise RuntimeError("post_process(): 'gamma_grid' has no .value; solver returned no solution.")

    #     # now it’s safe to round
    #     gamma_grid_rounded = np.round(gamma_val).astype(int)

        #gamma_grid_rounded = np.round(gamma_val).astype(int)
        p_grid_draw_final = self.cvx_variables["p_grid_draw"].value * (1 - gamma_grid_rounded)
        p_grid_feedin_final = self.cvx_variables["p_grid_feedin"].value * gamma_grid_rounded


        return p_grid_draw_final, p_grid_feedin_final
    



    def save_results_to_csv(self, start_datetime_str="2023-01-01 00:00", interval_min=15):
        # Create time index as formatted strings
        start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
        time_index = [start_dt + timedelta(minutes=interval_min * i) for i in range(self.n_hor)]
        time_str_index = [dt.strftime("%d.%m.%Y %H:%M") for dt in time_index]

        base_path = "C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\1_mpc_results\\"

        # --- Active power (p_RES_net) ---
        res_p_net = {res: self.cvx_variables["p_RES_net"][res].value for res in self.res_nodes}
        df_res_p = pd.DataFrame(res_p_net, index=time_str_index)
        df_res_p.index.name = "time-step"
        df_res_p.to_csv(base_path + "res_net_active.csv", sep=',')

        # --- Reactive power (q_RES_net) ---
        res_q_net = {res: self.cvx_variables["q_RES_net"][res].value for res in self.res_nodes}
        df_res_q = pd.DataFrame(res_q_net, index=time_str_index)
        df_res_q.index.name = "time-step"
        df_res_q.to_csv(base_path + "res_net_reactive.csv", sep=',')

        # --- Battery active charge power (p_batt_charge) ---
        batt_p_charge = {ess: self.cvx_variables["p_batt_charge"][ess].value for ess in self.ess_nodes}
        df_batt_p_charge = pd.DataFrame(batt_p_charge, index=time_str_index)
        df_batt_p_charge.index.name = "time-step"
        df_batt_p_charge.to_csv(base_path + "batt_charge_active.csv", sep=',')

        # --- Battery reactive discharge power (q_batt_discharge) ---
        batt_q_discharge = {ess: self.cvx_variables["q_batt_discharge"][ess].value for ess in self.ess_nodes}
        df_batt_q_discharge = pd.DataFrame(batt_q_discharge, index=time_str_index)
        df_batt_q_discharge.index.name = "time-step"
        df_batt_q_discharge.to_csv(base_path + "batt_discharge_reactive.csv", sep=',')

        # --- Battery active discharge power (p_batt_discharge) ---
        batt_p_discharge = {ess: self.cvx_variables["p_batt_discharge"][ess].value for ess in self.ess_nodes}
        df_batt_p_discharge = pd.DataFrame(batt_p_discharge, index=time_str_index)
        df_batt_p_discharge.index.name = "time-step"
        df_batt_p_discharge.to_csv(base_path + "batt_discharge_active.csv", sep=',')

        # --- Battery reactive charge power (q_batt_charge) ---
        batt_q_charge = {ess: self.cvx_variables["q_batt_charge"][ess].value for ess in self.ess_nodes}
        df_batt_q_charge = pd.DataFrame(batt_q_charge, index=time_str_index)
        df_batt_q_charge.index.name = "time-step"
        df_batt_q_charge.to_csv(base_path + "batt_charge_reactive.csv", sep=',')

        # --- Line active power flows (p_line) ---
        p_line_values = self.cvx_variables["p_line"].value  # shape: (num_edges, n_hor)
        line_names = [f"{edge[0]}-{edge[1]}" for edge in self.edges]
        df_p_line = pd.DataFrame(p_line_values.T, columns=line_names, index=time_str_index)
        df_p_line.index.name = "time-step"
        df_p_line.to_csv(base_path + "line_active_power.csv", sep=',')

        # --- Line reactive power flows (q_line) ---
        q_line_values = self.cvx_variables["q_line"].value
        df_q_line = pd.DataFrame(q_line_values.T, columns=line_names, index=time_str_index)
        df_q_line.index.name = "time-step"
        df_q_line.to_csv(base_path + "line_reactive_power.csv", sep=',')

       

            # delta_V is stored as a dict with integer keys for node indices
        d_V = {
            self.nodes[node_idx]: self.cvx_variables["delta_V"][node_idx].value
            for node_idx in range(len(self.nodes))
            if node_idx in self.cvx_variables["delta_V"]
        }
        df_d_V = pd.DataFrame(d_V, index=time_str_index)
        df_d_V.index.name = "time-step"
        df_d_V.to_csv(base_path + "delta_V.csv", sep=',')

        

        print("Saved all active/reactive powers and line flows to separate CSV files.")





    def plot_results(self, p_grid_draw_final, p_grid_feedin_final):

        factor = 1000
        # ---------------------------------------------
        # Figure 1: Battery SOC, charge, discharge
        # ---------------------------------------------
        fig1, axs1 = plt.subplots(3, 1, figsize=(12, 10), constrained_layout=True)
        fig1.suptitle("Battery Performance", fontsize=14)

        for ess in self.ess_nodes:
            axs1[0].plot(self.cvx_variables["SOC_batt"][ess].value, label=f"SOC {ess}")
        axs1[0].set_title("State of Charge (SOC)")
        axs1[0].set_ylabel("SOC")
        axs1[0].legend(fontsize=12)
        axs1[0].grid(True)

        for ess in self.ess_nodes:
            axs1[1].plot(self.cvx_variables["p_batt_charge"][ess].value*factor, label=f"Charge {ess}")
        axs1[1].set_title("Charging Power")
        axs1[1].set_ylabel("Power (kW)")
        axs1[1].legend(fontsize=12)
        axs1[1].grid(True)

        for ess in self.ess_nodes:
            axs1[2].plot(self.cvx_variables["p_batt_discharge"][ess].value*factor, label=f"Discharge {ess}")
        axs1[2].set_title("Discharging Power")
        axs1[2].set_ylabel("Power (kW)")
        axs1[2].legend(fontsize=12)
        axs1[2].grid(True)

        # ---------------------------------------------
        # Figure 2: RES Net Generation
        # ---------------------------------------------
        fig_res, axs_res = plt.subplots(3, 1, figsize=(12, 10), constrained_layout=True)
        fig_res.suptitle("Renewable Energy (PV)", fontsize=14)

        for res in self.res_nodes:
            axs_res[0].plot(self.cvx_variables["p_RES_net"][res].value*factor, label=f"Net Output {res}")
        axs_res[0].set_title("Net Renewable Output")
        axs_res[0].set_ylabel("Power (kW)")
        axs_res[0].legend(fontsize=12)
        axs_res[0].grid(True)

        for res in self.res_nodes:
            axs_res[1].plot(self.cvx_parameters["p_RES"][res].value*factor, label=f"PV {res}")
        axs_res[1].set_title("PV Generation")
        axs_res[1].set_ylabel("Power (kW)")
        axs_res[1].legend(fontsize=12)
        axs_res[1].grid(True)

        for res in self.res_nodes:
            axs_res[2].plot(self.cvx_variables["p_curtailment"][res].value*factor, label=f"Curtailment {res}")
        axs_res[2].set_title("Curtailment")
        axs_res[2].set_ylabel("Power (kW)")
        axs_res[2].legend(fontsize=12)
        axs_res[2].grid(True)

        # -------------------------------------------------
        # Figure 3: Aggregated Demand, RES, Battery, Grid
        # -------------------------------------------------
        fig2, axs2 = plt.subplots(4, 1, figsize=(12, 14), constrained_layout=True)

        # Total Demand
        sum_demand = np.sum(
            [self.cvx_parameters["p_demand"][ld].value for ld in self.load_nodes], axis=0
        )
        axs2[0].plot(sum_demand*factor, label="Total Demand", color="black")
        axs2[0].set_title("Total Load Demand")
        axs2[0].set_ylabel("Power (kW)")
        axs2[0].legend(fontsize=12)
        axs2[0].grid(True)

        # Total RES
        sum_res = np.sum(
            [self.cvx_variables["p_RES_net"][rs].value for rs in self.res_nodes], axis=0
        )
        axs2[1].plot(sum_res*factor, label="Total RES Generation", color="green")
        axs2[1].set_title("Total Renewable Energy Generation")
        axs2[1].set_ylabel("Power (kW)")
        axs2[1].legend(fontsize=12)
        axs2[1].grid(True)

        # Battery
        sum_charge = np.sum(
            [self.cvx_variables["p_batt_charge"][be].value for be in self.ess_nodes], axis=0
        )
        sum_discharge = np.sum(
            [self.cvx_variables["p_batt_discharge"][be].value for be in self.ess_nodes], axis=0
        )
        axs2[2].plot(sum_charge*factor, label="Total Battery Charge", color="blue")
        axs2[2].plot(sum_discharge*factor, label="Total Battery Discharge", color="red")
        axs2[2].set_title("Total Battery Power")
        axs2[2].set_ylabel("Power (kW)")
        axs2[2].legend(fontsize=12)
        axs2[2].grid(True)

        # Grid
        axs2[3].plot(p_grid_draw_final*factor, label="Grid Draw", color="orange")
        axs2[3].plot(p_grid_feedin_final*factor, label="Grid Feed-In", color="purple")
        axs2[3].set_title("Grid Interaction")
        axs2[3].set_ylabel("Power (kW)")
        axs2[3].legend(fontsize=12)
        axs2[3].grid(True)

        # ---------------------------------------------
        # Figure 4: Line Flows (P and Q)
        # ---------------------------------------------
        # skip if AC‐OPF was disabled (so p_line never got created)
        if "p_line" not in self.cvx_variables:
            print("  [Skipping line-flow plots (AC-OPF disabled)]")
            return
        
        if "p_line" not in self.cvx_variables:
            print("  [Skipping line-flow plots (AC-OPF disabled)]")
            return

        # otherwise safe to build and plot p_line/q_line
        num_edges = len(self.edges)
        p_vals = np.vstack([self.cvx_variables["p_line"][e].value for e in range(num_edges)])
        q_vals = np.vstack([self.cvx_variables["q_line"][e].value for e in range(num_edges)])

        fig3, axs3 = plt.subplots(2, 1, figsize=(12, 12), constrained_layout=True)
        fig3.suptitle("Line Power Flows", fontsize=14)

        for e in range(num_edges):
            axs3[0].plot(p_vals[e, :]*factor, label=f"P Line {e}")
        axs3[0].set_title("Active Power Flow (P)")
        axs3[0].set_ylabel("Power (kW)")
        axs3[0].grid(True)
        axs3[0].legend(fontsize=8, ncol=4)

        for e in range(num_edges):
            axs3[1].plot(q_vals[e, :]*factor, label=f"Q Line {e}")
        axs3[1].set_title("Reactive Power Flow (Q)")
        axs3[1].set_ylabel("Power (kVar)")
        axs3[1].grid(True)
        axs3[1].legend(fontsize=8, ncol=4)


      
        # ---------------------------------------------
        # Figure 5: Voltage Profile (1 + ΔV) (p.u.)
        # ---------------------------------------------
        fig5, ax5 = plt.subplots(figsize=(12, 4), constrained_layout=True)
        fig5.suptitle("Voltage Profile (p.u.)", fontsize=14)

        # delta_V is keyed by integer node indices 0..N-1
        for idx, dv in self.cvx_variables["delta_V"].items():
            ax5.plot(1 + dv.value, label=self.nodes[idx])

        ax5.set_title("Voltage at each node (p.u.)")
        ax5.set_xlabel("Time step")
        ax5.set_ylabel("Voltage")
        ax5.legend(fontsize=10, ncol=2)
        ax5.grid(True)


        # ---------------------------------------------
        # Figure 6: Reactive Power Summary
        # ---------------------------------------------
        fig6, ax6 = plt.subplots(figsize=(12, 6), constrained_layout=True)
        fig6.suptitle("Reactive Power Contributions", fontsize=14)

        # Battery Q (net)
        for ess in self.ess_nodes:
            q_dis = self.cvx_variables["q_batt_discharge"][ess].value
            q_chg = self.cvx_variables["q_batt_charge"][ess].value
            q_net = q_dis - q_chg
            ax6.plot(q_net*factor, label=f"ESS {ess} (Q net)", linestyle='-')

        # RES Q
        for res in self.res_nodes:
            q_res = self.cvx_variables["q_RES_net"][res].value
            ax6.plot(q_res*factor, label=f"RES {res}", linestyle='--')

        # Grid Q
        q_grid = self.cvx_variables["q_grid"].value
        ax6.plot(q_grid*factor, label="Grid Q", linestyle=':')

        ax6.axhline(0, color='black', linewidth=0.8)
        ax6.set_xlabel("Time Step")
        ax6.set_ylabel("Reactive Power (kVAr)")
        ax6.legend(fontsize=10)
        ax6.grid(True)


        plt.show()



def test_electrical_side_of_mpc():
    demand_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\grid_sim\\results\\aggregated_bus_time_series.csv'
    #res_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\mpc_el_data_pv_only_cleaned.csv'
    res_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\combined_pv_outputs.csv'
    market_data_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\market_analysis_15min_converted.csv'
    line_lim_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\grid_sim\\data\\line_limits_acpf.csv'

    # Define the time for the simulation
    #time_intervals = 288                    # 24 hours
    time_intervals = 96                    # 24 hours
    #time_intervals = 5                    # 24 hours


 
    # Extract demand data 
    df_demand = pd.read_csv(demand_path)

    # #subset_df = df_demand.iloc[:, :len(UG_load_nodes)] # take the values stored up until the n-th load_node
    # subset_df = df_demand.iloc[:, 1:3] # take the values stored up until the n-th load_node
    # #print(subset_df.head())
    # p_demand_data = subset_df * 1000   # Convert MW to kW

    subset_df = df_demand.iloc[:, 1:3] *10
    #subset_df = df_demand.iloc[:, :len(UG_load_nodes)] # take the values stored up until the n-th load_node
    #p_demand_data = (subset_df * 1000).values[:time_intervals, :]
    p_demand_data = (subset_df).values[:time_intervals, :]


    

    ########################################### MARKET PRICE ASSIGNMENT ###################################################
    # Extract market price data
    df_market = pd.read_csv(market_data_path)
    # Adjust dimesnions of market data
    market_prices = df_market['Intraday_Auktion [Euro/MWh]'].values
    index_range = np.arange(0, len(market_prices) * 15, 5)
    draw_prices = np.interp(index_range, np.arange(0, len(market_prices) * 15, 15), market_prices)[:time_intervals] #/ 1000000 # Euro/kWh
    feedin_prices = -draw_prices

    df_prices = pd.DataFrame({
    'cost_feedin': feedin_prices,
    'cost_draw': draw_prices
    })

    cost_feedin = df_prices['cost_feedin'].values[:time_intervals]
    cost_draw = df_prices['cost_draw'].values[:time_intervals]


    ######################################### ADJUST RES DATA HERE!#######################################################
    res_df = pd.read_csv(res_path)
    p_res_data = res_df.iloc[:, 1:3]/3000


    # res_data = pd.read_csv(res_path)
    # p_res_data1 = res_data['pv_power'].values[:time_intervals] /1000  # W --> kW
    # p_res_data2 = res_data['pv_power'].values[:time_intervals] /1000
    # p_res_data3 = res_data['pv_power'].values[:time_intervals] /1000


    # p_res_data = np.column_stack((p_res_data1, p_res_data2, p_res_data3))

    


    controller = CentralController()

    ################################# SET LINE LIMITS: one value for each edge ##########################################
    #line_limits = np.full(len(controller.edges), 1e7) #this case all line values get 10000
    line_lim_df = pd.read_csv(line_lim_path)
    line_limits = line_lim_df.iloc[:, 1]

    


    ################################### STEP CONFIG FOR MULTIPLE NODES! ###############################################
    step_config = {

    #"p_RES": {res: p_res_data[:, i] for i, res in enumerate(controller.res_nodes)},
    "p_RES": {res: p_res_data.iloc[:, i].values for i, res in enumerate(controller.res_nodes)},
    "p_demand": {load: p_demand_data[:, idx]           for idx, load in enumerate(controller.load_nodes)},

    "SOC_initial": {ess: 0.7 for ess in controller.ess_nodes},

    # Cost parameters provided as full time series arrays.
    "cost_feedin": cost_feedin,  # This array will be sliced inside step() if necessary.
    "cost_draw": cost_draw,       # Same here

    # Assignemt of line limits parameters
    "line_limits": line_limits,
    }
    

    
    # # ——— Debug: check all your arrays are in kW ———
    # print("Demand  [kW]:", p_demand_data.min(), "…", p_demand_data.max())
    # print("PV gen  [kW]:", p_res_data.min(),    "…", p_res_data.max())
    # print("Line lim[kW]:", line_limits)
    # # ————————————————————————————————

    # try:
    #     controller.step(step_config)
    # except RuntimeError as e:
    #     print("Aborting simulation:", e)
    #     return

    controller.step(step_config)


    # print("RES1 PV sample:", p_res_data.iloc[:10, 0].values)
    # print("RES2 PV sample:", p_res_data.iloc[:10, 1].values)
    


    # for node in controller.ess_nodes:
    #     soc_vals = [controller.cvx_variables["SOC_batt"][node][t].value for t in range(controller.n_hor + 1)]
    #     charge_vals = [controller.cvx_variables["p_batt_charge"][node][t].value for t in range(controller.n_hor)]
    #     discharge_vals = [controller.cvx_variables["p_batt_discharge"][node][t].value for t in range(controller.n_hor)]

    #     print(f"\n{node} SoC: {soc_vals}")
    #     print(f"{node} Charge: {charge_vals}")
    #     print(f"{node} Discharge: {discharge_vals}")


    # for t in range(min(5, controller.n_hor)):
    #     for res in controller.res_nodes:
    #         p_res = controller.cvx_parameters['p_RES'][res].value[t]
    #         p_curt = controller.cvx_variables['p_curtailment'][res][t].value
    #         p_net = controller.cvx_variables['p_RES_net'][res][t].value
    #         print(f"[t={t}] {res} | p_RES: {p_res:.2f} W | Curtail: {p_curt:.2f} W | Net: {p_net:.2f} W")

    
    # for t in range(min(5, controller.n_hor)):
    #     p_grid = controller.cvx_variables['p_grid'][t].value
    #     p_bus_sum = sum(controller.cvx_variables['p_bus'][node][t].value for node in controller.nodes if node != "PCC")
        
    #     res_sum = sum(controller.cvx_variables['p_RES_net'][res][t].value for res in controller.res_nodes)
    #     batt_draw = sum(controller.cvx_variables['p_batt_discharge'][ess][t].value for ess in controller.ess_nodes)
    #     batt_charge = sum(controller.cvx_variables['p_batt_charge'][ess][t].value for ess in controller.ess_nodes)
    #     load_sum = sum(controller.cvx_parameters['p_demand'][load][t] for load in controller.load_nodes)

    #     print(f"\n--- t={t} ---")
    #     print(f"Grid Power: {p_grid:.3f} W")
    #     print(f"Sum p_bus (non-PCC): {p_bus_sum:.3f} W")
    #     print(f"Total RES: {res_sum:.3f} W")
    #     print(f"Total Batt Discharge: {batt_draw:.3f} W")
    #     print(f"Total Batt Charge: {batt_charge:.3f} W")
    #     print(f"Total Load: {load_sum.value:.3f} W")

    
    # # #############################################################
    # # DEBUG: Print line flows for all edges and time steps
    # # #############################################################
    # print("\n--- Debug: Line Flows ---")
    # num_edges = len(controller.edges)
    # H = controller.n_hor
    # for e in range(num_edges):
    #     u, v, *_ = controller.edges[e]
    #     p_line_vals = controller.cvx_variables['p_line'][e].value
    #     print(f"Line {u}→{v}:")
    #     print("  Flow (kW):", p_line_vals[:5])  # First 5 time steps
    # # #############################################################

    # # #############################################################
    # # DEBUG: Print voltage deviations (delta_V)
    # # #############################################################
    # print("\n--- Debug: Voltage Deviations ---")
    # for idx, dv in controller.cvx_variables["delta_V"].items():
    #     node_name = controller.nodes[idx]
    #     print(f"Voltage at {node_name}:")
    #     print("  ΔV (p.u.):", dv.value[:5])  # First 5 time steps
    # # #############################################################


    # Now safe to post_process and plot
    p_draw, p_feedin = controller.post_process()
    controller.save_results_to_csv()
    controller.plot_results(p_draw, p_feedin)
    # Now save results to CSV
    print("MPC run complete!")

if __name__ == "__main__":
    test_electrical_side_of_mpc()