import numpy as np
#from grid2DCpf import T_nodes, T_edges



T_nodes = ["PCC", "Load1", "Load2", "RES1", "RES2", "ESS1", "ESS2"]
        # Edges: (from_node, to_node, shunt susceptance b_sh,ij; susceptance b_ij, g_ij conductance)
T_edges = [
    ("PCC", "Load1", 1.57e-06), 
    ("PCC", "Load2", 2.2e-05),

    ("ESS1", "Load1", 2.2e-05),
    ("RES1", "Load1", 2.2e-05),
    ("RES1", "ESS1", 1.57e-06,),

    ("ESS2", "Load2", 1.57e-06),
    ("RES2", "Load2", 1.57e-06),
    ("ESS2", "RES2", 2.2e-05),
]

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
print("Incidence:\n ",Fe)

print("diag a dim: ",diag_a.shape)

print("T_tilde dim: ",T_tilde.shape)
print("L_tilde dim: ",L_tilde.shape)
print("L_tilde_inv dim: ",L_tilde_inv.shape)


print("F_tilde dim: ",F_tilde_e.shape)