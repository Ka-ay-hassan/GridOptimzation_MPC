import os
from typing import Literal, Any, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from datetime import datetime

from numpy import ndarray, dtype

from components.prosumer.prosumer import Prosumer
from config.config import PROJ_PATH

from utilities.simulation_period import SimulationPeriod

from components.prosumer.heat_pump.heat_pump import HeatPump



class LargeScaleHeatPump(HeatPump):
    def __init__(self, simulation_period: SimulationPeriod, power_nom_kw: float, temperature_celsius: float, tes=False):
        super().__init__(simulation_period, "Large-Scale HT", power_nom_kw, temperature_celsius, tes, init_coeffs=False)

    def calculate_cop_thermal(self, t_source: float, method: Optional[str] = None) -> None:
        """Calculate the Coefficient of Performance (COP) for a large-scale heat pump."""
        a = 40.789
        b = 1.0305
        c = -1.0489
        d = 0.29998
        delta_T_lift = self.temperature_celsius - t_source
        self.cop_thermal = a * ((delta_T_lift + 2 * b) ** c) * ((self.temperature_celsius + b) ** d)

    def start_up(self, current_step: int) -> tuple[float | Any, float | int | Any, float | Any]:
        """
        Simulates the start-up behavior of the heat pump.

        Args:
            current_step (int): The current time step of the simulation.

        Returns:
            p_heat (float): The heat power produced by the heat pump during start-up.
            p_el (float): The electric power consumed by the heat pump during start-up.
            p_heat_ratio (float): The ratio of the current heat power to the maximum heat power.
        """
        p_heat_max = self.cop * self.p_el_set
        dt = self.dt
        dt_start_up = 900  # 15 minutes in seconds
        ramp_up_ratio = min(current_step * dt / dt_start_up, 1.0)
        p_heat = ramp_up_ratio * p_heat_max
        p_el = ramp_up_ratio * self.p_el_set
        p_heat_ratio = ramp_up_ratio
        self.startup_counter += 1
        return p_heat, p_el, p_heat_ratio

    def propagate(self, t_source: float, timestamp: datetime) -> None:
        if self.p_el_history[-1] == 0 and self.p_el > 0:
            self.start = True
        plf = self.calculate_partial_load_factor
        self.calculate_cop_thermal(t_source)
        self.cop = plf * self.cop_thermal
        self.p_thermal = self.cop * self.p_el
        if self.start:
            p_heat_start, p_el_start_up, p_heat_ratio = self.start_up(self.startup_counter)
            self.p_thermal = p_heat_start
            self._p_el = p_el_start_up
            self.p_el_history.append(p_el_start_up)
            if p_heat_ratio == 1:
                self.start = False
        else:
            self.startup_counter = 0
            self.p_el_history.append(self.p_el)
        if self.p_el == 0:
            self.shutdown_counter += 1
            self.shutdown_time = self.shutdown_counter * self.dt
            self.start = False
        elif self.p_el > 0:
            self.shutdown_time = 0
            self.shutdown_counter = 0




def test_large_scale_heat_pump_propagate():
    from datetime import timedelta
    # Create a LargeScaleHeatPump object
    simulation_period = SimulationPeriod(
        start=datetime(2022, 1, 1),
        end=datetime(2022, 1, 5),
        resolution=timedelta(minutes=1)
    )
    hp = LargeScaleHeatPump(simulation_period, power_nom_kw=100.0, temperature_celsius=60.0)

    # Initialize lists to store the thermal power, electric power, COP, PLF, and thermal COP at each time step
    P_thermal_history = []
    P_el_history = []
    cop_history = []
    plf_history = []
    mass_flow_list = []
    cop_thermal_history = []
    # Initialize a list to store the source temperature at each time step
    t_source_history = []

    # Define the on and off periods for the heat pump (in minutes)
    on_period = 60  # The heat pump will be on for 60 minutes
    off_period = 60  # The heat pump will be off for 60 minutes

    # Initialize a counter for the current period
    period_counter = 0

    # Define parameters for the sinusoidal temperature curve
    amplitude = 10  # Temperature variation amplitude
    period = 24 * 60  # Temperature variation period (in minutes)
    phase = 0  # Phase shift
    mean_temp = 10  # Mean temperature

    # Loop over a certain number of time steps
    for i, timestamp in enumerate(simulation_period):
        # Determine the current period (on or off)
        if period_counter < on_period:
            hp.p_el = 50.0  # The heat pump is on
        else:
            hp.p_el = 0  # The heat pump is off

        # Update the period counter
        period_counter += 1
        if period_counter >= on_period + off_period:
            period_counter = 0  # Reset the counter

        # Calculate the source temperature as a sinusoidal function of time
        t_source = amplitude * np.sin(2 * np.pi * (i / period - phase)) + mean_temp

        # Record the source temperature
        t_source_history.append(t_source)

        # Propagate the heat pump
        hp.propagate(t_source, timestamp)
        mass_flow = hp.calculate_mass_flow_rate

        # Store the thermal power, electric power, COP, PLF, and thermal COP at this time step
        P_thermal_history.append(hp.p_thermal)
        P_el_history.append(hp.p_el)
        cop_history.append(hp.cop)
        plf_history.append(hp.calculate_partial_load_factor)
        cop_thermal_history.append(hp.cop_thermal)
        mass_flow_list.append(mass_flow)

    # Calculate the time steps in seconds
    time_steps = np.arange(len(simulation_period)) * hp.dt

    # Plot the thermal power, electric power, COP, PLF, and thermal COP history
    plt.figure(figsize=(12, 12))

    plt.subplot(5, 1, 1)
    plt.plot(time_steps, P_thermal_history, label='Thermal power (kW)')
    plt.plot(time_steps, P_el_history, label='Electric power (kW)')
    plt.ylabel('Power (kW)')
    plt.legend()

    plt.subplot(5, 1, 2)
    plt.plot(time_steps, cop_history, label='COP', color='green')
    plt.ylabel('COP')
    plt.legend()

    plt.subplot(5, 1, 3)
    plt.plot(time_steps, plf_history, label='PLF', color='blue')
    plt.plot(time_steps, cop_thermal_history, label='COP Thermal', color='red')
    plt.xlabel('Time step (s)')
    plt.ylabel('PLF / COP Thermal')
    plt.legend()

    plt.subplot(5, 1, 4)
    plt.plot(time_steps, mass_flow_list, label='mass flow', color='purple')
    plt.ylabel('mass flow rate')
    plt.legend()

    plt.subplot(5, 1, 5)
    plt.plot(t_source_history, cop_history, label='COP vs Source Temp', color='orange')
    plt.xlabel('Source Temperature (°C)')
    plt.ylabel('COP')
    plt.legend()

    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    # Run the test function
    test_large_scale_heat_pump_propagate()

