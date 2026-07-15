import numpy as np
import matplotlib.pyplot as plt
from heat_pump import HeatPump
from utilities.simulation_period import SimulationPeriod
from datetime import timedelta
from datetime import datetime
from sklearn.linear_model import LinearRegression

# Define the heat pump model
# Create a HeatPump object
simulation_period = SimulationPeriod(
    start=datetime(2022, 1, 1),
    end=datetime(2022, 1, 5),
    resolution=timedelta(minutes=1)
)
hp = HeatPump(simulation_period, 'Outdoor Air/Water_Regulated', 7, 35.1)


# Simulate the heat pump operation under different conditions
p_el_values = np.linspace(0, 7, 100)  # Electric power input values
t_source_values = np.linspace(-10, 20, 100)  # Source temperature values

p_thermal_values = []
for p_el in p_el_values:
    for t_source in t_source_values:
        p_thermal = hp.propagate(p_el, t_source)
        p_thermal_values.append(p_thermal)

# Prepare the data for regression
X = np.array(list(zip(p_el_values, t_source_values)))  # Input features: electric power and source temperature
y = np.array(p_thermal_values)  # Target variable: thermal power

# Create a linear regression model
model = LinearRegression()

# Train the model
model.fit(X, y)

# Print the coefficients of the linear regression model
print("Coefficients: ", model.coef_)
print("Intercept: ", model.intercept_)
