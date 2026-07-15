import pandas as pd
import numpy as np

nodes = ["PCC", "Load1", "Load2", "RES1", "RES2", "ESS1", "ESS2"]
edges = [
            ("PCC", "Load1", 0.2, 0.1, 0.01), 
            ("ESS1", "Load1", 0.1, 0.12, 0.05),
            ("RES1", "Load1", 0.15, 0.17, 0.08),
            ("ESS1", "RES1", 0.25, 0.16, 0.012),
            ("PCC", "Load2", 0.23, 0.14, 0.011),
            ("ESS2", "Load2", 0.12, 0.14, 0.06),
            ("RES2", "Load2", 0.15, 0.135, 0.08),
            ("ESS2", "RES2", 0.23, 0.12, 0.011),
]

num_nodes = len(nodes)
num_edges = len(edges)

# 3) Build incidence matrix Fe (nodes × edges)
Fe = np.zeros((num_nodes, num_edges))
for edge, (from_node, to_node, *_) in enumerate(edges):
    from_idx = nodes.index(from_node)
    to_idx = nodes.index(to_node)
    Fe[from_idx, edge] =  1  # flow leaves u
    Fe[to_idx, edge] = -1  # flow enters v


print(Fe)