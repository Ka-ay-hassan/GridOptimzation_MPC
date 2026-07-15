#!/usr/bin/env python

"""Simulation Model of a heat pump."""

from __future__ import annotations

__author__ = "Abdul Azzam"
__copyright__ = "Copyright (C) 2023 Abdul Azzam"
__license__ = "GPL"
__version__ = "1.0"


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

heat_pump_types = Literal[
    "Outdoor Air/Water_Regulated",
    "Outdoor Air/Water_On-Off",
    "Brine/Water_Regulated",
    "Water/Water_On-Off",
    "Brine/Water and Water/Water_Regulated",
    "Water/Water_Regulated",
    "Brine/Water and Water/Water_On-Off",
    "Brine/Water_On-Off",
    "Large-Scale HT"
]

# todo: RL-temp according to EN 14825 normally 5K lower -> spread of 5K

class HeatPump(Prosumer):
    """A class to simulate an Air Source or Ground Source Heat Pump.

    Attributes:
        hp_type (str): Type of heat pump ('air-source', 'ground-source').
        power_nom_kw (float): Rated electrical power of the heat pump.
        tes (bool): Whether the heat pump is connected to a thermal energy storage (TES) system.
        temp (float): Reference sink temperature.
    """

    def __init__(self, simulation_period: SimulationPeriod, heat_pump_type: str, power_nom_kw: float,
                 temperature_celsius: float, tes=False, init_coeffs=True):
        """Initialize the HeatPump object."""
        super().__init__(self.__class__.__name__)
        self.simulation_period = simulation_period
        self.heat_pump_type = heat_pump_type
        self.power_nom_kw = power_nom_kw
        self.p_el = 0
        self.p_el_set = 0
        self.tes = tes
        self.dt = self.simulation_period.resolution_seconds
        self.temperature_celsius = temperature_celsius
        self.temperature_difference = 0
        self.cop = 1.
        self.cop_thermal = 2
        self.p_thermal = 0.
        self.start = False
        self.startup_counter = 0
        self.shutdown_counter = 0
        self.shutdown_time = 0
        self.p_el_history = [0]
        # Define the low and high supply temperatures
        self.temp_low = 30.
        self.temp_high = 55.

        # Data directory
        data_path = PROJ_PATH / "data" / "heat_pump"

        if init_coeffs:
            self._init_coeffs(data_path)
            # Interpolate the coefficients if the temperature is between the low and high supply temperatures
            self.set_temperature(temperature_celsius)

        # Specific Heat of Water in [kJ/kg.K] (from 30° - 50°C)
        self.cp_water = 4.174

        self.coeffs_plf = pd.read_csv(data_path / "quadratic_coeffs_plf.csv").values

        self.component_type = 'converter'

    def _init_coeffs(self, data_path):
        self.coeffs_linear_low = pd.read_csv(data_path / "linear_coeffs_low.csv", index_col=0).loc[
            self.heat_pump_type].values
        self.coeffs_linear_high = pd.read_csv(data_path / "linear_coeffs_high.csv", index_col=0).loc[
            self.heat_pump_type].values
        self.coeffs_cubic_low = pd.read_csv(data_path / "cubic_coeffs_low.csv", index_col=0).loc[
            self.heat_pump_type].values
        self.coeffs_cubic_high = pd.read_csv(data_path / "cubic_coeffs_high.csv", index_col=0).loc[
            self.heat_pump_type].values

        df_start = pd.read_csv(os.path.join(data_path, "start_up.csv"))
        self.df_start_el = df_start["Compressor el.Power [P/P_max] ts = 30s"].tolist()
        self.df_start_heat = df_start["Heating Power [P/P_max] ts = 30s"].tolist()

    def set_temperature(self, temp: float) -> None:
        """Set the supply temperature and update the coefficients."""
        self.temp = temp

        # Interpolate the coefficients if the temperature is between the low and high supply temperatures
        if self.temp_low < temp < self.temp_high:
            self.coeffs_linear = self.interpolate_coeffs(self.temp_low, self.coeffs_linear_low, self.temp_high,
                                                         self.coeffs_linear_high, temp)
            self.coeffs_cubic = self.interpolate_coeffs(self.temp_low, self.coeffs_cubic_low, self.temp_high,
                                                        self.coeffs_cubic_high, temp)
        # Extrapolate the coefficients if the temperature is below the low supply temperature
        elif temp < self.temp_low:
            self.coeffs_linear = self.extrapolate_coeffs(self.temp_low, self.coeffs_linear_low, self.temp_high,
                                                         self.coeffs_linear_high, temp)
            self.coeffs_cubic = self.extrapolate_coeffs(self.temp_low, self.coeffs_cubic_low, self.temp_high,
                                                        self.coeffs_cubic_high, temp)
        # Extrapolate the coefficients if the temperature is above the high supply temperature
        elif temp > self.temp_high:
            self.coeffs_linear = self.extrapolate_coeffs(self.temp_low, self.coeffs_linear_low, self.temp_high,
                                                         self.coeffs_linear_high, temp)
            self.coeffs_cubic = self.extrapolate_coeffs(self.temp_low, self.coeffs_cubic_low, self.temp_high,
                                                        self.coeffs_cubic_high, temp)
        elif temp == self.temp_low:
            self.coeffs_linear = self.coeffs_linear_low
            self.coeffs_cubic = self.coeffs_cubic_low

        elif temp == self.temp_high:
            self.coeffs_linear = self.coeffs_linear_high
            self.coeffs_cubic = self.coeffs_cubic_high

    def power_kw(self, timestamp: datetime) -> float:
        pass

    def interpolate_coeffs(self, temp_low, coeffs_low, temp_high, coeffs_high, temp):
        """Interpolate between two sets of coefficients."""
        return coeffs_low + (coeffs_high - coeffs_low) * ((temp - temp_low) / (temp_high - temp_low))

    def extrapolate_coeffs(self, temp_low, coeffs_low, temp_high, coeffs_high, temp):
        """Extrapolate between two sets of coefficients."""
        if temp < temp_low:
            return coeffs_low + (coeffs_low - coeffs_high) * ((temp_low - temp) / (temp_high - temp_low))
        elif temp > temp_high:
            return coeffs_high + (coeffs_high - coeffs_low) * ((temp - temp_high) / (temp_high - temp_low))
        else:
            raise ValueError("Temperature is within the interpolation range. Use interpolate_coeffs instead.")

    @property
    def p_el(self):
        return self._p_el

    @p_el.setter
    def p_el(self, value):
        self._p_el = value
        self.p_el_set = value

    @staticmethod
    def calculate_epsilon(t_sink, t_source, kelvin=273.15):
        """Calculate the Carnot efficiency (epsilon) for a heat pump."""
        return (t_sink + kelvin) / ((t_sink + kelvin) - (t_source + kelvin))

    def calculate_cop_reference(self, coeff: ndarray, t_source: float):
        """Calculate the Coefficient of Performance (COP) of the heat pump."""
        return np.polyval(coeff, t_source)

    def calculate_cop_thermal(self, t_source: float, method: Optional[str] = None) -> None:
        """Calculate the Coefficient of Performance (COP) of a heat pump under
        different source and sink temperatures."""
        if method == "carnot":
            epsilon = self.calculate_epsilon(t_source, self.temp)
            epsilon_ref = self.calculate_epsilon(t_source, self.temp)
            cop_ref = self.calculate_cop_reference(self.coeffs_low, t_source)
            self.cop_thermal = cop_ref * epsilon / epsilon_ref
        elif method == "curves":
            if t_source < -7:
                self.cop_thermal = self.calculate_cop_reference(self.coeffs_linear, t_source)
            elif t_source > 12:
                self.cop_thermal = self.calculate_cop_reference(self.coeffs_linear, t_source)
            else:
                self.cop_thermal = self.calculate_cop_reference(self.coeffs_cubic, t_source)
        else:
            raise NotImplementedError("The provided method is not supported.")

    @property
    def calculate_partial_load_factor(self) -> float:
        """
        Calculates the partial load factor of the heat pump.

        The partial load factor is calculated as the ratio of the set electrical power to the rated electrical power.

        Returns:
        float: The partial load factor.
        """

        # Check if the electrical power has been set
        if hasattr(self, 'p_el'):
            # Calculate the partial load factor
            plr = self.p_el / self.power_nom_kw
            if plr > 1:
                plr = 1
            plf = float(np.polyval(self.coeffs_plf, plr))
        else:
            raise ValueError("Electrical power has not been set. Please use the set_electric_power method to set it.")

        return plf

    @property
    def calculate_mass_flow_rate(self) -> float:
        """Calculate the mass flow rate based on the power and temperature difference."""
        self.temperature_difference = self.temperature_celsius - self.temp_low
        if self.temperature_difference != 0:
            mass_flow_rate = self.p_thermal / (self.cp_water * self.temperature_difference)
        else:
            raise ValueError("Temperature difference must not be zero.")
        return mass_flow_rate

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
        # Calculate the maximum heat power
        p_heat_max = self.cop * self.p_el_set

        # Define the time step sizes
        dt = self.dt
        dt_start_up = 30

        # Calculate the step size for the start-up process
        len_ts = len(self.df_start_heat)
        d_step_startup = max(1, np.ceil(dt / dt_start_up))
        step = d_step_startup * current_step
        step = int(min(step, len_ts - 1))

        # Calculate the ratios of the current heat and electric power to the maximum power
        p_heat_ratio = self.df_start_heat[step] / 100
        p_el_ratio = self.df_start_el[step] / 100

        # Calculate the current heat and electric power
        p_heat = p_heat_ratio * p_heat_max
        p_el = p_el_ratio * self.p_el_set

        # Increment the start-up counter
        self.startup_counter += 1

        return p_heat, p_el, p_heat_ratio

    def propagate(self, t_source: float, timestamp: datetime) -> None:
        """
        Simulates the operation of the heat pump over a time step.

        Args:
            t_source (float): The source temperature.

        Returns:
            self: The HeatPump object after propagation.
        """
        # Check if the Heat Pump is starting up or already in operation
        # If the last electric power in history is 0 and the current electric power is greater than 0, set start to True
        if self.p_el_history[-1] == 0 and self.p_el > 0:
            self.start = True

        # Calculate the partial load factor (PLF) and the thermal coefficient of performance (COP)
        # Then calculate the resulting COP by multiplying the PLF and the thermal COP
        plf = self.calculate_partial_load_factor
        self.calculate_cop_thermal(t_source, method="curves")
        self.cop = plf * self.cop_thermal

        # Calculate the Thermal Power by multiplying the COP and the electric power
        self.p_thermal = self.cop * self.p_el

        # If the heat pump is starting up, calculate the start-up behavior
        if self.start:
            p_heat_start, p_el_start_up, p_heat_ratio = self.start_up(self.startup_counter)
            self.p_thermal = p_heat_start
            self._p_el = p_el_start_up
            self.p_el_history.append(p_el_start_up)
            # If the heat power ratio is 1, the heat pump has reached its maximum power and
            # the start-up process is complete
            if p_heat_ratio == 1:
                self.start = False
        else:
            # If the heat pump is not starting up, reset the start-up counter and append the
            # current electric power to the history
            self.startup_counter = 0
            self.p_el_history.append(self.p_el)

        # If the electric power is 0, increment the shutdown counter and calculate the shutdown time
        # Set start to False as the heat pump is not operating
        if self.p_el == 0:
            self.shutdown_counter += 1
            self.shutdown_time = self.shutdown_counter * self.dt
            self.start = False
        # If the electric power is greater than 0, reset the shutdown counter and the shutdown time
        elif self.p_el > 0:
            self.shutdown_time = 0
            self.shutdown_counter = 0


def test_propagate():
    from datetime import timedelta
    # Create a HeatPump object
    simulation_period = SimulationPeriod(
        start=datetime(2022, 1, 1),
        end=datetime(2022, 1, 5),
        resolution=timedelta(minutes=1)
    )
    hp = HeatPump(simulation_period, 'Outdoor Air/Water_Regulated', 7, 35.1)

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
            hp.p_el = 7  # The heat pump is on
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
    time_steps = np.arange(5761) * hp.dt

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


if __name__ == '__main__':
    test_propagate()
