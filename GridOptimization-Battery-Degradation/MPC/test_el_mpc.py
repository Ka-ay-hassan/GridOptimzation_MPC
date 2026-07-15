import os
import numpy as np
import pandas as pd
import cvxpy as cvx
import matplotlib.pyplot as plt
#from MPC.MPC import MPC_Battery_PCC_RES
from MPC import MPC_Battery_PCC_RES         #Verwendung nur für Kareem (andere Directory)

class CentralController(MPC_Battery_PCC_RES):
    def __init__(self):
        super().__init__()
        self.print_parameters()
        self.init_batt()
        self.init_res()
        self.init_demand()
        self.init_pcc()
        self.problem = cvx.Problem(cvx.Minimize(self.cost), self.constraints)

    def print_parameters(self):
        print("Battery Parameters:")
        print(f"  Battery capacity (c_batt): {self.c_batt} MWh")
        print(f"  Battery cost (batt_cost): {self.batt_cost} €/MWh")
        print(f"  Battery efficiency (eta_batt): {self.eta_batt}")
        print(f"  Maximum battery power (p_batt_max): {self.p_batt_max} MW")
        print(f"  Initial state of charge (soc_init): {self.soc_init}\n")

        print("PV Parameters:")
        print(f"  Maximum net generation of PV (p_res_max): {self.p_res_max} kW")
        print(f"  Curtailment cost (c_curtail): {self.c_curtail} €/kWh\n")

        print("Grid Parameters:")
        print(f"  Maximum grid power (p_grid_max): {self.p_grid_max} kW\n")

    def step(self, step_config):
        self.cvx_parameters["p_RES"].project_and_assign(step_config["p_RES"][:self.n_hor])
        self.cvx_parameters["p_demand"].project_and_assign(step_config["p_demand"][:self.n_hor])
        self.cvx_parameters["cost_feedin"].project_and_assign(step_config["cost_feedin"][:self.n_hor])
        self.cvx_parameters["cost_draw"].project_and_assign(step_config["cost_draw"][:self.n_hor])
        self.problem.solve(solver=cvx.SCIP, verbose=True)
        # Print total battery degradation cost after solving
        print(f"Total battery degradation cost (optimized): {self.total_bat_cost_expr.value}")

    def post_process(self):
        gamma_grid_rounded = np.round(self.cvx_variables["gamma_grid"].value).astype(int)
        p_grid_draw_final = self.cvx_variables["p_grid_draw"].value * (1 - gamma_grid_rounded)
        p_grid_feedin_final = self.cvx_variables["p_grid_feedin"].value * gamma_grid_rounded
        return p_grid_draw_final, p_grid_feedin_final

    def plot_results(self, p_grid_draw_final, p_grid_feedin_final):
        fig, axs = plt.subplots(7, 1, figsize=(12, 28))
        axs[0].plot(self.cvx_variables["SOC_batt"].value, label='SOC_batt')
        axs[0].set_ylabel('SOC (%)')
        axs[0].legend()
        axs[0].grid(True)

        axs[1].plot(self.cvx_variables["p_batt_charge"].value, label='p_batt_charge')
        axs[1].plot(self.cvx_variables["p_batt_discharge"].value, label='p_batt_discharge')
        axs[1].set_ylabel('Battery Power (kW)')
        axs[1].set_xlabel('Time step')
        axs[1].legend()
        axs[1].grid(True)

        axs[2].plot(p_grid_draw_final, label='p_grid_draw (Final)')
        axs[2].plot(p_grid_feedin_final, label='p_grid_feedin (Final)')
        axs[2].set_ylabel('Grid Power (kW)')
        axs[2].set_xlabel('Time step')
        axs[2].legend()
        axs[2].grid(True)

        axs[3].plot(self.cvx_parameters["p_RES"].value, label='PV generation')
        axs[3].plot(self.cvx_variables["p_curtailment"].value, 'r--', label='Curtailment')
        axs[3].plot(self.cvx_variables["p_RES_net"].value, label='p_RES_net')
        axs[3].set_ylabel('Power (kW)')
        axs[3].set_xlabel('Time step')
        axs[3].legend()
        axs[3].grid(True)

        axs[4].plot(self.cvx_parameters["p_demand"].value, label='Demand')
        axs[4].set_ylabel('Demand (kW)')
        axs[4].set_xlabel('Time step')
        axs[4].legend()
        axs[4].grid(True)

        axs[5].plot(self.cvx_parameters["cost_feedin"].value, label='Feed-in Price')
        axs[5].plot(self.cvx_parameters["cost_draw"].value, label='Draw Price')
        axs[5].set_ylabel('Price (€/kWh)')
        axs[5].set_xlabel('Time step')
        axs[5].legend()
        axs[5].grid(True)

        electrical_balance = (
            self.cvx_parameters["p_RES"].value +
            p_grid_draw_final -
            p_grid_feedin_final +
            self.cvx_variables["p_batt_discharge"].value -
            self.cvx_variables["p_batt_charge"].value -
            self.cvx_parameters["p_demand"].value
        )
        axs[6].plot(electrical_balance, label='Electrical Balance')
        axs[6].set_ylabel('Power (kW)')
        axs[6].set_xlabel('Time step')
        axs[6].legend()
        axs[6].grid(True)

        plt.tight_layout()
        plt.show()
        

