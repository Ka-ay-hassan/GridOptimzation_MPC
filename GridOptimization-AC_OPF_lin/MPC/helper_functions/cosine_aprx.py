import numpy as np
import matplotlib.pyplot as plt

# Define angle range and segments
angle_max = 25 * np.pi / 180  # 25 degrees in radians (you had 30 degrees comment but 25 deg in code)
n_cos_segments = 5

# Tangent points (where the cosine will be approximated)
tangent_points = np.linspace(-angle_max, angle_max, n_cos_segments)

# Generate fine angle grid for plotting the true cosine curve
theta = np.linspace(-angle_max * 1.2, angle_max * 1.2, 500)
cos_values = np.cos(theta)

# Plot setup
plt.figure(figsize=(8, 5))
plt.plot(theta, cos_values, label='cos(θ)', color='blue', linewidth=2)  # thicker line

plt.scatter(tangent_points, np.cos(tangent_points), color='red', label='Tangent Points', s=60)  # bigger markers

# Plot tangent lines at those points
for x0 in tangent_points:
    y0 = np.cos(x0)
    slope = -np.sin(x0)
    x_vals = np.linspace(x0 - 0.1, x0 + 0.1, 100)
    tangent_line = y0 + slope * (x_vals - x0)
    plt.plot(x_vals, tangent_line, color='red', linestyle='--', alpha=1, linewidth=1.5)  # thicker dashed lines

# Final touches
plt.axhline(0, color='gray', linewidth=1)
plt.axvline(0, color='gray', linewidth=1)
plt.title("Cosine Function with Tangent Approximations", fontsize=22)
plt.xlabel("θ (radians)", fontsize=22)
plt.ylabel("cos(θ)", fontsize=22)
plt.legend(fontsize=20)
plt.ylim(0.8, 1.01)  # Set y-axis limits
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)


plt.grid(True)
plt.tight_layout()
plt.show()
