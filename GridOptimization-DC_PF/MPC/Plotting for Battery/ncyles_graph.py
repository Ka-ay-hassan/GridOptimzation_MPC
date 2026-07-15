import numpy as np
import matplotlib.pyplot as plt

# Parameters for the calculation
beta0, beta1, beta2 = 4901, 1.98, 0.016

# Generate SOC values from 0 to 1
SOC = np.linspace(0, 1, 25)

# Calculate Ncycle using the provided formula
DOD = 1 - SOC 
Ncycle = beta0 * np.power(DOD, -beta1) * np.exp(beta2 * (1 - DOD))

# Plotting the graph of Ncycle
plt.figure(figsize=(10, 6))
plt.plot(DOD, Ncycle, label='Ncycle vs. SOC', color='blue')

# Increase font sizes here
plt.title('Graph of Ncycle as a function of SOC', fontsize=24)
plt.xlabel('State of Charge (SOC)', fontsize=22)
plt.ylabel('Ncycle', fontsize=22)

# Increase tick label sizes for both axes
plt.xticks(fontsize=20)
plt.yticks(fontsize=20)

plt.grid(True)

# Legend with larger font
plt.legend(fontsize=22)

#plt.savefig('Ncycle_vs_SOC.png')  # Save the plot to a file
plt.show()
