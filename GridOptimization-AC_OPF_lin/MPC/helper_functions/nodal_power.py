# This code adjusts checks the dimensions of the nodal powers pe_n as a vector
# Necassary for the DCPF


import numpy as np

# Example: 5 time steps
n_hor = 5

# Example values:
# p_grid is a 1D array with 5 time steps
p_grid = np.array([10, 11, 12, 13, 14])  # shape: (5,)

# p_RES_net with 2 RES values over 5 time steps (shape: (2, 5))
p_RES_net = np.array([[1, 2, 3, 4, 5],
                      [1.5, 2.5, 3.5, 4.5, 5.5]])

# battery with 3 battery values over 5 time steps (shape: (3, 5))
battery = np.array([[0.5, 0.6, 0.7, 0.8, 0.9],
                    [0.3, 0.4, 0.5, 0.6, 0.7],
                    [0.2, 0.2, 0.3, 0.3, 0.4]])

# Initialize an empty list to store pe_n for each time step
pe_n = []

# Loop over each time step j
for j in range(n_hor):
    # Extract the j-th value from p_grid (as a 1-element array)
    pgrid_j = np.array([p_grid[j]])
    
    # Extract the j-th column from p_RES_net and battery.
    # Note: p_RES_net[:, j] and battery[:, j] are 1D arrays.
    res_j = p_RES_net[:, j]
    bat_j = battery[:, j]
    
    # Concatenate to form the vector for time step j
    pe_n_j = np.concatenate((pgrid_j, res_j, bat_j))
    
    # Append this vector to our list
    pe_n.append(pe_n_j)

# Convert list to a NumPy array for easier handling
pe_n = np.array(pe_n)

# Now, pe_n[j] is the vector for time step j.
# Its shape is (n_hor, 1+n_res+n_bat). In our case, that's (5, 6).
print("pe_n for each time step:")
print(pe_n)
print("Shape of pe_n:", pe_n.shape)
print(pe_n[0])
