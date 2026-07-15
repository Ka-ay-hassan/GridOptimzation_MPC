__author__ = "Abdul Azzam"
__copyright__ = "Copyright (C) 2024 Abdul Azzam"
__license__ = "GPL"
__version__ = "1.0"

import cvxpy as cvx
from cvxpy import exp, power
import numpy as np
#from grid2DCpf import UG_edges, UG_nodes, UG_load_nodes, RES_nodes, ESS_nodes
from grid2DCpf import UG_edges

class MPC_Battery_PCC_RES:
    def __init__(self):
        """
        Initialization of the MPC Class for Battery, PCC, and RES
        """

        # Time horizon parameters
        # self.dt_s = 300     # Stepsize in seconds
        # self.n_hor = 288   # Prediction horizon : 288 Steps --> 288 * 300s = 24h

        # self.dt_s = 300     # Stepsize in seconds
        # self.n_hor = 12

        self.dt_s = 900     # Stepsize in seconds
        self.n_hor = 96   # Prediction horizon : 288 Steps --> 288 * 900s = 24h
        #self.n_hor = 5
      

        # Battery parameters
        # self.c_batt = 200000.0  # Battery capacity in kWh
        # self.p_batt_max = 100000.0

        # self.c_batt =     1000000.0 *1e-6  # Battery capacity in kWh
        # self.p_batt_max = 500000.0 *1e-6 

        self.c_batt = 4.5 #* 1e6  # Battery capacity in MWh
        self.p_batt_max = 2.25 #* 1e6


        # self.c_batt = 500000.0 #in W
        # self.p_batt_max = 50000.0 # Maximum battery power in kW

        self.batt_cost = 0.01  # Battery cost in €/kWh
        self.eta_batt = 1.0  # Battery efficiency
        self.soc_init = 0.5  # Initial state of charge

        ### --------------- Kareem addition start --------------- ###
        
        self.calendar_cost = 0.005  # Cost per hour per unit of capacity
        self.cycle_cost = 0.1
        
        ### --------------- Kareem addition end --------------- ###


        # Grid parameters
        #self.p_grid_max = 33000.0  # Maximum grid power in kW
        #self.p_grid_max = 330000.0  # Maximum grid power in kW
        self.p_grid_max = 15.0 # * 1e6
        #self.p_grid_max = 10000000.0 * 1e-6

    

        # Renewable energy parameters
        #self.p_res_max = 100000.0  # Maximum renewable energy power in kW
        self.p_res_max = 5.0 #* 1e6 
        #self.p_res_max = 750000.0 * 1e-6

        self.c_curtail = 0.0  # Curtailment cost €/kWh


        # Nodal Voltage parameters
        self.voltage_nominal = 1.0  # p.u. nominal voltage
        self.voltage_min = 0.95    # p.u.
        self.voltage_max = 1.05     # p.u.   #look up!

        ## Line angles
        self.theta_max = np.deg2rad(90) # since All power flow equations use angles in radians

        # Minimize cost function by minimizing PSI
        self.alpha = 0.05

        # CVXPY Variables and Parameters
        self.cvx_variables = {}
        self.cvx_parameters = {}
        self.constraints = []   #list to hold constraints of optimization 
        self.cost = cvx.Constant(0)

        # ==========================
        # 0. Define Network Topology
        # ==========================

        # Network topology
        # Nodes
        self.nodes = ["PCC", "Load1", "Load2", "RES1", "RES2", "ESS1", "ESS2"]
        # # Edges: (from_node, to_node, shunt susceptance b_sh,ij; susceptance b_ij, g_ij conductance)
        # self.edges = [
        #     ("PCC", "Load1", 1.57e-06, -732, 438), 
        #     ("PCC", "Load2", 2.2e-05, -732, 438),

        #     ("ESS1", "Load1", 2.2e-05, -732, 438),
        #     ("RES1", "Load1", 2.2e-05, -30, 50),
        #     ("RES1", "ESS1", 1.57e-06, -50, 50),

        #     ("ESS2", "Load2", 1.57e-06, -35, 35),
        #     ("RES2", "Load2", 1.57e-06, -732, 425),
        #     ("RES2", "ESS2", 2.2e-05, -50, 40),
        # ]



        # Define which nodes are battery, RES or load
        self.pcc = self.nodes[0] #PCC
        self.load_nodes = ["Load1", "Load2"]   # List of nodes that have Loads
        self.res_nodes = ["RES1", "RES2"]      # List of nodes that have RES
        self.ess_nodes = ["ESS1", "ESS2"]      # List of nodes that have batteries


        # ##### UNCOMMENT for ---> Values of UniGrid ##################
        # self.nodes = UG_nodes
        # self.pcc = self.nodes[0]
        self.edges = UG_edges
        # #RES & ESS nodes
        # self.load_nodes = UG_load_nodes
        # self.res_nodes = RES_nodes
        # self.ess_nodes = ESS_nodes
        # #############################################################

   

        self.cvx_parameters['line_limits'] = cvx.Parameter(len(self.edges))









    def init_res(self):
        H = self.n_hor

        self.cvx_variables['p_RES_net'] = {}
        self.cvx_variables['p_curtailment'] = {}
        self.cvx_parameters['p_RES'] = {}

        self.cvx_variables['q_RES_net'] = {}

        S_max = 1.1 * self.p_res_max # Apparent power limit for RES (slightly higher to handle reactive)/ SolarEdge
        q_max = np.sqrt(S_max**2 - self.p_res_max**2)


        for res in self.res_nodes:
            self.cvx_variables['p_RES_net'][res] = cvx.Variable(H)  # Generation power of RES after demand profile and curtailment [W]
            self.cvx_variables['p_curtailment'][res] = cvx.Variable(H)  # Curtailment of renewables [W]
            self.cvx_parameters['p_RES'][res] = cvx.Parameter(H)  # RES prediction

            self.cvx_variables['q_RES_net'][res] = cvx.Variable(H)  # Generation reactive power of RES after demand profile and curtailment [Var]
            # self.cvx_variables['q_curtailment'][res] = cvx.Variable(H)  # Curtailment of renewables [Var]


            for t in range(H):
                # Node-specific constraints
                self.constraints += [

                    #for active RES power
                    0 <= self.cvx_variables['p_curtailment'][res][t],
                    #self.cvx_variables['p_curtailment'][res][t] <= self.cvx_parameters['p_RES'][res][t],  # Cannot curtail more than exists

                    0 <= self.cvx_parameters['p_RES'][res][t],
                    0 <= self.cvx_variables['p_RES_net'][res][t],  # Cannot output negative active power

                    self.cvx_variables['p_RES_net'][res][t] == self.cvx_parameters['p_RES'][res][t] - self.cvx_variables['p_curtailment'][res][t],
                    self.cvx_variables['p_RES_net'][res][t] <= self.p_res_max,
                    
                    # for reactive RES power
                    cvx.square(self.cvx_variables['q_RES_net'][res][t]) + cvx.square(self.cvx_variables['p_RES_net'][res][t]) <= cvx.square(S_max),  # Apparent power limit
                    cvx.abs(self.cvx_variables['q_RES_net'][res][t]) <= q_max,

                    
                ]

            # # Cost calculation for each node
            # for j in range(H):
            #     self.cost += self.cvx_variables['p_curtailment'][res][j] * self.c_curtail * self.dt_s  # kW * eur/kWh * 1s/3600s/h

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

        steps_per_day = int((24 * 3600) / self.dt_s)

        eta_chg = self.eta_batt  # Charging efficiency
        eta_dsg = self.eta_batt  # Discharging efficiency

        

        S_max = 1.1 * self.p_batt_max  # Apparent power limit for batteries

        q_max = np.sqrt(S_max**2 - self.p_batt_max**2)

        C_cap = 50000 #capital cost example
        #beta0, beta1, beta2 = 4901, 1.98, 0.016  # Example 1 curve fitting coefficients from Paper
        beta0, beta1, beta2 = 3142, 1.68, 8.7 * power(10,-5) 


        self.cvx_parameters["SOC_initial"] = {}
        self.cvx_variables["SOC_batt"] = {}

        self.cvx_variables["p_batt_charge"] = {}
        self.cvx_variables["p_batt_discharge"] = {}

        self.cvx_variables["q_batt_charge"] = {}
        self.cvx_variables["q_batt_discharge"] = {}

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
            self.cvx_variables["q_batt_charge"][ess] = cvx.Variable(H) # Reactive Power
            self.cvx_variables["q_batt_discharge"][ess] = cvx.Variable(H)

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
            ]

            # Add constraints for SOC, charging, discharging, and power limits
            for i in range(H):
                self.constraints += [
                    0 <= self.cvx_variables['gamma'][ess][i],
                    self.cvx_variables['gamma'][ess][i] <= 1,

                    0.2 <= self.cvx_variables["SOC_batt"][ess][i],
                    self.cvx_variables["SOC_batt"][ess][i] <= 0.8,

                    0 * self.cvx_variables["gamma"][ess][i] <= self.cvx_variables["p_batt_charge"][ess][i],
                    self.cvx_variables["p_batt_charge"][ess][i] <= self.cvx_parameters["p_batt_max"][ess] * self.cvx_variables["gamma"][ess][i],

                    0 * (1 - self.cvx_variables["gamma"][ess][i]) <= self.cvx_variables["p_batt_discharge"][ess][i],
                    self.cvx_variables["p_batt_discharge"][ess][i] <= self.cvx_parameters["p_batt_max"][ess] * (1 - self.cvx_variables["gamma"][ess][i]),
                            
                    self.cvx_variables["SOC_batt"][ess][i + 1] == self.cvx_variables["SOC_batt"][ess][i] +
                    (eta_chg * self.cvx_variables["p_batt_charge"][ess][i] - self.cvx_variables["p_batt_discharge"][ess][
                        i] / eta_dsg) * self.dt_s / (3600 * self.cvx_parameters['C_batt'][ess]),

                    #self.cvx_variables["SOC_batt"][ess][0] == self.cvx_variables["SOC_batt"][ess][-1],  # Cyclic constraint

                    # #------------------------ Battery degradation cost---------------------------------------------
                    # self.cvx_variables["SOC_aux"][ess][i + 1] == self.cvx_variables["SOC_batt"][ess][i] - (
                    # self.dt_s / (3600 * self.cvx_parameters["C_batt"][ess]) * (
                    # self.cvx_variables["p_batt_discharge"][ess][i] / eta_dsg)),
                    # #-------------------------------------------------------------------------------------------

                    0 * self.cvx_variables["gamma"][ess][i] <= self.cvx_variables["q_batt_charge"][ess][i],
                    self.cvx_variables["q_batt_charge"][ess][i] <= q_max * self.cvx_variables["gamma"][ess][i],

                    0 * (1 - self.cvx_variables["gamma"][ess][i]) <= self.cvx_variables["p_batt_discharge"][ess][i],
                    self.cvx_variables["q_batt_discharge"][ess][i] <= q_max * (1 - self.cvx_variables["gamma"][ess][i]),


                    cvx.square(self.cvx_variables["p_batt_charge"][ess][i] - self.cvx_variables["p_batt_discharge"][ess][i]) +
                    cvx.square(self.cvx_variables["q_batt_charge"][ess][i] - self.cvx_variables["q_batt_discharge"][ess][i])
                    <= cvx.square(S_max),


                    # cvx.abs(self.cvx_variables["q_batt_charge"][ess][i]) <= q_max * self.cvx_variables["gamma"][ess][i],
                    # cvx.abs(self.cvx_variables["q_batt_discharge"][ess][i]) <= q_max * (1 - self.cvx_variables["gamma"][ess][i]),

                    # cvx.abs(self.cvx_variables["q_batt_discharge"][ess][i]) <= q_max,
                    # cvx.abs(self.cvx_variables["q_batt_charge"][ess][i]) <= q_max,


                ]
                
                # #------------------------ Battery degradation cost - advanced ---------------------------------------------
                # #SOC in the end of the day is equal to Initial SOC
                # if (i + 1) % steps_per_day == 0:  # Every 288 steps (every 24 hours)
                #     self.constraints += [
                #     self.cvx_variables["SOC_batt"][ess][i + 1] == self.cvx_parameters["SOC_initial"][ess],
                # ]
                


                # #Update cost function with degradation cost
                # if i > 0:  # Skip the initial step to avoid indexing issues
                #     degradation_cost = MPC_Battery_PCC_RES.degradation_cost_formula(self.cvx_variables["SOC_aux"][ess][i], C_cap, beta0, beta1, beta2) -\
                #                     MPC_Battery_PCC_RES.degradation_cost_formula(self.cvx_variables["SOC_batt"][ess][i - 1], C_cap, beta0, beta1, beta2)
                #     self.cost += degradation_cost + self.calendar_cost  
                # #--------------------------------------------------------------------------------------------


                self.cost += (
                    self.cvx_variables["p_batt_charge"][ess][i] * self.batt_cost * self.dt_s -
                    self.cvx_variables["p_batt_discharge"][ess][i] * self.batt_cost * self.dt_s +
                    self.cvx_variables["gamma"][ess][i] * self.cycle_cost +
                    self.calendar_cost * self.dt_s )


                # self.cost += (
                #     - self.cvx_variables["p_batt_discharge"][ess][i] * self.batt_cost * self.dt_s +
                #     self.cvx_variables["gamma"][ess][i] * self.cycle_cost +
                #     self.calendar_cost * self.dt_s)

            

            # self.power_hub_electric = [self.cvx_variables["p_batt_charge"] - self.cvx_variables["p_batt_discharge"]]


    def init_demand(self):

        H = self.n_hor

        self.cvx_parameters["p_demand"] = {}
        self.cvx_variables["q_demand"] = {}


        for loads in self.load_nodes:
            self.cvx_parameters["p_demand"][loads] = cvx.Parameter(self.n_hor)
            self.cvx_variables["q_demand"][loads] = cvx.Variable(self.n_hor)

            for t in range(H):
                self.constraints.append(self.cvx_variables['q_demand'][loads][t] == self.cvx_parameters["p_demand"][loads][t] * 0.05)




    

    def angle_constraints(self):
        """Piecewise-linear cos(θ) over θ in [-θ_max,θ_max], plus θ_ij = θ_i-θ_j."""
        H = self.n_hor
        N = len(self.nodes)
        M = len(self.edges)

        # 1) Node‐angle variables
        self.cvx_variables['theta'] = {i: cvx.Variable(H) for i in range(N)}


        # Slack node (index 0) is fixed to zero:
        for t in range(H):
            self.constraints.append(self.cvx_variables['theta'][0][t] == 0)



        # 2) Edge‐angle & cos approximation vars
        self.cvx_variables['theta_ij'] = {e: cvx.Variable(H) for e in range(M)}
        self.cvx_variables['psi']     = {e: cvx.Variable(H) for e in range(M)} #cosine approximation

        # Domain for approximation
        l = -self.theta_max   
        h = +self.theta_max   
        ns = 5                # number of tangent segments 
        tangent_pts = np.linspace(l, h, ns)

        for e, (u, v, *_) in enumerate(self.edges):
            ui = self.nodes.index(u)
            vi = self.nodes.index(v)

            for t in range(H):
                θu  = self.cvx_variables['theta'][ui][t]
                θv  = self.cvx_variables['theta'][vi][t]
                θij = self.cvx_variables['theta_ij'][e][t]
                PSI   = self.cvx_variables['psi'][e][t]

                # (a) Enforce θij = θu – θv, and clamp:
                self.constraints += [
                    θij == θu - θv,
                    θij >= l,
                    θij <= h
                ]

                # (b) Upper‐bound by each tangent line on [l,h]:
                for a in tangent_pts:
                    m = -np.sin(a)
                    b = np.cos(a) 
                    # ψ ≤ m·θij + b
                    self.constraints.append(PSI <= m * (θij-a) + b)



                # # (c) Simple lower‐bound so ψ stays ≥ cos(h)
                # self.constraints.append(PSI >= np.cos(h))

                # # 0 <= ψ <= 1 (43) --> Habibi
                # self.constraints += [ 
                #     0 <= PSI,
                #     PSI <= 1,
                #     ]
                

                # (d) Encourage ψ to be as large as possible
                self.cost -= self.alpha * PSI


       
        
    def voltage_constraints(self):
        """Add voltage AC power flow constraints"""
        H = self.n_hor
        num_nodes = len(self.nodes)

        # Voltage magnitude variables (delta V from nominal)
        self.cvx_variables['delta_V'] = {}
        
        for node in range(num_nodes):
            self.cvx_variables['delta_V'][node] = cvx.Variable(H)

            # Voltage constraints (Eq. 17) - Oussama
            for t in range(H):
                self.constraints += [
                self.cvx_variables['delta_V'][0][t] == 0, # PCC/ slack --> no Voltage change (Oussama Page 6)
                self.voltage_min <= self.voltage_nominal + self.cvx_variables['delta_V'][node][t], # Vi_min ≤ Vi0 + ΔVi, wobei Vi0 = 1 p.u.
                self.voltage_nominal + self.cvx_variables['delta_V'][node][t] <= self.voltage_max, # Vi0 + ΔVi ≤ Vi_max
                ]
            
                # Add small penalty on voltage deviations
                self.cost += 0.001 * self.cvx_variables['delta_V'][node][t]





    def  acopf_pcc(self):
        
        H = self.n_hor
        num_nodes = len(self.nodes)
        num_edges = len(self.edges)

        self.cost = 0

        #S_grid_max = self.p_grid_max * 1.1

        #q_grid_max = np.sqrt(S_grid_max**2+self.p_grid_max**2)
        # --------------------------
        # 1. Define PCC variables
        # --------------------------
        self.cvx_variables['p_grid_draw'] = cvx.Variable(self.n_hor)
        self.cvx_variables['p_grid_feedin'] = cvx.Variable(self.n_hor)
        self.cvx_variables['p_grid'] = cvx.Variable(self.n_hor)  # Grid power [W]
        self.cvx_variables['gamma_grid'] = cvx.Variable(self.n_hor, boolean=True, name='grid_state_binary')

        self.cvx_variables['q_grid'] = cvx.Variable(self.n_hor) # Grid reactive power [var]

        # --------------------------
        # 2. Grid parameters
        # --------------------------
        self.cvx_parameters['p_grid_max'] = cvx.Constant(self.p_grid_max)
        self.cvx_parameters['q_grid_max']   = cvx.Constant(self.p_grid_max * 0.5)
        #self.cvx_parameters['q_grid_max']   = cvx.Constant(q_grid_max)

        # Add the cost parameters here:
        self.cvx_parameters['cost_draw'] = cvx.Parameter((self.n_hor, 1))
        self.cvx_parameters['cost_feedin'] = cvx.Parameter((self.n_hor, 1))

      

        q_grid_penalty = 1e-3 # to reduce reactive power in Grid


        # -----------------------------
        # 3. AC Power Flow parameters
        # -----------------------------

       

        # 3.1) Line‐flow variables
        self.cvx_variables['p_line'] = cvx.Variable((num_edges, H), name='p_line_flows')
        self.cvx_variables['q_line'] = cvx.Variable((num_edges, H), name='q_line_flows')

        #self.cvx_variables['alpha_line'] = cvx.Variable((num_edges, H)) # soft constraint alpha for line flow


       
       # --- declare bus‐injections (you already have these) ---
        self.cvx_variables['p_bus'] = { node: [cvx.Variable(name=f"p_bus_{node}_{t}") for t in range(H)] for node in self.nodes}
        self.cvx_variables['q_bus'] = { node: [cvx.Variable(name=f"q_bus_{node}_{t}") for t in range(H)] for node in self.nodes}

    
        

        for edge, (from_node, to_node, b_sh_ij, b_ij, g_ij) in enumerate(self.edges):

            from_idx = self.nodes.index(from_node)
            to_idx = self.nodes.index(to_node)

            # Power flow equations             
            for t in range(H):
                Vi0 = self.voltage_nominal
                Vj0 = self.voltage_nominal

                psi    = self.cvx_variables['psi'][edge][t]
                theta_ = self.cvx_variables['theta_ij'][edge][t]
                dVi    = self.cvx_variables['delta_V'][from_idx][t]
                dVj    = self.cvx_variables['delta_V'][to_idx][t]

                #-------------------------------------------------------------------------------------------------------------
                # # constant part of P in eq. (16) - Habibi 
                # p_t     = Vi0 * g_ij - Vi0 * (psi * g_ij + b_ij * theta_)
                
                # # linear delta‐part of P (eq.21) - Habibi
                # p_delta = Vi0 * g_ij * (dVi - dVj) + (Vi0 - Vj0) * g_ij * dVi


                # # constant part of Q (eq.17) - Habibi
                # q_t     = -cvx.square(Vi0) * b_ij - Vi0 * Vj0 * (g_ij * theta_ - b_ij * psi) - (b_sh_ij/2) * cvx.square(Vi0)

                # # linear delta‐part of Q (eq.20) -  Habibi
                # q_delta = -Vi0 * b_ij * (dVi - dVj) - (Vi0 - Vj0) * b_ij * dVi- b_sh_ij * Vi0 * dVi

                # self.constraints += [
                #     # Linearized active power flow  --> (12) - Habibi       --> (7) Oussama
                #     self.cvx_variables['p_line'][edge][t] == p_t + p_delta,

                #     # # Linearized reactive power flow  --> (13) - Habibi       --> (8) Oussama
                #     # self.cvx_variables['q_line'][edge][t] == q_t + q_delta,

                #     self.cvx_variables['p_line'][edge][t] <= self.cvx_parameters['line_limits'][edge], # (44) --> Habibi
                #     -self.cvx_parameters['line_limits'][edge] <= self.cvx_variables['p_line'][edge][t] ,
                # ]
                #--------------------------------------------------------------------------------------------------------------

                #p_ij according to Oussama (eq. 7)
                p_t     = g_ij - Vi0 * (psi * g_ij + b_ij * theta_)

                #q_delta 
                q_t = -(0.5*b_sh_ij+b_ij) - (g_ij * theta_ - b_ij * psi)

                q_delta = -2 * (0.5 * b_sh_ij + b_ij) * dVi + b_ij * (dVi + dVj)

                
                self.constraints += [
                    # Linearized active power flow  --> (7) Oussama
                    self.cvx_variables['p_line'][edge][t] == p_t,

                    # Linearized reactive power flow  --> (8) Oussama
                    self.cvx_variables['q_line'][edge][t] == q_t + q_delta,

                    self.cvx_variables['p_line'][edge][t]**2 + self.cvx_variables['q_line'][edge][t]**2
                    <= self.cvx_parameters['line_limits'][edge]**2, # Oussama

                    
                    # 0 <= self.cvx_variables['alpha_line'][edge][t],
                    # self.cvx_variables['alpha_line'][edge][t] <= 1,

                    # cvx.abs(self.cvx_variables['p_line'][edge][t]) <= self.cvx_parameters['line_limits'][edge] * self.cvx_variables['alpha_line'][edge][t], # Oussama
                ]


        # 1) Build map of outgoing edges once
        out_edges = {node: [] for node in self.nodes}
        for e, (u, v, *_) in enumerate(self.edges):
            out_edges[u].append(e)

        # 3.2) Build incidence matrix Fe (nodes × edges)
        Fe = np.zeros((num_nodes, num_edges))
        for e, (u, v, *_) in enumerate(self.edges):
            ui = self.nodes.index(u)
            vi = self.nodes.index(v)
            Fe[ui, e] = +1   # flow leaves u
            Fe[vi, e] = -1   # flow enters v

        # # After building Fe, print it for verification
        # print("\n--- Debug: Incidence Matrix ---")
        # print("Fe matrix (nodes x edges):")
        # print(Fe)

        # Identify slack (PCC) and non-slack buses
        pcc_idx = self.nodes.index(self.pcc)
        non_slack_idx = [i for i in range(num_nodes) if i != pcc_idx]

        # 3.3) Per-time-step nodal KCL using Fe
        for t in range(H):
            p_line_vec = self.cvx_variables['p_line'][:, t]
            q_line_vec = self.cvx_variables['q_line'][:, t]



            for node in self.nodes:
                p_expr = 0
                if node in self.res_nodes:
                    p_expr += self.cvx_variables["p_RES_net"][node][t]
                if node in self.load_nodes:
                    p_expr -= self.cvx_parameters["p_demand"][node][t]
                if node in self.ess_nodes:
                    p_expr += self.cvx_variables["p_batt_discharge"][node][t]
                    p_expr -= self.cvx_variables["p_batt_charge"][node][t]
                if node == self.pcc:
                    p_expr += self.cvx_variables["p_grid_draw"][t]
                    p_expr -= self.cvx_variables["p_grid_feedin"][t]

                self.constraints.append(self.cvx_variables['p_bus'][node][t] == p_expr)

            p_inj_ns = [self.cvx_variables['p_bus'][self.nodes[i]][t] for i in non_slack_idx]


            for node in self.nodes:
                q_expr = 0
                if node in self.res_nodes:
                    q_expr += self.cvx_variables["q_RES_net"][node][t]
                if node in self.load_nodes:
                    q_expr -= self.cvx_variables["q_demand"][node][t]
                if node in self.ess_nodes:
                    q_expr += self.cvx_variables["q_batt_discharge"][node][t]
                    q_expr -= self.cvx_variables["q_batt_charge"][node][t]
                if node == self.pcc:
                    q_expr += self.cvx_variables["q_grid"][t]
                self.constraints.append(self.cvx_variables['q_bus'][node][t] == q_expr)

            q_inj_ns = [self.cvx_variables['q_bus'][self.nodes[i]][t] for i in non_slack_idx]

            

            self.constraints += [
                Fe[non_slack_idx, :] @ p_line_vec == cvx.hstack(p_inj_ns),
                Fe[non_slack_idx, :] @ q_line_vec == cvx.hstack(q_inj_ns),

                # PCC power injection equals grid power
                self.cvx_variables['p_bus']["PCC"][t] == self.cvx_variables['p_grid'][t],
                self.cvx_variables['q_bus']["PCC"][t] == self.cvx_variables['q_grid'][t]

            ]

            # Slack bus: Fe[pcc] * p_line == p_grid
            self.constraints += [
                Fe[pcc_idx, :] @ p_line_vec == self.cvx_variables['p_grid'][t],
                Fe[pcc_idx, :] @ q_line_vec == self.cvx_variables['q_grid'][t]
            ]
                

        #-------------------------------------------
        # 4) PCC constraints & cost
        #-------------------------------------------



        for j in range(H):
            self.constraints += [
                # binary selector
                0 <= self.cvx_variables['gamma_grid'][j],
                self.cvx_variables['gamma_grid'][j] <= 1,

                # net grid power = draw − feed‐in
                self.cvx_variables['p_grid'][j] 
                == self.cvx_variables['p_grid_draw'][j] - self.cvx_variables['p_grid_feedin'][j],

                # no simultaneous draw & feed‐in
                self.cvx_variables['p_grid_feedin'][j] <= self.cvx_parameters['p_grid_max'] * self.cvx_variables['gamma_grid'][j],
                self.cvx_variables['p_grid_draw'][j] <= self.cvx_parameters['p_grid_max'] * (1 - self.cvx_variables['gamma_grid'][j]),

                # sign and limits
                0 <= self.cvx_variables['p_grid_draw'][j],
                0 <= self.cvx_variables['p_grid_feedin'][j],


                -self.cvx_parameters['q_grid_max'] <= self.cvx_variables['q_grid'][j],
                self.cvx_variables['q_grid'][j] <= self.cvx_parameters['q_grid_max'],

             ]

            # energy cost
            self.cost += (
                self.cvx_variables['p_grid_draw'][j] * self.cvx_parameters['cost_draw'][j]
                - self.cvx_variables['p_grid_feedin'][j]* self.cvx_parameters['cost_feedin'][j]
            ) * self.dt_s

            # # small penalty on reactive slack
            self.cost += q_grid_penalty * cvx.abs(self.cvx_variables['q_grid'][j])