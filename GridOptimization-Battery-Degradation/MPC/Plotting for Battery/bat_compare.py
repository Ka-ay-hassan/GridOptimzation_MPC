import pandas as pd
import matplotlib.pyplot as plt
import os

# Base directory on your PC
base_dir = "C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC"

# Files dictionary with filenames only, chronological order for legend
files = {
    "Battery B1": "batb1.csv",
    "Battery B2": "batb2.csv",
    "Battery B3": "batb3.csv",
    "Battery B4": "batb4.csv"
}

# Load data
data = {}
for label, filename in files.items():
    full_path = os.path.join(base_dir, filename)
    df = pd.read_csv(full_path)
    data[label] = df

# Font sizes
label_fontsize = 22
title_fontsize = 16
tick_fontsize = 18
legend_fontsize = 18

# Styles for batteries except B1 (we'll treat B1 separately)
styles_others = ['-', '-', '-']
battery_order = ["Battery B1", "Battery B2", "Battery B3", "Battery B4"]

def plot_with_b1_on_top(y_col, ylabel, title, convert_kw=False, figsize=(10,6)):
    plt.figure(figsize=figsize)
    
    # Plot other batteries first
    others = [b for b in battery_order if b != "Battery B1"]
    for label, style in zip(others, styles_others):
        ydata = data[label][y_col]
        if convert_kw:
            ydata = ydata / 1000  # convert W to kW if needed
        plt.plot(ydata, style, label=label, linewidth=2)
    
    # Plot Battery B1 last, thick line, solid with circles
    ydata_b1 = data["Battery B1"][y_col]
    if convert_kw:
        ydata_b1 = ydata_b1 / 1000
    plt.plot(ydata_b1, '-.', label="Battery B1", linewidth=3, zorder=10)
    
    plt.title(title, fontsize=title_fontsize)
    plt.xlabel('Time Step', fontsize=label_fontsize)
    plt.ylabel(ylabel, fontsize=label_fontsize)
    
    # Fix legend order: Battery B1 first, then others in order
    handles, labels = plt.gca().get_legend_handles_labels()
    label_handle_map = dict(zip(labels, handles))
    desired_order = battery_order
    ordered_handles = [label_handle_map[label] for label in desired_order]
    plt.legend(ordered_handles, desired_order, fontsize=legend_fontsize)
    
    plt.grid(True)
    plt.tick_params(axis='both', which='major', labelsize=tick_fontsize)
    plt.tight_layout()
    plt.show()


# Plot SOC_batt
plot_with_b1_on_top(
    y_col='SOC_batt',
    ylabel='Battery SOC',
    title='SOC change over Time',
    convert_kw=False,
    figsize=(10,6)
)

# Plot p_batt_charge (in kW)
plot_with_b1_on_top(
    y_col='p_batt_charge',
    ylabel='Charge Power [kW]',
    title='Battery Charge Power over Time',
    convert_kw=True,
    figsize=(15,3)
)

# Plot p_batt_discharge (in kW)
plot_with_b1_on_top(
    y_col='p_batt_discharge',
    ylabel='Discharge Power [kW]',
    title='Battery Discharge Power over Time',
    convert_kw=True,
    figsize=(15,3)
)