def test_electrical_side_of_mpc():
    # Construct the full path to the CSV file in the parent directory
    csv_file_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\mpc_el_data.csv'
    market_data_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\market_analysis_15min_converted.csv'
    pv_file_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\mpc_el_data_pv_only_cleaned.csv'
 
    df_data = pd.read_csv(csv_file_path)
    pv_data = pd.read_csv(pv_file_path)

    df_market = pd.read_csv(market_data_path)

    #time_intervals = 288  # 24 hours * 60 minutes / 5 minutes
    time_intervals = 576

    feedin_prices = np.zeros(time_intervals)
    draw_prices = np.zeros(time_intervals)

    # Extract and interpolate market prices to 5-minute intervals
    market_prices = df_market['Intraday_Auktion [Euro/MWh]'].values
    index_range = np.arange(0, len(market_prices) * 15, 5)
    draw_prices = np.interp(index_range, np.arange(0, len(market_prices) * 15, 15), market_prices)
    draw_prices = draw_prices[:time_intervals] / 1000  # Convert MWh to kWh

    # Assuming feed-in prices are negatively correlated with draw prices
    feedin_prices = -draw_prices  

   

    # low_price = 0.005
    # high_price = 0.01

    # morning_peak_end = 96  # 8 AM (8 * 12)
    # evening_peak_start = 192  # 4 PM (16 * 12)
    # night_period_start = 240  # 8 PM (20 * 12)

    # for i in range(time_intervals):
    #     if i < morning_peak_end or i >= night_period_start:
    #         feedin_prices[i] = low_price
    #         draw_prices[i] = high_price
    #     elif morning_peak_end <= i < evening_peak_start:
    #         feedin_prices[i] = high_price
    #         draw_prices[i] = low_price
    #     else:
    #         feedin_prices[i] = high_price
    #         draw_prices[i] = low_price

    df_prices = pd.DataFrame({
        'cost_feedin': feedin_prices,
        'cost_draw': draw_prices
    })

    p_res_data = pv_data['pv_power'].values[:1000]
    p_demand_data = df_data['demand'].values[:1000]


    cost_feedin = df_prices['cost_feedin'].values[:time_intervals]
    cost_draw = df_prices['cost_draw'].values[:time_intervals]

    controller = CentralController()
    step_config = {
        "p_RES": p_res_data,
        "SOC_initial": 0.7,
        "p_demand": p_demand_data,
        "cost_feedin": cost_feedin,
        "cost_draw": cost_draw
    }
    controller.step(step_config)

    p_grid_draw_final, p_grid_feedin_final = controller.post_process()

    controller.plot_results(p_grid_draw_final, p_grid_feedin_final)

     # Prepare data dictionary for CSV
    data_dict = {
        "SOC_batt": controller.cvx_variables["SOC_batt"].value[:-1],  # length n_hor+1, trim last for alignment
        "p_batt_charge": controller.cvx_variables["p_batt_charge"].value,
        "p_batt_discharge": controller.cvx_variables["p_batt_discharge"].value,
        "p_RES": controller.cvx_parameters["p_RES"].value,
        "p_curtailment": controller.cvx_variables["p_curtailment"].value,
        "p_RES_net": controller.cvx_variables["p_RES_net"].value,
    }

    df_results = pd.DataFrame(data_dict)
    df_results.index.name = "time_step"

    # Save to CSV file (you can specify your own path)
    output_csv_path = "C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\batB3.csv"
    df_results.to_csv(output_csv_path)

    print(f"Saved battery and PV time series data to {output_csv_path}")

if __name__ == "__main__":
    test_electrical_side_of_mpc()