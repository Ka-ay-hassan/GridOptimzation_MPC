import matplotlib.pyplot as plt

# Time offset for auxiliary curve during charge
dt = 0.5

# Segment 1: Discharge (aux matches actual)
t1 = [0, 1, 2, 3, 4]
soc1 = [1.0, 0.8, 0.6, 0.4, 0.2]

# Segment 2: Charge (aux shifted horizontally, y matches actual)
t2_actual = [4, 5, 6, 7]
t2_aux    = [t + dt for t in t2_actual]
soc2      = [0.2, 0.5, 0.75, 1.0]

# Bridge horizontal segment to avoid discontinuity
t_bridge1 = [4, 4 + dt]
soc_bridge1 = [0.2, 0.2]

# Segment 3: Discharge (aux now matches actual, no shift)
t3 = [7, 8, 9, 10]
soc3 = [1.0, 0.85, 0.6, 0.35]

# Segment 4: Charge (aux shifted horizontally, y matches actual)
t4_actual = [10, 11, 12]
t4_aux    = [t + dt for t in t4_actual]
soc4      = [0.35, 0.7, 1.0]

# Bridge horizontal segment for second charge
t_bridge2 = [10, 10 + dt]
soc_bridge2 = [0.35, 0.35]

plt.figure(figsize=(10, 4))

# Plot actual and auxiliary for discharge segments
plt.plot(t1, soc1, marker='s', linestyle='-', label='Actual SoC', color='magenta')
plt.plot(t1, soc1, marker='D', linestyle='--', label='Auxiliary SoC', color='cyan')

# Plot charge segments with aux shift
plt.plot(t2_actual, soc2, marker='s', linestyle='-', color='magenta')
plt.plot(t2_aux,    soc2, marker='D', linestyle='--', color='cyan')
plt.plot(t_bridge1, soc_bridge1, linestyle='--', marker='D', color='cyan')

# Plot discharge segment with no shift
plt.plot(t3, soc3, marker='s', linestyle='-', color='magenta')
plt.plot(t3, soc3, marker='D', linestyle='--', color='cyan')

# Plot charge segments with aux shift
plt.plot(t4_actual, soc4, marker='s', linestyle='-', color='magenta')
plt.plot(t4_aux,    soc4, marker='D', linestyle='--', color='cyan')
plt.plot(t_bridge2, soc_bridge2, linestyle='--', marker='D', color='cyan')

# Annotate arrows
plt.annotate('discharge', xy=(2, 0.6), xytext=(3, 0.75), arrowprops={'arrowstyle': '->'})
plt.annotate('charge',    xy=(5.5, 0.375), xytext=(4.5, 0.2), arrowprops={'arrowstyle': '->'})
plt.annotate('discharge', xy=(9, 0.6), xytext=(10, 0.75), arrowprops={'arrowstyle': '->'})
plt.annotate('charge',    xy=(11, 0.7), xytext=(10, 0.55), arrowprops={'arrowstyle': '->'})

# Δt brackets
# Charge starts
for base in [4, 10]:
    plt.annotate('', xy=(base, 0.02), xytext=(base + dt, 0.02), arrowprops={'arrowstyle': '<->'})
    plt.text(base + dt/2, 0.05, 'Δt', ha='center')
# Discharge start (sync)
plt.annotate('', xy=(7, 0.02), xytext=(7, 0.02), arrowprops={'arrowstyle': '<->'})
plt.text(7, 0.05, 'Δt=0', ha='center')

# Labels, legend, and grid
plt.xlabel('time')
plt.ylabel('SoC')
plt.ylim(0, 1.1)
plt.xlim(0, 12.7)
plt.legend(loc='lower left')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
