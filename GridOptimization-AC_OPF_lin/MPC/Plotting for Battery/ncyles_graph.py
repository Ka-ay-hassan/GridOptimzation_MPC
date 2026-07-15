import numpy as np
import matplotlib.pyplot as plt

# Parameters
beta0, beta1, beta2 = 3142, 1.68, 8.7e-5

# Generate SOC and compute DOD and Ncycle
SOC = np.linspace(0.8, 0.2, 24)
DOD = 1 - SOC
Ncycle = beta0 * DOD**(-beta1) * np.exp(beta2 * (1 - DOD))

# Plot
plt.figure(figsize=(10, 6))

# Thicker blue line
plt.plot(
    DOD * 100,
    Ncycle,
    color='blue',
    linewidth=3,             # thicker line
    label='Ncycle vs. DOD'
)

# Thicker red '+' markers
plt.plot(
    DOD * 100,
    Ncycle,
    linestyle='',
    marker='+',
    color='red',
    markersize=12,           # larger marker size
    markeredgewidth=4,       # thicker '+' lines
    label='Data'
)

# Titles and labels with bigger font
#plt.title('Number of Cycles as a Function of Depth of Discharge', fontsize=18)
plt.xlabel('Depth of Discharge (DOD) [%]', fontsize=20)
plt.ylabel('Number of Cycles', fontsize=20)

# Increase tick label font size
plt.tick_params(axis='both', which='major', labelsize=22)

plt.grid(True)

# Make the legend text larger
plt.legend(fontsize=14)

plt.tight_layout()
plt.show()
