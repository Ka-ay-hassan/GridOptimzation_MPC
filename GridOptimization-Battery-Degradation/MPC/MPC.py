__author__ = "Abdul Azzam"
__copyright__ = "Copyright (C) 2024 Abdul Azzam"
__license__ = "GPL"
__version__ = "1.0"

import cvxpy as cvx
from cvxpy import exp, power
import numpy as np
#from grid2DCpf import T_nodes, T_edges


class MPC_Battery_PCC_RES:
    def __init__(self):
        """
        Initialization of the MPC Class for Battery, PCC, and RES
        """

        # Time horizon parameters
        self.dt_s = 300     # Stepsize in seconds
        #self.n_hor = 288   # Prediction horizon  ** 288 Steps? --> 288 * 300s = 24h? **
        self.n_hor = 576    # 2 days
        #self.n_hor = 2016
        #self.n_hor = 8640   #30 days

        # Battery parameters
        self.c_batt = 200000.0  # Battery capacity in Wh
        self.batt_cost = 0.01  # Battery cost in €/kWh
        self.eta_batt = 1.0  # Battery efficiency
        self.p_batt_max = 100000.0  # Maximum battery power in W
        self.soc_init = 0.5  # Initial state of charge

        
        self.calendar_cost = 0.001  # Cost per hour per unit of capacity
        


        # Grid parameters
        self.p_grid_max = 3300000.0  # Maximum grid power in W
        self.grid_cost_draw = 0.2  # Cost for drawing from grid €/kWh
        self.grid_cost_feedin = -0.05  # Feed-in tariff €/kWh

        # Renewable energy parameters
        self.p_res_max = 30000.0  # Maximum renewable energy power in W
        self.c_curtail = 0.0  # Curtailment cost €/kWh

        # CVXPY Variables and Parameters
        self.cvx_variables = {}
        self.cvx_parameters = {}
        self.constraints = []   #list to hold constraints of optimization
        self.cost = cvx.Constant(0)

      
  

    def init_res(self):
        H = self.n_hor

        self.cvx_variables['p_RES_net'] = cvx.Variable(H)  # Generation power of RES after demand profile and curtailment [W]
        self.cvx_variables['p_curtailment'] = cvx.Variable(H)  # Curtailment of renewables [W]
        self.cvx_parameters['p_RES'] = cvx.Parameter(H)  # RES prediction

            # Node-specific constraints
        self.constraints += [
            0 <= self.cvx_variables['p_curtailment'],
            0 <= self.cvx_parameters['p_RES'],
            self.cvx_variables['p_RES_net'] == self.cvx_parameters['p_RES'] - self.cvx_variables['p_curtailment'],
            self.cvx_variables['p_RES_net'] <= self.p_res_max,
            0 <= self.cvx_variables['p_RES_net']
            ]

        # Cost calculation for each node
        for j in range(H):
            self.cost += self.cvx_variables['p_curtailment'][j] * self.c_curtail * self.dt_s  # kW * eur/kWh * s

        ###--- linear approximation of one_cycle cost
    @staticmethod
    def degradation_cost_formula(SOC, C_cap, beta0, beta1, beta2):
        """Calculate the degradation cost based on the state of charge."""
        DOD = 1-SOC
        Ncycle = beta0 * power(DOD, -beta1) * exp(beta2 * (1 - DOD))
        CE = C_cap / Ncycle
        return CE

    def init_batt(self):
        """Initialize battery variables and constraints in a structured manner"""
        H = self.n_hor  # Number of hours, equivalent to the prediction horizon
        eta_chg = self.eta_batt  # Charging efficiency
        eta_dsg = self.eta_batt  # Discharging efficiency

        C_cap = 50000 #capital cost example
        beta0, beta1, beta2 = 4901, 1.98, 0.016  # B1 and B2
        beta0, beta1, beta2 = 3832, 0.68 , 1.64 #B3

        total_bat_cost = 0


        # Local states for storages
        self.cvx_parameters["SOC_initial"] = cvx.Constant(self.soc_init)
        self.cvx_variables["SOC_batt"] = cvx.Variable(H + 1)  # State of charge (SOC)
        self.cvx_variables["p_batt_charge"] = cvx.Variable(H)  # Charging power
        self.cvx_variables["p_batt_discharge"] = cvx.Variable(H)  # Discharging power
        self.cvx_variables["gamma"] = cvx.Variable(H, boolean=True)  # Binary variable for charge/discharge state

        # Initialize auxiliary SoC variable
        self.cvx_variables["SOC_aux"] = cvx.Variable(H + 1)


        # Power and SOC limits
        self.cvx_parameters["p_batt_max"] = cvx.Constant(self.p_batt_max) # Battery power in W
        self.cvx_parameters["C_batt"] = cvx.Constant(self.c_batt)  # Battery capacity in kWh

        # Initialize constraints list
        self.constraints += [
            self.cvx_variables["SOC_batt"][0] == self.cvx_parameters["SOC_initial"],
            self.cvx_variables["SOC_aux"][0] == self.cvx_parameters["SOC_initial"],
            self.cvx_variables["SOC_batt"][0] == self.cvx_variables["SOC_batt"][-1]  # Cyclic constraint
        ]

        # Add constraints for SOC, charging, discharging, and power limits
        for i in range(H):
            self.constraints += [
                0 <= self.cvx_variables['gamma'][i],
                self.cvx_variables['gamma'][i] <= 1,
                0.2 <= self.cvx_variables["SOC_batt"][i],
                self.cvx_variables["SOC_batt"][i] <= 0.8,
                0 * self.cvx_variables["gamma"][i] <= self.cvx_variables["p_batt_charge"][i],
                self.cvx_variables["p_batt_charge"][i] <= self.cvx_parameters["p_batt_max"] *
                self.cvx_variables["gamma"][i],
                0 * (1 - self.cvx_variables["gamma"][i]) <= self.cvx_variables["p_batt_discharge"][i],
                self.cvx_variables["p_batt_discharge"][i] <= self.cvx_parameters["p_batt_max"] * (
                        1 - self.cvx_variables["gamma"][i]),
                self.cvx_variables["SOC_batt"][i + 1] == self.cvx_variables["SOC_batt"][i] +
                (eta_chg * self.cvx_variables["p_batt_charge"][i] - self.cvx_variables["p_batt_discharge"][
                    i] / eta_dsg) * self.dt_s / (3600 * self.cvx_parameters['C_batt']),

                #self.cvx_variables["SOC_batt"][H-1] == self.cvx_variables["SOC_batt"][0],

                self.cvx_variables["SOC_aux"][i + 1] == self.cvx_variables["SOC_batt"][i] - (
                self.dt_s / (3600 * self.cvx_parameters["C_batt"]) * (
                self.cvx_variables["p_batt_discharge"][i] / eta_dsg)),

            ]
            
            if (i + 1) % 288 == 0:
                self.constraints += [
                    self.cvx_variables["SOC_batt"][i + 1] == self.cvx_parameters["SOC_initial"],
                ]

            if i > 0:
                degradation_cost = (
                    MPC_Battery_PCC_RES.degradation_cost_formula(self.cvx_variables["SOC_aux"][i], C_cap, beta0, beta1, beta2)
                    - MPC_Battery_PCC_RES.degradation_cost_formula(self.cvx_variables["SOC_batt"][i - 1], C_cap, beta0, beta1, beta2)
                )
                total_bat_cost += degradation_cost + self.calendar_cost

        self.cost += total_bat_cost
        self.total_bat_cost_expr = total_bat_cost  # Save symbolic expression for later access

        #     total_bat_cost += (
        #     self.cvx_variables["p_batt_charge"][i] * self.batt_cost * self.dt_s -
        #     self.cvx_variables["p_batt_discharge"][i] * self.batt_cost * self.dt_s +
        #     self.cvx_variables["gamma"][i] * self.batt_cost +
        #     self.calendar_cost * self.dt_s
        # )
            
        # self.cost += total_bat_cost
        # self.total_bat_cost_expr = total_bat_cost  # Save symbolic expression for later access
            
        
    



            # self.power_hub_electric = [self.cvx_variables["p_batt_charge"] - self.cvx_variables["p_batt_discharge"]]

    def init_pcc(self):
        """Initialize the Point of Common Coupling (PPC)"""
        self.cvx_variables["p_grid_draw"] = cvx.Variable(self.n_hor)
        self.cvx_variables["p_grid_feedin"] = cvx.Variable(self.n_hor)
        self.cvx_variables["p_grid"] = cvx.Variable(self.n_hor)  # Grid power [W]

        # Grid parameters
        self.cvx_parameters["p_grid_max"] = cvx.Constant(self.p_grid_max)
        self.cvx_parameters["cost_feedin"] = cvx.Parameter(self.n_hor)
        self.cvx_parameters["cost_draw"] = cvx.Parameter(self.n_hor)
        self.cvx_variables["gamma_grid"] = cvx.Variable(self.n_hor)  # Binary variable for grid state

        self.cost = 0  # Initialize cost

        for j in range(self.n_hor):
            self.constraints += [
                0 <= self.cvx_variables['gamma_grid'][j],
                self.cvx_variables['gamma_grid'][j] <= 1,
                self.cvx_variables["p_grid"][j] == self.cvx_parameters['p_demand'][j] - self.cvx_variables["p_RES_net"][j]
                  + self.cvx_variables["p_batt_charge"][j] - self.cvx_variables["p_batt_discharge"][j],
                self.cvx_variables["p_grid"][j] == self.cvx_variables["p_grid_draw"][j] -
                self.cvx_variables["p_grid_feedin"][j],
                -self.cvx_parameters["p_grid_max"] <= self.cvx_variables["p_grid"][j],
                self.cvx_variables["p_grid"][j] <= self.cvx_parameters["p_grid_max"],
                self.cvx_variables["p_grid_feedin"][j] >= 0,
                self.cvx_variables["p_grid_draw"][j] >= 0,

                # Constraints to avoid simultaneous draw and feed-in

                0 * self.cvx_variables["gamma_grid"][j] <= self.cvx_variables["p_grid_feedin"][j],
                self.cvx_variables["p_grid_feedin"][j] <= self.cvx_parameters["p_grid_max"] *
                self.cvx_variables["gamma_grid"][j],
                0 * (1 - self.cvx_variables["gamma_grid"][j]) <= self.cvx_variables["p_grid_draw"][j],
                self.cvx_variables["p_grid_draw"][j] <= self.cvx_parameters["p_grid_max"] * (
                        1 - self.cvx_variables["gamma_grid"][j])
            ]
            self.cost += (
                                 self.cvx_variables["p_grid_draw"][j] * self.cvx_parameters["cost_draw"][j] -
                                 self.cvx_variables["p_grid_feedin"][j] * self.cvx_parameters["cost_feedin"][j]
                         ) * self.dt_s

    def init_demand(self):
        self.cvx_parameters["p_demand"] = cvx.Parameter(self.n_hor)


    def init_pcc_dcpf(self) -> None:
        """Initializes the Point of Common Coupling (PCC) with DC power flow constraints.

        This method replaces the original init_pcc method by incorporating DC power flow
        constraints to model grid physics. It defines variables for grid power exchange,
        line flows, and enforces constraints for line thermal limits and grid connectivity.

        Attributes:
            cvx_variables: Adds optimization variables for grid draw/feed-in, line flows.
            cvx_parameters: Adds parameters for DC power flow matrix and line limits.
        """

        self.cvx_variables['p_grid_draw'] = {}
        self.cvx_variables['p_grid_feedin'] = {}
        self.cvx_variables['p_grid'] = {}
        self.cvx_variables['gamma_grid'] = {}

         # --------------------------
        # 2. DC Power Flow variables
        # --------------------------
        num_edges = len(self.edges)
        self.cvx_variables['pe_e'] = cvx.Variable(
            (num_edges, self.n_hor),
            name='line_flows'  # Line flows [MW]
        )

        # --------------------------
        # 1. Define PCC variables
        # --------------------------
        self.cvx_variables['p_grid_draw'] = cvx.Variable(self.n_hor)
        self.cvx_variables['p_grid_feedin'] = cvx.Variable(self.n_hor)
        self.cvx_variables['p_grid'] = cvx.Variable(self.n_hor)  # Grid power [W]
        self.cvx_variables['gamma_grid'] = cvx.Variable(self.n_hor, boolean=True, name='grid_state_binary')


        # --------------------------
        # 3. Grid parameters
        # --------------------------
        self.cvx_parameters['p_grid_max'] = cvx.Constant(self.p_grid_max)
        self.cvx_variables['gamma_grid'] = cvx.Variable(self.n_hor,boolean=True,name='grid_state_binary')

            # --------------------------
            # 4. DC Power Flow parameters
            # --------------------------
        self.cvx_parameters['F_tilde_e'] = cvx.Parameter(
            (num_edges, len(self.nodes)),
            value=self.F_tilde_e,name='F_tilde_matrix')
        
        self.cvx_parameters['line_limits'] = cvx.Parameter(
            num_edges,
            name='line_thermal_limits'  # [MW]
            )

        self.cost = 0  # Initialize cost

        for j in range(self.n_hor):
            # ======================================================================
            # I. Nodal Power Vector (pe_n)
            # ======================================================================
            # Ensure the shapes are compatible for broadcasting
            pe_n = cvx.vstack([
            self.cvx_variables['p_grid'][j] - self.cvx_variables['p_RES_net'][j] + 
            self.cvx_variables['p_batt_charge'][j] - self.cvx_variables['p_batt_discharge'][j]
            ])

            # Flatten pe_n if necessary or adjust pe_e[:, j]
            self.constraints.extend([
                self.cvx_variables['pe_e'][:, j].reshape((-1, 1)) == self.cvx_parameters['F_tilde_e'] @ pe_n,
                cvx.abs(self.cvx_variables['pe_e'][:, j])
                <= self.cvx_parameters['line_limits'],])

            # ======================================================================
            # III. Grid Connectivity Constraints
            # ======================================================================
            self.constraints.extend([
                # Power balance equation
                self.cvx_variables['p_grid'][j] == (
                        self.cvx_parameters['p_demand'][j]
                        - self.cvx_variables['p_RES_net'][j]
                        + self.cvx_variables['p_batt_charge'][j]
                        - self.cvx_variables['p_batt_discharge'][j]),

                # Grid draw/feed-in decomposition
                self.cvx_variables['p_grid'][j] == (
                            self.cvx_variables['p_grid_draw'][j]
                            - self.cvx_variables['p_grid_feedin'][j]
                    ),
                # Grid connection limits
                -self.cvx_parameters['p_grid_max'] <= self.cvx_variables['p_grid'][j],
                self.cvx_variables['p_grid'][j] <= self.cvx_parameters['p_grid_max'],
                # Non-negativity constraints
                self.cvx_variables['p_grid_feedin'][j] >= 0,

                self.cvx_variables['p_grid_draw'][j] >= 0,

                0 * self.cvx_variables['gamma_grid'][j]
                <= self.cvx_variables['p_grid_feedin'][j],

                self.cvx_variables['p_grid_feedin'][j]
                <= self.cvx_parameters['p_grid_max'] * self.cvx_variables['gamma_grid'][j],

                0 * (1 - self.cvx_variables['gamma_grid'][j])
                <= self.cvx_variables['p_grid_draw'][j],

                self.cvx_variables['p_grid_draw'][j]
                <= self.cvx_parameters['p_grid_max'] * (1 - self.cvx_variables['gamma_grid'][j])
            ])

                # ======================================================================
                # IV. Cost Calculation
                # ======================================================================
            self.cost += (
                self.cvx_variables['p_grid_draw'][j] * self.cvx_parameters['cost_draw'][j] -
                self.cvx_variables['p_grid_feedin'][j] * self.cvx_parameters['cost_feedin'][j]
            ) * self.dt_s / 3600