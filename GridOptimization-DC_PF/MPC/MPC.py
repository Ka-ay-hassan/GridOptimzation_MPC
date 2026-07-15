__author__ = "Abdul Azzam"
__copyright__ = "Copyright (C) 2024 Abdul Azzam"
__license__ = "GPL"
__version__ = "1.0"

import cvxpy as cvx
from cvxpy import exp, power
import numpy as np
from grid2DCpf import UG_edges, UG_nodes, UG_load_nodes, RES_nodes, ESS_nodes
#from RES_ESS_add import T_nodes, T_edges, res_nodes, ess_nodes, load_nodes


class MPC_Battery_PCC_RES:
    def __init__(self):
        """
        Initialization of the MPC Class for Battery, PCC, and RES
        """

        # Time horizon parameters
        self.dt_s = 300     # Stepsize in seconds
        self.n_hor = 288   # Prediction horizon : 288 Steps --> 288 * 300s = 24h
        #self.n_hor = 10
        

      

        # Battery parameters
        self.c_batt = 200000.0  # Battery capacity in Wh
        self.batt_cost = 0.01  # Battery cost in €/kWh
        self.eta_batt = 1.0  # Battery efficiency
        self.p_batt_max = 100000.0  # Maximum battery power in W combo 1

        #self.p_batt_max = 150000.0  # Maximum battery power in W (original) combo 1
        #self.p_batt_max = 200000.0  # Maximum battery power in W

        self.soc_init = 0.5  # Initial state of charge

        ### --------------- Kareem addition start --------------- ###
        
        self.calendar_cost = 0.001  # Cost per hour per unit of capacity
        
        ### --------------- Kareem addition end --------------- ###


        # Grid parameters
        self.p_grid_max =  3300000.0 # Maximum grid power in W
        # self.grid_cost_draw = 0.2  # Cost for drawing from grid €/kWh
        # self.grid_cost_feedin = -0.05  # Feed-in tariff €/kWh

        # Maximum Renewable energy parameters in [W]
        #self.p_res_max = 30000.0  # original value --> combo 1) working value
        #self.p_res_max = 60000.0  # combo 1) working value 
        #self.p_res_max =  70000.0  # combo 1) working value

        self.p_res_max =  75000.0  # Maximum renewable energy power in W --> combo 1) working value

        self.c_curtail = 0.0  # Curtailment cost €/kWh

        # CVXPY Variables and Parameters
        self.cvx_variables = {}
        self.cvx_parameters = {}
        self.constraints = []   #list to hold constraints of optimization
        self.cost = cvx.Constant(0)

        # ==========================
        # 0. Define Network Topology
        # ==========================

        # #Nodes in specified order: PCC, ESS, P2H, RES, Loads
        self.nodes = ["PCC", "Load1", "Load2", "RES1", "RES2", "ESS1", "ESS2"]

        # #Edges: (from_node, to_node, susceptance)
        # self.edges = [
        #     ("PCC", "Load1", 0.2),
        #     ("ESS1", "Load1", 0.1),
        #     ("RES1", "Load1", 0.15),
        #     ("ESS1", "RES1", 0.25),

        #     ("PCC", "Load2", 0.23),
        #     ("ESS2", "Load2", 0.12),
        #     ("RES2", "Load2", 0.15),
        #     ("ESS2", "RES2", 0.23),
        # ]

        # Define which nodes are battery, RES or load 
        # self.load_nodes = ["Load1", "Load2"]   # List of nodes that have Loads
        # self.res_nodes = ["RES1", "RES2"]      # List of nodes that have RES
        # self.ess_nodes = ["ESS1", "ESS2"]      # List of nodes that have batteries


        ###### UNCOMMENT for ---> Values of UniGrid ##################
        self.nodes = UG_nodes
        self.edges = UG_edges
        #RES & ESS nodes
        self.load_nodes = UG_load_nodes
        self.res_nodes = RES_nodes
        self.ess_nodes = ESS_nodes
        ###############################################################

        

        # Compute F_tilde_e matrix
        self.F_tilde_e = self._compute_F_tilde()

    def _compute_F_tilde(self):
        """Compute F_tilde_e matrix from grid topology."""
        # ==========================
        # 1. Construct Incidence Matrix
        # ==========================
        num_nodes = len(self.nodes)
        num_edges = len(self.edges)
        Fe = np.zeros((num_nodes, num_edges))
        for edge_idx, (from_node, to_node, _) in enumerate(self.edges):
            from_idx = self.nodes.index(from_node)
            to_idx = self.nodes.index(to_node)
            Fe[from_idx, edge_idx] = 1
            Fe[to_idx, edge_idx] = -1

        # ==========================
        # 2. Compute Edge Parameters (a)
        # ==========================
        a = np.array([b for _, _, b in self.edges]) * 1.0 * 1.0  # a_i = b_ml * v_m * v_l

        # ==========================
        # 3. Build Laplacian Matrix
        # ==========================
        diag_a = np.diag(a)
        L = Fe @ diag_a @ Fe.T

        # ==========================
        # 4. Transformation Matrices
        # ==========================
        n = num_nodes 
        T = np.vstack([
            np.hstack([np.eye(n-1), -np.ones((n-1, 1))]),  # Upper block
            np.hstack([np.zeros((1, n-1)), np.ones((1, 1))])  # Lower block
        ])
        T_tilde = np.hstack([np.eye(n-1), np.zeros((n-1, 1))])  # Already dense

        
        # Reduced Laplacian (now dense)
        L_tilde = T_tilde @ L @ T_tilde.T
        L_tilde_inv = np.linalg.pinv(L_tilde) #from inv --> pinv due to possibility matrix not being nxn dimension

        # ==========================
        # 5. Compute F_tilde_e
        # ==========================
        F_tilde_e = diag_a @ Fe.T @ np.linalg.inv(T) @ T_tilde.T @ L_tilde_inv @ T_tilde
        return F_tilde_e

  

    def init_res(self):
        H = self.n_hor

        self.cvx_variables['p_RES_net'] = {}
        self.cvx_variables['p_curtailment'] = {}
        self.cvx_parameters['p_RES'] = {}


        for res in self.res_nodes:
            self.cvx_variables['p_RES_net'][res] = cvx.Variable(H)  # Generation power of RES after demand profile and curtailment [W]
            self.cvx_variables['p_curtailment'][res] = cvx.Variable(H)  # Curtailment of renewables [W]
            self.cvx_parameters['p_RES'][res] = cvx.Parameter(H)  # RES prediction

            # Node-specific constraints
            self.constraints += [
                0 <= self.cvx_variables['p_curtailment'][res],
                0 <= self.cvx_parameters['p_RES'][res],
                self.cvx_variables['p_RES_net'][res] == self.cvx_parameters['p_RES'][res] - self.cvx_variables['p_curtailment'][res],
                self.cvx_variables['p_RES_net'][res] <= self.p_res_max,
                0 <= self.cvx_variables['p_RES_net'][res],

            ]

        # Cost calculation for each node
        for j in range(H):
            self.cost += self.cvx_variables['p_curtailment'][res][j] * self.c_curtail * self.dt_s  # kW * eur/kWh * s

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
        #beta0, beta1, beta2 = 4901, 1.98, 0.016  # Example 1 curve fitting coefficients from Paper
        beta0, beta1, beta2 = 3142, 1.68, 8.7 * power(10,-5) 


        self.cvx_parameters["SOC_initial"] = {}
        self.cvx_variables["SOC_batt"] = {}
        self.cvx_variables["p_batt_charge"] = {}
        self.cvx_variables["p_batt_discharge"] = {}
        self.cvx_variables["gamma"] = {}
        self.cvx_variables["SOC_aux"] = {}

        self.cvx_parameters["p_batt_max"] = {}
        self.cvx_parameters["C_batt"] = {}


       
        for ess in self.ess_nodes:
        # Local states for storages
            self.cvx_parameters["SOC_initial"][ess] = cvx.Constant(self.soc_init)
            self.cvx_variables["SOC_batt"][ess] = cvx.Variable(H + 1)  # State of charge (SOC)
            self.cvx_variables["p_batt_charge"][ess] = cvx.Variable(H)  # Charging power
            self.cvx_variables["p_batt_discharge"][ess] = cvx.Variable(H)  # Discharging power
            self.cvx_variables["gamma"][ess] = cvx.Variable(H, boolean=True)  # Binary variable for charge/discharge state

            # Initialize auxiliary SoC variable
            self.cvx_variables["SOC_aux"][ess] = cvx.Variable(H + 1)


            # Power and SOC limits
            self.cvx_parameters["p_batt_max"][ess] = cvx.Constant(self.p_batt_max) # Battery power in W
            self.cvx_parameters["C_batt"][ess] = cvx.Constant(self.c_batt)  # Battery capacity in kWh

            # Initialize constraints list
            self.constraints += [
                self.cvx_variables["SOC_batt"][ess][0] == self.cvx_parameters["SOC_initial"][ess],
                self.cvx_variables["SOC_aux"][ess][0] == self.cvx_parameters["SOC_initial"][ess],
                self.cvx_variables["SOC_batt"][ess][0] == self.cvx_variables["SOC_batt"][ess][-1]  # Cyclic constraint
            ]

            # Add constraints for SOC, charging, discharging, and power limits
            for i in range(H):
                self.constraints += [
                    0 <= self.cvx_variables['gamma'][ess][i],
                    self.cvx_variables['gamma'][ess][i] <= 1,

                    0.2 <= self.cvx_variables["SOC_batt"][ess][i],
                    self.cvx_variables["SOC_batt"][ess][i] <= 0.8,

                    0 * self.cvx_variables["gamma"][ess][i] <= self.cvx_variables["p_batt_charge"][ess][i],
                    self.cvx_variables["p_batt_charge"][ess][i] <= self.cvx_parameters["p_batt_max"][ess] *
                    self.cvx_variables["gamma"][ess][i],

                    0 * (1 - self.cvx_variables["gamma"][ess][i]) <= self.cvx_variables["p_batt_discharge"][ess][i],
                    self.cvx_variables["p_batt_discharge"][ess][i] <= self.cvx_parameters["p_batt_max"][ess] * (
                            1 - self.cvx_variables["gamma"][ess][i]),
                            
                    self.cvx_variables["SOC_batt"][ess][i + 1] == self.cvx_variables["SOC_batt"][ess][i] +
                    (eta_chg * self.cvx_variables["p_batt_charge"][ess][i] - self.cvx_variables["p_batt_discharge"][ess][
                        i] / eta_dsg) * self.dt_s / (3600 * self.cvx_parameters['C_batt'][ess]),


                    self.cvx_variables["SOC_aux"][ess][i + 1] == self.cvx_variables["SOC_batt"][ess][i] - (
                    self.dt_s / (3600 * self.cvx_parameters["C_batt"][ess]) * (
                    self.cvx_variables["p_batt_discharge"][ess][i] / eta_dsg)),

                ]
                
                # SOC in the end of the day is equal to Initial SOC
                # if (i + 1) % 288 == 0:  # Every 288 steps (every 24 hours)
                #     self.constraints += [
                #     self.cvx_variables["SOC_batt"][ess][i + 1] == self.cvx_parameters["SOC_initial"],
                # ]

                # Update cost function with degradation cost
                if i > 0:  # Skip the initial step to avoid indexing issues
                    degradation_cost = MPC_Battery_PCC_RES.degradation_cost_formula(self.cvx_variables["SOC_aux"][ess][i], C_cap, beta0, beta1, beta2) -\
                                    MPC_Battery_PCC_RES.degradation_cost_formula(self.cvx_variables["SOC_batt"][ess][i - 1], C_cap, beta0, beta1, beta2)
                    self.cost += degradation_cost + self.calendar_cost  



            #     self.cost += (
            #     self.cvx_variables["p_batt_charge"][i] * self.batt_cost * self.dt_s -
            #     self.cvx_variables["p_batt_discharge"][i] * self.batt_cost * self.dt_s +
            #     self.cvx_variables["gamma"][i] * self.cycle_cost +
            #     self.calendar_cost * self.dt_s
            # )
            

            # self.power_hub_electric = [self.cvx_variables["p_batt_charge"] - self.cvx_variables["p_batt_discharge"]]


    def init_demand(self):

        self.cvx_parameters["p_demand"] = {}

        for loads in self.load_nodes:
            self.cvx_parameters["p_demand"][loads] = cvx.Parameter(self.n_hor)


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

                # ############### Original: FOR ONE-NODE #############################################
                # self.cvx_variables["p_grid"][j] == self.cvx_parameters["p_demand"][j] - self.cvx_variables["p_RES_net"][j]
                #   + self.cvx_variables["p_batt_charge"][j] - self.cvx_variables["p_batt_discharge"][j],
                # ############### Change here: For MULTIPLE-NODEs ####################################


                self.cvx_variables["p_grid"][j] ==
                    cvx.sum([self.cvx_parameters["p_demand"][load][j] for load in self.load_nodes]) 
                    - cvx.sum([self.cvx_variables["p_RES_net"][res][j] for res in self.res_nodes])
                    + cvx.sum([self.cvx_variables["p_batt_charge"][ess][j] for ess in self.ess_nodes])
                    - cvx.sum([self.cvx_variables["p_batt_discharge"][ess][j] for ess in self.ess_nodes]), 
                
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

    


    def init_pcc_dcpf(self) -> None:
        """Initializes the Point of Common Coupling (PCC) with DC power flow constraints.

        This method replaces the original init_pcc method by incorporating DC power flow
        constraints to model grid physics. It defines variables for grid power exchange,
        line flows, and enforces constraints for line thermal limits and grid connectivity.

        Attributes:
            cvx_variables: Adds optimization variables for grid draw/feed-in, line flows.
            cvx_parameters: Adds parameters for DC power flow matrix and line limits.
        """

        # --------------------------------
        # 0. DC Power Flow line variables
        # --------------------------------
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
        # 2. Grid parameters
        # --------------------------
        self.cvx_parameters['p_grid_max'] = cvx.Constant(self.p_grid_max)
        
        # Add the cost parameters here:
        self.cvx_parameters['cost_draw'] = cvx.Parameter((self.n_hor, 1))
        self.cvx_parameters['cost_feedin'] = cvx.Parameter((self.n_hor, 1))

        # --------------------------
        # 3. DC Power Flow parameters
        # --------------------------
        self.cvx_parameters['F_tilde_e'] = cvx.Parameter(
            (num_edges, len(self.nodes)),
            value=self.F_tilde_e,name='F_tilde_matrix')
        
        self.cvx_parameters['line_limits'] = cvx.Parameter(
            num_edges,
            name='line_thermal_limits'  # [MW]
            )

        self.cost = 0  # Initialize cost

        # # ======================================================================
        # # I. Nodal Power Vector (pe_n)
        # # ======================================================================
        # # Ensure the shapes are compatible for broadcasting
        
        # for j in range(self.n_hor):

        #     pe_n = []
        #     for res, ess, loads in zip(res_nodes, ess_nodes, load_nodes):
        #         pe_n.append(
        #             self.cvx_variables['p_grid'][j]
        #             +self.cvx_parameters['p_demand'][loads][j]
        #             -self.cvx_variables['p_RES_net'][res][j]
        #             - self.cvx_variables['p_batt_charge'][ess][j]
        #             + self.cvx_variables['p_batt_discharge'][ess][j]
        #         )
            
        # Create an empty list to store pe_n for each time step
        pe_n = []
        for j in range(self.n_hor):
            # Build the nodal power vector for time step j
            # Start with p_grid[j]
            nodal_entries = [self.cvx_variables['p_grid'][j]]
            
            #Append all Load values
            nodal_entries += [self.cvx_parameters["p_demand"][loads][j] for loads in self.load_nodes]

            # Append all RES_net values for each RES node at time j
            nodal_entries += [-self.cvx_variables['p_RES_net'][res][j] for res in self.res_nodes]
            
            
            nodal_entries += [self.cvx_variables['p_batt_charge'][ess][j] - self.cvx_variables['p_batt_discharge'][ess][j] for ess in self.ess_nodes] #combine battery charge and discharge to create one node

            # Now stack them vertically
            nodal_pws = cvx.vstack(nodal_entries)  # --> pe_n[j] = [p_grid[j]  p_demand[1][j] ... p_demand[n][j]  p_RES_net[1][j]...p_RES_net[n][j] ... battery ...   ]^T

            pe_n.append(nodal_pws)

                
            # Build a full injection vector for all nodes in self.nodes
            # pe_n = []
            # for node in self.nodes:
            #     if node in self.res_nodes:
            #         # For RES nodes, the injection is the net RES generation.
            #         injection = self.cvx_variables['p_RES_net'][node][j]
            #     elif node in self.ess_nodes:
            #         # For ESS nodes, injection is the discharging minus charging.
            #         injection = - self.cvx_variables['p_batt_charge'][node][j] + self.cvx_variables['p_batt_discharge'][node][j]
            #     elif node in load_nodes:  # load_nodes are the original nodes (imported from RES_ESS_add)
            #         # For original load nodes, injection is the negative of the demand.
            #         injection = - self.cvx_parameters['p_demand'][node][j]
            #     else:
            #         injection = 0  # Default if node does not belong to any of the above categories
            #     pe_n.append(injection)

            #pe_n = cvx.vstack(pe_n)  # pe_n now has dimensions (len(self.nodes) x 1)
            
            

            # Flatten pe_n if necessary or adjust pe_e[:, j]
            self.constraints.extend([

                # self.cvx_variables['pe_e'][:, j].reshape((-1, 1)) == self.cvx_parameters['F_tilde_e'] @ pe_n[j],
                # cvx.abs(self.cvx_variables['pe_e'][:, j])
                # <= self.cvx_parameters['line_limits'],
                
                self.cvx_variables['pe_e'][:, j].reshape((-1, 1), order="F") == self.cvx_parameters['F_tilde_e'] @ pe_n[j],
                cvx.abs(self.cvx_variables['pe_e'][:, j])
                <= self.cvx_parameters['line_limits'],
                
                ])

            # ======================================================================
            # III. Grid Connectivity Constraints
            # ======================================================================
            self.constraints.extend([

                # ########## Power balance equation (for ONE NODE!) ##############
                # self.cvx_variables['p_grid'][j] == (
                #         self.cvx_parameters['p_demand'][j]
                #         - self.cvx_variables['p_RES_net'][j]
                #         + self.cvx_variables['p_batt_charge'][j]
                #         - self.cvx_variables['p_batt_discharge'][j]),
                
                ########## Power balance equation (for MULTIPLE NODES!) ##########
                cvx.sum(pe_n[j]) == 0,

               

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