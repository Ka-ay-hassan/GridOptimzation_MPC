#!/usr/bin/env python

"""Simulation Model of a heat pump."""

__author__ = "Abdul Azzam"
__copyright__ = "Copyright (C) 2023 Abdul Azzam"
__license__ = "GPL"
__version__ = "0.1"

import numpy as np
import matplotlib.pyplot as plt
from components.prosumer.heat_pump.heat_pump import HeatPump

def test_propagate():
    # Create a HeatPump object
    hp = HeatPump('Outdoor Air/Water_Regulated', 7, 45, dt=30)

    # Set the electric power
    hp.set_electric_power(7)

    # Define the source temperature for the tests
    t_source = 2

    # Initialize lists to store the thermal power, electric power, COP, PLF, and thermal COP at each time step
    P_thermal_history = []
    P_el_history = []
    cop_history = []
    plf_history = []
    cop_thermal_history = []

    # Loop over a certain number of time steps
    for _ in range(30):
        # Propagate the heat pump
        hp.propagate(t_source)

        # Print the current state of the heat pump
        print(f"Source temperature: {t_source}°C")
        print(f"COP: {hp.cop}")
        print(f"Thermal power: {hp.p_thermal} kW")
        print(f"Electric power: {hp.p_el} kW")
        print()

        # Store the thermal power, electric power, COP, PLF, and thermal COP at this time step
        P_thermal_history.append(hp.p_thermal)
        P_el_history.append(hp.p_el)
        cop_history.append(hp.cop)
        plf_history.append(hp.calculate_partial_load_factor())
        cop_thermal_history.append(hp.calculate_cop_thermal(t_source, method="curves"))

    # Calculate the time steps in seconds
    time_steps = np.arange(30) * hp.dt

    # Plot the thermal power, electric power, COP, PLF, and thermal COP history
    plt.figure(figsize=(12, 10))

    plt.subplot(3, 1, 1)
    plt.plot(time_steps, P_thermal_history, label='Thermal power (kW)')
    plt.plot(time_steps, P_el_history, label='Electric power (kW)')
    plt.ylabel('Power (kW)')
    plt.legend()

    plt.subplot(3, 1, 2)
    plt.plot(time_steps, cop_history, label='COP', color='green')
    plt.ylabel('COP')
    plt.legend()

    plt.subplot(3, 1, 3)
    plt.plot(time_steps, plf_history, label='PLF', color='blue')
    plt.plot(time_steps, cop_thermal_history, label='COP Thermal', color='red')
    plt.xlabel('Time step (s)')
    plt.ylabel('PLF / COP Thermal')
    plt.legend()

    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    test_propagate()