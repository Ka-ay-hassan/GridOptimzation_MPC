# This file is supposed to imitate DC-Powerflow with a simple example

import numpy as np
from scipy.sparse import diags, block_diag
from scipy.linalg import pinv
from grid2DCpf import T_nodes, T_edges, P_mw
#from RES_ESS_add import T_nodes, T_edges


# ==========================
# 1. Define Network Topology
# ==========================

# Nodes in specified order: PCC, ESS, P2H, RES, Loads
# nodes = ["PCC", "ESS1", "P2H1", "RES1", "Load1"]
# num_nodes = len(nodes)

# Edges: (from_node, to_node, susceptance)
# edges = [
#     ("PCC", "Load1", 0.2),
#     ("ESS1", "Load1", 0.1),
#     ("RES1", "Load1", 0.15),
#     ("ESS1", "RES1", 0.25),
#     ("RES1", "P2H1", 0.15),
#     ("ESS1", "P2H1", 0.3)
# ]
# num_edges = len(edges)

nodes = T_nodes
num_nodes = len(nodes)
 
edges = T_edges
num_edges = len(edges)

# ==========================
# 2. Construct Incidence Matrix
# ==========================
Fe = np.zeros((num_nodes, num_edges))
for edge_idx, (from_node, to_node, _) in enumerate(edges):
    from_idx = nodes.index(from_node)
    to_idx = nodes.index(to_node)
    Fe[from_idx, edge_idx] = 1
    Fe[to_idx, edge_idx] = -1

# ==========================
# 3. Compute Edge Parameters
# ==========================
# Assume constant voltage magnitudes = 1.0 pu
a = np.array([b for _, _, b in edges]) * 1.0 * 1.0  # a_i = b_ml * v_m * v_l

# ==========================
# 4. Build Laplacian Matrix
# ==========================
diag_a = diags(a)
L = Fe @ diag_a @ Fe.T


# ==========================
# 5. Build Laplacian Matrix
# ==========================
# diag_a = diags(a).toarray()  # Convert to dense upfront
# L = Fe @ diag_a @ Fe.T

# ==========================
# 6. Transformation Matrices
# ==========================
n = num_nodes 
T = np.vstack([
    np.hstack([np.eye(n-1), -np.ones((n-1, 1))]),  # Upper block
    np.hstack([np.zeros((1, n-1)), np.ones((1, 1))])  # Lower block
])
T_tilde = np.hstack([np.eye(n-1), np.zeros((n-1, 1))])  # Already dense

# Reduced Laplacian (now dense)
L_tilde = T_tilde @ L @ T_tilde.T
L_tilde_inv = np.linalg.pinv(L_tilde)


# ==========================
# 7. Compute F_tilde Matrix
# ==========================
F_tilde_e = diag_a @ Fe.T @ np.linalg.inv(T) @ T_tilde.T @ L_tilde_inv @ T_tilde

# ==========================
# 8. Define Nodal Power Vector
# ==========================


# Define Stable Nodal Power Vector
# Assign a specific power value to each node
pe_n = np.zeros(num_nodes)
for i in range(num_nodes):
    if i % 2 == 0:
        pe_n[i] = 0.5  # Assuming even indexed nodes are generators
    else:
        pe_n[i] = -0.5  # Assuming odd indexed nodes are loads

# Adjust the last value to ensure the sum is zero for balance
pe_n[-1] -= pe_n.sum()


# Verify power balance
assert np.isclose(pe_n.sum(), 0), f"Power imbalance: {pe_n.sum()}"

# ==========================
# 9. Calculate Line Flows
# ==========================
pe_e = F_tilde_e @ pe_n  # No more NameError



# ==========================
# 8. ESS State of Charge Model
# ==========================
delta_t = 1  # hour
B_e = np.eye(1) * delta_t  # For 1 ESS

def update_ess(xe_current, ue_s):
    return xe_current + B_e @ ue_s


# ==========================
# 9. Print Results
# ==========================
print("Incidence Matrix Fe:")
print(Fe)
print("\nLine Power Flows:")
for i, flow in enumerate(pe_e):
    print(f"Line {i}: {flow:.2f} MW")
print("\nF_tilde Matrix:")
print(F_tilde_e)  # No .toarray() needed

# Sample ESS update
xe_current = np.array([50])  # 50 MWh
ue_s = np.array([-0.2])      # Charging at 0.2 MW
xe_next = update_ess(xe_current, ue_s)
print(f"\nESS State: {xe_current[0]} -> {xe_next[0]} MWh")

print('\n')
print('Length of Pe_n:', len(pe_n))
print('\n')
print('Dim of Pe_n:', pe_n.shape)
print('\n')
print('Pe_n:', pe_n)

print('\n')
print('Length of Pe_e:', len(pe_e))
print('\n')
print('Pe_e:', pe_e)