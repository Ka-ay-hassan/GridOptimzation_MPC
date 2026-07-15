import numpy as np
import matplotlib.pyplot as plt

# Generate a decaying cost curve
x = np.linspace(0.2, 0.8, 500)
y = 1.1 * np.exp(-2.2 * x) + 0.05

# Shift points left by 0.05 on the x-axis
shift = 0.05

# Original spans: ΔSoC1 = 0.10, ΔSoC2 = 0.15
x1_X = 0.80 - shift
x1_Y = x1_X - 0.10
x2_X = 0.50 - shift
x2_Y = x2_X - 0.15

# Compute corresponding y-values
y1_X = 1.1 * np.exp(-2.2 * x1_X) + 0.05
y1_Y = 1.1 * np.exp(-2.2 * x1_Y) + 0.05
y2_X = 1.1 * np.exp(-2.2 * x2_X) + 0.05
y2_Y = 1.1 * np.exp(-2.2 * x2_Y) + 0.05

plt.figure(figsize=(8, 6))

# Plot the main cost curve
plt.plot(x, y, color='tab:orange', linewidth=2)

# Blue group: X2 & Y2
plt.scatter([x2_X, x2_Y], [y2_X, y2_Y], color='blue', marker='o', zorder=5)
plt.hlines(y2_X, 0, x2_X, colors='blue', linestyles='dashed')
plt.vlines(x2_X, 0, y2_X, colors='blue', linestyles='dashed')
plt.hlines(y2_Y, 0, x2_Y, colors='blue', linestyles='dashed')
plt.vlines(x2_Y, 0, y2_Y, colors='blue', linestyles='dashed')

# Green group: X1 & Y1
plt.scatter([x1_X, x1_Y], [y1_X, y1_Y], color='green', marker='o', zorder=5)
plt.hlines(y1_X, 0, x1_X, colors='green', linestyles='dashed')
plt.vlines(x1_X, 0, y1_X, colors='green', linestyles='dashed')
plt.hlines(y1_Y, 0, x1_Y, colors='green', linestyles='dashed')
plt.vlines(x1_Y, 0, y1_Y, colors='green', linestyles='dashed')

# Annotate points with larger font
annot_kwargs = dict(textcoords='offset points', fontsize=20)
plt.annotate('X2', (x2_X, y2_X +0.05), xytext=(5, -15), **annot_kwargs)
plt.annotate('Y2', (x2_Y, y2_Y), xytext=(5, 5), **annot_kwargs)
plt.annotate('X1', (x1_X, y1_X + 0.05), xytext=(5, -15), **annot_kwargs)
plt.annotate('Y1', (x1_Y, y1_Y), xytext=(5, 5), **annot_kwargs)

# Draw ΔC_E arrows on the left (y-axis) with larger labels
arrow_kwargs = dict(arrowstyle='<->')
plt.annotate('', (0.21, y1_X), xytext=(0.21, y1_Y), arrowprops=dict(color='green', **arrow_kwargs))
plt.text(0.22, (y1_X + y1_Y) / 2, r'$\Delta C_{E,1}$', va='center', color='green', fontsize=24)

plt.annotate('', (0.21, y2_X), xytext=(0.21, y2_Y), arrowprops=dict(color='blue', **arrow_kwargs))
plt.text(0.22, (y2_X + y2_Y) / 2, r'$\Delta C_{E,2}$', va='center', color='blue', fontsize=24)

# Draw ΔSoC arrows along the bottom (x-axis) with larger labels
plt.annotate('', (x1_Y, 0.02), xytext=(x1_X, 0.02), arrowprops=dict(arrowstyle='<->'))
plt.text((x1_X + x1_Y) / 2, -0.035, r'$\Delta SoC_1$', ha='center', fontsize=24)

plt.annotate('', (x2_Y, 0.02), xytext=(x2_X, 0.02), arrowprops=dict(arrowstyle='<->'))
plt.text((x2_X + x2_Y) / 2, -0.035, r'$\Delta SoC_2$', ha='center', fontsize=24)

# Labels and limits: larger axis labels and tick labels
plt.xlabel('State of Charge (SoC)', fontsize=24)
plt.ylabel('One-cycle Degradation Cost ($C_E$)', fontsize=24)
plt.xticks(fontsize=18)
plt.yticks([])  # hide y-axis ticks
plt.xlim(0.2, 0.8)
plt.ylim(-0.05, y.max() + 0.1)
plt.tight_layout()
plt.show()
