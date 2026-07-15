import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the path to the other repository
sys.path.append('/home/abu/PycharmProjects/DiTEnS/DistrictGenerator')

from components.storages.energetic.electrical.battery import BatterySystem
from components.prosumer.pv import PV
from components.controller.ems import EnergyManagementSystem
from utilities.simulation_period import SimulationPeriod
from config.config import PROJ_PATH

class BatteryPVSimulation:
    """
    Class for simulating the interaction between a battery storage system and a photovoltaic (PV) system
    within an electric hub.

    This class initializes and manages the components of the simulation, including the battery and PV system, and
    handles the propagation of the simulation over a specified period. It also includes methods for controlling
    the battery based on power demand and state of charge (SOC), updating the energy data,
    and saving the results to a CSV file.

    Attributes:
        simulation_period (SimulationPeriod): The period over which the simulation runs.
        battery (BatterySystem): The battery storage system used in the simulation.
        pv_system (PV): The photovoltaic system used in the simulation.
        timestamp (datetime): The current timestamp in the simulation.
        electric_hub (EnergyManagementSystem): The energy management system managing the electric hub.
        pv_power (float): The current power output of the PV system.
        data (dict): A dictionary to store the simulation data.
        electric_hub_df (pd.DataFrame): DataFrame to store the state of the electric hub.
        index (int): The current index of the simulation steps.
        external_controller (optional): An external controller for managing the battery.
        demand_data (pd.DataFrame): DataFrame containing the power demand data.
    """

    def __init__(self, simulation_period=None, external_controller=None):
        self.simulation_period = simulation_period
        self.battery = None
        self.pv_system = None
        self.timestamp = None
        self.electric_hub = EnergyManagementSystem(slack_device="pcc")
        self.pv_power = 0
        self.data = {}
        self.init_components()
        self.electric_hub_df = pd.DataFrame()
        self.index = 0
        self.external_controller = external_controller
        # Load demand data and ensure timestamps are properly formatted
        self.demand_data = pd.read_csv(
            'data/demand_data/interpolated_power_500s.csv',
            parse_dates=['timestamp'],
            index_col='timestamp'
        )
        self.demand_data = self.demand_data.resample(f'{int(delta.total_seconds())}S').interpolate()

    def init_components(self):
        """Initialize the simulation with all necessary components"""
        self.battery = BatterySystem(capacity_nom_kwh=2000, power_nom_kw=500, simulation_period=self.simulation_period)
        data_path = PROJ_PATH / "data" / "building"
        epw_file = os.path.join(data_path, "DEU_Stuttgart.107380_IWEC.epw")  # replace with your actual file path
        self.pv_system = PV(self.simulation_period, area_m2=1000000*0.25, angle_deg=30, orientation_deg=180, epw_file=epw_file)
        self.components = [self.battery, self.pv_system]
        self.control_dict = {component.__class__.__name__: None for component in self.components}

    def propagate(self, timestamp, demand: float) -> None:
        """Propagate the simulation of all components"""
        self.timestamp = timestamp  # Update the current timestamp
        # Calculate all loads
        self.pv_power = self.pv_system.power_kw(self.timestamp)
        self.electric_hub.set_power("PV", [self.pv_power, 0])
        self.electric_hub.set_power("el_load", [0, demand])
        self.battery_controller()
        self.propagate_components()
        # Save the current state of the hubs
        self.electric_hub_df = self.electric_hub.get_DataFrame()
        # Update the energy_dict
        self.update_energy_dict()
        # Increment the index
        self.index += 1

    def battery_controller(self):
        """Controls the operation of the battery based on the state of charge (SOC) and power demand"""
        # Calculate the sum of power in the electric hub
        electric_hub_power_sum = self.electric_hub.get_sum("ppc")

        if self.external_controller:
            setpoint = self.external_controller.calculate_setpoint(electric_hub_power_sum, self.battery.soc)
        else:
        # If the power sum is positive, there is excess power, so charge the battery if it's not already fully charged
            if electric_hub_power_sum > 0 and not self.battery.soc > 0.95:
                setpoint = electric_hub_power_sum
            # If the power sum is negative, there is a power deficit, so discharge the battery if it's not already fully discharged
            elif electric_hub_power_sum < 0 and not self.battery.soc < 0.2:
                setpoint = electric_hub_power_sum
            else:
                setpoint = 0

        self.electric_hub.set_setpoint('battery', {'el_power': setpoint})

    def propagate_components(self):
        """Propagate the components with the setpoints from the ems system and then set the values of the components into the electric hub."""
        # Get the setpoints for the battery from the electric hub
        battery_setpoint = self.electric_hub.power_dict_kw['battery']['setpoint']['el_power']
        # Propagate the battery with the setpoint and get the results
        batt_power = self.battery.set_power_kw(battery_setpoint, self.timestamp)
        self.electric_hub.set_power("battery", [batt_power, 0])

    def update_energy_dict(self):
        """Update the energy_dict with the current values of SOC, PV power, demand, battery power, and hub net power."""
        # Initialize the lists if they don't exist
        if not self.data:
            self.data = {
                'battery_soc': [],
                'pv_power': [],
                'demand': [],
                'batt_power': [],
                'hub_net_power': []
            }
        # Append the current values to the lists
        self.data['battery_soc'].append(self.battery.soc)
        self.data['pv_power'].append(self.pv_power)
        self.data['demand'].append(self.demand_data.loc[self.timestamp, 'aggregated_power']*1e3)
        self.data['batt_power'].append(self.electric_hub.get_setpoint('battery', 'el_power'))
        self.data['hub_net_power'].append(self.electric_hub.get_sum('ppc'))

