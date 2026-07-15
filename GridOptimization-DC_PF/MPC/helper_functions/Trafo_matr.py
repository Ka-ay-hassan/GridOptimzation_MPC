import numpy as np
from grid2DCpf import T_nodes, T_edges



# # Nodes in specified order: PCC, ESS, P2H, RES, Loads
# T_nodes = ["PCC", "ESS1", "P2H1", "RES1", "Load1"]

# # Edges: (from_node, to_node, susceptance)
# T_edges = [
#     ("PCC", "Load1", 0.2),
#     ("ESS1", "Load1", 0.1),
#     ("RES1", "Load1", 0.15),
#     ("ESS1", "RES1", 0.25),
#     ("RES1", "P2H1", 0.15),
#     ("ESS1", "P2H1", 0.3)
# ]

num_nodes = len(T_nodes)
num_edges = len(T_edges)
Fe = np.zeros((num_nodes, num_edges))

for edge_idx, (from_node, to_node, _) in enumerate(T_edges):
    from_idx = T_nodes.index(from_node)
    to_idx = T_nodes.index(to_node)
    Fe[from_idx, edge_idx] = 1
    Fe[to_idx, edge_idx] = -1

# ==========================
# 2. Compute Edge Parameters (a)
# ==========================
a = np.array([b for _, _, b in T_edges]) * 1.0 * 1.0  # a_i = b_ml * v_m * v_l

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


print('Number of nodes:', len(T_nodes))

print("Fe dim: ",Fe.shape)
print("diag a dim: ",diag_a.shape)

print("T_tilde dim: ",T_tilde.shape)
print("L_tilde dim: ",L_tilde.shape)
print("L_tilde_inv dim: ",L_tilde_inv.shape)


print("F_tilde dim: ",F_tilde_e.shape)