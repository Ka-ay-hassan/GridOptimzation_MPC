import numpy as np
import matplotlib.pyplot as plt

# Parameters for the calculation
beta0, beta1, beta2 = 4901, 1.98, 0.016

# Generate SOC values from 0.2 to 0.8
SOC = np.linspace(0, 1, 25)

# Calculate Ncycle using the provided formula
DOD = 1-SOC 
Ncycle = beta0 * np.power(DOD, -beta1) * np.exp(beta2 * (1 - DOD))

# Plotting the graph of Ncycle
plt.figure(figsize=(10, 6))
plt.plot(SOC, Ncycle, label='Ncycle vs. SOC', color='blue')
plt.title('Graph of Ncycle as a function of SOC')
plt.xlabel('State of Charge (SOC)')
plt.ylabel('Ncycle')
plt.grid(True)
plt.legend()
plt.savefig('Ncycle_vs_SOC.png')  # Save the plot to a file
plt.show()