class BatteryPVSimulationTest:
    def __init__(self, start_date: datetime, end_date: datetime, delta: timedelta):
        self.sim = BatteryPVSimulation()
        self.simulation_period = SimulationPeriod(start_date, end_date, delta)

        # Load demand data
        self.demand_data = pd.read_csv(
            '/home/abu/PycharmProjects/tim_heating/HP_abu/HeatingSimulation/data/demand_data/interpolated_power_500s.csv',
            parse_dates=['timestamp'],
            index_col='timestamp'
        )

        # Convert index to the required datetime format
        self.demand_data.index = self.demand_data.index.map(
            lambda t: datetime(t.year, t.month, t.day, t.hour, t.minute, t.second))

    def run_test(self):
        """Run the simulation test for one week"""
        for timestamp in self.simulation_period:
            demand = self.demand_data.loc[timestamp, 'aggregated_power']*1e3
            self.sim.propagate(timestamp, demand)

        # Plot results
        self.plot_results()
        # Save PV generation to a CSV file
        self.save_pv_generation_to_csv()

    def plot_results(self):
        """Plot the power flows and SOC of the battery"""
        data = self.sim.data
        timestamps = [timestamp for timestamp in self.simulation_period]

        fig, axs = plt.subplots(5, figsize=(12, 8), sharex=True)

        # Plot battery SOC
        axs[0].plot(timestamps, data['battery_soc'], label='Battery SOC')
        axs[0].set_ylabel('State of Charge (SOC)')
        axs[0].legend()
        axs[0].grid(True)

        # Plot PV power
        axs[1].plot(timestamps, data['pv_power'], label='PV Power')
        axs[1].set_ylabel('PV Power (kW)')
        axs[1].legend()
        axs[1].grid(True)

        # Plot Demand
        axs[2].plot(timestamps, data['demand'], label='Demand')
        axs[2].set_ylabel('Demand Power (kW)')
        axs[2].legend()
        axs[2].grid(True)

        # Plot PV power
        axs[3].plot(timestamps, data['batt_power'], label='Batt Power')
        axs[3].set_ylabel('Batt Power (kW)')
        axs[3].legend()
        axs[3].grid(True)

        # Plot Demand
        axs[4].plot(timestamps, data['hub_net_power'], label='Net Power')
        axs[4].set_ylabel('Hub Net Power (kW)')
        axs[4].legend()
        axs[4].grid(True)

        plt.xlabel('Time')
        plt.show()

    def save_pv_generation_to_csv(self, file_path="mpc_el_data.csv"):
        """Save all the data in the data dictionary to a CSV file"""
        data = self.sim.data
        timestamps = [timestamp for timestamp in self.simulation_period]

        df = pd.DataFrame({
            'timestamp': timestamps,
            'battery_soc': data['battery_soc'],
            'pv_power': data['pv_power'],
            'demand': data['demand'],
            'batt_power': data['batt_power'],
            'hub_net_power': data['hub_net_power']
        })

        df.to_csv(file_path, index=False)
        print(f"All simulation data saved to {file_path}")


# Define simulation period for one week
start_date = datetime(2023, 4, 1)
end_date = datetime(2023, 5, 1)
delta = timedelta(minutes=5)

# Create and run the test
test = BatteryPVSimulationTest(start_date, end_date, delta)
test.run_test()
