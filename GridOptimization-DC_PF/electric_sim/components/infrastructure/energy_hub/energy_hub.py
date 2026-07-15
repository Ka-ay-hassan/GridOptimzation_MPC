from __future__ import annotations
from typing import List, Literal, Generator, Any

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import logging

from datetime import time

from components.controller.ems import EnergyManagementSystem
from components.infrastructure.energy_node.energy_node import EnergyNode
from components.infrastructure.buildings.building import Building
from components.prosumer.heat_pump.heat_pump import HeatPump
from components.prosumer.electrical_load import ElectricalLoad
from components.prosumer.dwh_load import DHWLoad
from components.storages.energetic.thermal.thermal_storage import HotWaterTank
from components.storages.energetic.electrical.battery import BatterySystem
from components.prosumer.pv import PV

from datetime import datetime
from components.controller.Controller import PIDController, BangBangTankElectric, BangBangController

logging.basicConfig(level=logging.INFO)


# TODO: use EMS to get electrical and thermal power values maybe also measurements -> connection to el./th. grid
# TODO: adjust controller and config
# TODO: think about using just one node instead of a node list (how to init many nodes in one hub? is it necessary?)
# TODO: how to handle DHW load? extra tank or durchlauferhitzer??
class EnergyHub:
    """
    Initialize the EnergyHub.

    Args:
        id (int): Unique identifier for the EnergyHub.
        nodes (List[EnergyNode]): List of EnergyNode instances associated with the hub.
        thermal_slack_device (str): Device that balances thermal power in the system.
        electrical_slack_device (str): Device that balances electrical power in the system.
    """

    def __init__(self, id: int, nodes: List[EnergyNode], thermal_slack_device: str, electrical_slack_device: str):
        self.id = id
        self.nodes = nodes
        self.pid_controller = PIDController(p=0.5, i=0.05, d=0.01, dt=60)
        self.control_action = 0.0
        self.thermal_hub = EnergyManagementSystem(slack_device=thermal_slack_device)
        self.electric_hub = EnergyManagementSystem(slack_device=electrical_slack_device)
        self.energy_dict = {}  # Initialize the energy_dict

        self.index = 0
        self.timestamp_iterator = iter(self.nodes[0].simulation_period) if self.nodes else None
        self.P_zone_heating = 0

        self.energy_dict = {
            'tank_soc': [],
            'battery_soc': [],
            'el_load_power': [],
            'dhw_load_power': [],
            'building_temp': [],
            'outdoor_temp': [],
            'hp_cop': [],
            'hp_thermal_power': [],
            'hp_electrical_power': [],
            'pv_power': [],
            'P_zone_heating': [],
            'sh_in': [],
            'sh_out': [],
            'dhw_in': [],
            'dhw_out': [],
            'hp_in': [],
            'hp_out': []
        }
        # Add entries for layer temperatures
        for i in range(4):  # Assuming there are 4 layers
            self.energy_dict[f'layer_{i + 1}_temp'] = []

    def update_energy_dict(self):
        """
        Update the energy_dict with the current values of soc, el load, and temperatures.
        """

        # Append the current values to the lists
        for node in self.nodes:
            for element in node.elements:
                if isinstance(element, HotWaterTank):
                    self.energy_dict['tank_soc'].append(element.SOC)
                    for i, layer in enumerate(element.layers):
                        self.energy_dict[f'layer_{i + 1}_temp'].append(layer.T)
                if isinstance(element, BatterySystem):
                    self.energy_dict['battery_soc'].append(element.soc)
                if isinstance(element, ElectricalLoad):
                    self.energy_dict['el_load_power'].append(element.power_kw(self.timestamp))
                if isinstance(element, DHWLoad):
                    self.energy_dict['dhw_load_power'].append(element.dhw_demand(self.timestamp) * 0.1)
                if isinstance(element, Building):
                    self.energy_dict['building_temp'].append(element.T_indoor)
                if isinstance(element, HeatPump):
                    self.energy_dict['hp_cop'].append(element.cop)
                    self.energy_dict['hp_thermal_power'].append(element.p_thermal)
                    self.energy_dict['hp_electrical_power'].append(element.p_el)
                if isinstance(element, PV):
                    self.energy_dict['pv_power'].append(element.power_kw(self.timestamp) * 1e-3)
                if isinstance(element, HotWaterTank):
                    self.energy_dict['sh_in'].append(element.connection_flows['sh_in'])
                    self.energy_dict['sh_out'].append(element.connection_flows['sh_out'])
                    self.energy_dict['dhw_in'].append(element.connection_flows['dhw_in'])
                    self.energy_dict['dhw_out'].append(element.connection_flows['dhw_out'])
                    self.energy_dict['hp_in'].append(element.connection_flows['hp_in'])
                    self.energy_dict['hp_out'].append(element.connection_flows['hp_out'])
        self.energy_dict['outdoor_temp'].append(self.t_outdoor_df.loc[self.timestamp])
        self.energy_dict['P_zone_heating'].append(self.P_zone_heating * 1e-3)

        # Upd

    @classmethod
    def from_config(cls, hub: dict, simulation_period: dict) -> 'EnergyHub':
        """
        Create an instance of EnergyHub from a configuration dictionary.

        Args:
            hub (dict): Configuration dictionary for the energy hub.
            simulation_period (dict): Configuration dictionary for the simulation period.

        Returns:
            EnergyHub: An instance of the EnergyHub class.
        """
        instance = cls(hub['id'], [], hub['thermal_slack_device'], hub['electrical_slack_device'])
        activation_fcn = instance.ep_building_callback  # Use the instance attribute
        nodes = [
            EnergyNode.from_config(id=hub['id'], simulation_period=simulation_period, elements=hub['elements'],
                                   activation_fcn=activation_fcn)]
        instance.nodes = nodes
        instance.timestamp_iterator = iter(
            instance.nodes[0].simulation_period)  # Initialize timestamp_iterator after nodes
        return instance

    # todo: integrate it into the from_config method with configuration in the json file
    def init_controller(self):
        """
        Initialize the controller for every component
        :return:
        """
        self.tank_controller = BangBangTankElectric(initial_state=0, P_el_max=7, SOC_min=0.2, SOC_max=0.4)
        self.heating_rod_controller = BangBangController(
                                                initial_state=0,
                                                Y_min=50,  # Lower threshold for the top layer temperature
                                                Y_max=65,  # Upper threshold for the top layer temperature
                                                U_min=0,
                                                U_max=3000  # Maximum power of the heating rod
                                            )

        self.t_in_controller = PIDController(p=5, i=0.1, d=0.001, dt=self.nodes[0].simulation_period.resolution_seconds,
                                             max_u=10e3, min_u=0.)

        self.t_outdoor_df = EnergyNode.weather_data.get("temp_air",
                                                        pd.DataFrame())  # Use get method to avoid NoneType error
        self.ghi_df = EnergyNode.weather_data.get("ghi", pd.DataFrame())

    def power_kw(self, timestamp: datetime, power_type: Literal["electrical", "thermal"]) -> float:
        return np.sum([
            element.power_kw(timestamp)
            for element in self.elements
            if element.power_type == power_type
        ])

    def main(self):
        """Main method to propagate the energy hub."""
        logging.info("Starting main propagation.")
        for node in self.nodes:
            for element in node.elements:
                if isinstance(element, Building):
                    element.propagate()
        logging.info("Finished main propagation.")

    def check_energy_balance(self):
        """
        Check the energy balance within the thermal and electrical hubs.
        """
        thermal_balance = self.thermal_hub.calculate_balance()
        electrical_balance = self.electric_hub.calculate_balance()

        print(f"Thermal Hub Balance: {thermal_balance}")
        print(f"Electrical Hub Balance: {electrical_balance}")

        # return thermal_balance, electrical_balance

    def allocate_demands_and_generation(self) -> None:
        for node in self.nodes:
            for element in node.elements:
                if isinstance(element, PV):
                    pv_power = element.power_kw(self.timestamp)
                    self.electric_hub.set_power("PV", [0, pv_power])
                if isinstance(element, ElectricalLoad):
                    el_load_power = element.power_kw(self.timestamp)
                    self.electric_hub.set_power("el_load", [el_load_power, 0])
                if isinstance(element, DHWLoad):
                    dhw_demand = element.dhw_demand(self.timestamp)
                    #todo: calculate power in J/s instead of liter -> temperature difference of HP
                    self.thermal_hub.set_power("hotwater", [dhw_demand, 0])

    def propagate_main(self) -> None:
        if self.index < len(self.nodes[0].simulation_period):

            self.timestamp = next(self.timestamp_iterator)

            self.allocate_demands_and_generation()

            self._propagate_controller()

            # Set heating power to zero during the night
            if self.is_night_time(self.timestamp):
                self.P_zone_heating = 0

            self.thermal_hub.set_power("house", [self.P_zone_heating, 0])

            self.propagate_elements()

            self.check_energy_balance()

            self.update_energy_dict()

            self.index += 1

    def propagate_elements(self) -> None:
        # todo: Alle wichtigen Parameter (T_out, etc.) sollten Klassenvariablen sein
        # Get the setpoints for the heat pump, tank, and battery from the electric hub
        heatpump_setpoint = self.electric_hub.power_dict_kw['heatpump']['setpoint']['el_power']
        # battery_setpoint = self.electric_hub.power_dict_kw['battery']['setpoint']['el_power']
        for node in self.nodes:
            for element in node.elements:
                if isinstance(element, HeatPump):
                    element.p_el = heatpump_setpoint
                    element.propagate(self.t_outdoor_df.loc[self.timestamp], self.timestamp)
                    print('P_zone_heating:', self.P_zone_heating)
                    print('P_thermal_hp:', element.p_thermal)
                    if self.P_zone_heating > 0:
                        mass_flow_rate = self.P_zone_heating*1e-3/(
                                element.cp_water * 22)
                    else:
                        mass_flow_rate = 0
                    hp_mass_flow_rate = element.calculate_mass_flow_rate
                    self.electric_hub.set_power("heatpump", [element.p_el, 0])
                    self.thermal_hub.set_power("heatpump", [0, element.p_thermal])
                if isinstance(element, HotWaterTank):
                    self.heating_rod_controller.propagate(Y=element.layers[-1].T)
                    element.heating_rods['hr_1'].P_th_set = self.heating_rod_controller.u

                    # Update the heating rod
                    element.heating_rods['hr_1'].update()

                    # Propagate the tank with the setpoint and get the results
                    element.connection_flows = {
                        'sh_in': mass_flow_rate,
                        'sh_out': -mass_flow_rate,
                        'dhw_in': 0,  #self.thermal_hub.get_power('hotwater')[0],
                        'dhw_out': 0,  # -self.thermal_hub.get_power('hotwater')[0],
                        'hp_in': hp_mass_flow_rate,
                        'hp_out': -hp_mass_flow_rate
                    }

                    element.connection_temps = {
                        'sh_in': 18,  # Temperature for space heating inflow
                        'sh_out': 40,  # Temperature for space heating outflow
                        'dhw_in': 18,  # Temperature for domestic hot water inflow
                        'dhw_out': element.layers[-1].T,  # Temperature for domestic hot water outflow
                        'hp_in': 40,  # Temperature for heat pump inflow
                        'hp_out': 30  # Temperature for heat pump outflow
                    }

                    print('Space Heating mass flow:', mass_flow_rate)
                    print('HP mass flow:', hp_mass_flow_rate)
                    element.propagate(self.timestamp)
                if isinstance(element, BatterySystem):
                    self.battery_controller(element)
                    battery_setpoint = self.electric_hub.power_dict_kw['battery']['setpoint']['el_power']
                    batt_power = element.set_power_kw(battery_setpoint, self.timestamp)
                    self.electric_hub.set_power("battery", [batt_power, 0])


    def iter_nodes(self, node_type: type[EnergyNode] = None) -> Generator[None | EnergyNode, Any, None]:
        if node_type is None:
            yield from self.nodes
        else:
            yield from (node for node in self.nodes if isinstance(node, node_type))

    def _propagate_controller(self):
        # todo: All measured values should be integrated into the energyhub dict for accesssing it easily
        for node in self.nodes:
            for element in node.elements:
                if isinstance(element, Building):
                    self.P_zone_heating = self.t_in_controller.update(21.0 - element.T_indoor, self.P_zone_heating)

                    element.actuator_value = self.P_zone_heating
                if isinstance(element, HotWaterTank):
                    self.tank_controller.propagate(SOC=element.SOC)
                    self.electric_hub.set_setpoint('heatpump', {'el_power': self.tank_controller.P_el})
                    print('Tank setpoint:', self.tank_controller.P_el)
                if isinstance(element, HeatPump):
                    P_thermal = self.tank_controller.P_el * element.cop_thermal
                    self.thermal_hub.set_setpoint('heatpump', {'thermal_power': P_thermal})


    def battery_controller(self, battery_class):
        """
        Controls the operation of the battery based on the state of charge (SOC), power demand, and the sum of power in the electric hub.
        """
        # Calculate the sum of power in the electric hub
        electric_hub_power_sum = self.electric_hub.get_sum("ppc")

        # If the power sum is positive, there is excess power, so charge the battery if it's not already fully charged
        if electric_hub_power_sum > 0 and not battery_class.soc > 0.95:
            setpoint = electric_hub_power_sum

        # If the power sum is negative, there is a power deficit, so discharge the battery if it's not already fully discharged
        elif electric_hub_power_sum < 0 and not battery_class.soc < 0.2:
            setpoint = electric_hub_power_sum
        # Otherwise, do nothing
        else:
            setpoint = 0
        self.electric_hub.set_setpoint('battery', {'el_power': setpoint})

    def ep_building_callback(self):
        """
        Callback function for simulating with Energyplus instance
        :return:
        """
        self.propagate_main()

    def is_night_time(self, timestamp: datetime) -> bool:
        """
        Check if the current time is between 22:00 and 06:00.
        """
        return time(22, 0) <= timestamp.time() or timestamp.time() < time(6, 0)

    def get_total_power(self, timestamp: datetime) -> float:
        return sum(element.power_kw(timestamp) for element in self.elements)

    def plot_energy_dict(self):
        """
        Plot the energy_dict with matplotlib using subplots.
        """
        fig, axs = plt.subplots(6, figsize=(16, 14))

        # Create a list of timestamps for the x-axis
        timestamps = [timestamp for timestamp in self.nodes[0].simulation_period]

        # Subplot for heat pump el power, thermal power and the cop
        axs[0].plot(timestamps, self.energy_dict['hp_thermal_power'], label='Heat Pump Thermal Power')
        axs[0].plot(timestamps, self.energy_dict['dhw_load_power'], label='DHW Demand')
        axs[0].plot(timestamps, self.energy_dict['P_zone_heating'], label='P Zone Heating')
        axs[0].set_xlabel('Time')
        axs[0].set_ylabel('Value')
        axs[0].set_title('Heat Pump Data', pad=20)  # Add pad parameter to adjust the space between title and plot
        axs[0].legend()
        axs[0].grid(True)

        # Subplot for electric demand, dhw demand, tank and battery soc and pv power
        axs[1].plot(timestamps, self.energy_dict['el_load_power'], label='Electric Demand')
        axs[1].plot(timestamps, self.energy_dict['pv_power'], label='PV Power')
        axs[1].plot(timestamps, self.energy_dict['hp_electrical_power'], label='Heat Pump El Power')
        axs[1].set_xlabel('Time')
        axs[1].set_ylabel('Value')
        axs[1].set_title('Electric Demand, DHW Demand and PV Power Data',
                         pad=20)  # Add pad parameter to adjust the space between title and plot
        axs[1].legend()
        axs[1].grid(True)

        axs[2].plot(timestamps, self.energy_dict['tank_soc'], label='Tank SOC')
        axs[2].plot(timestamps, self.energy_dict['battery_soc'], label='Battery SOC')
        axs[2].legend()
        axs[2].grid(True)

        # Subplot for outdoor and indoor temperature
        axs[3].plot(timestamps, self.energy_dict['outdoor_temp'], label='Outdoor Temperature')
        axs[3].plot(timestamps, self.energy_dict['building_temp'], label='Indoor Temperature')
        axs[3].set_xlabel('Time')
        axs[3].set_ylabel('Temperature')
        axs[3].set_title('Temperature Data', pad=20)  # Add pad parameter to adjust the space between title and plot
        axs[3].legend()
        axs[3].grid(True)

        # Subplot for mass flows
        axs[4].plot(timestamps, self.energy_dict['sh_in'], label='Space Heating In')
        axs[4].plot(timestamps, self.energy_dict['sh_out'], label='Space Heating Out')
        axs[4].plot(timestamps, self.energy_dict['dhw_in'], label='DHW In')
        axs[4].plot(timestamps, self.energy_dict['dhw_out'], label='DHW Out')
        axs[4].plot(timestamps, self.energy_dict['hp_in'], label='Heat Pump In')
        axs[4].plot(timestamps, self.energy_dict['hp_out'], label='Heat Pump Out')
        axs[4].set_xlabel('Time')
        axs[4].set_ylabel('Mass Flow')
        axs[4].set_title('Mass Flows', pad=20)  # Add pad parameter to adjust the space between title and plot
        axs[4].legend()
        axs[4].grid(True)

        # Subplot for layer temperatures
        for i in range(4):
            axs[5].plot(timestamps, self.energy_dict[f'layer_{i + 1}_temp'], label=f'Layer {i + 1}')
        axs[5].set_xlabel('Time')
        axs[5].set_ylabel('Temperature (°C)')
        axs[5].set_title('Layer Temperatures Over Time',
                         pad=20)  # Add pad parameter to adjust the space between title and plot
        axs[5].legend()
        axs[5].grid(True)

        plt.tight_layout()
        plt.show()


if __name__ == '__main__':
    import json
    import os
    # Get the current script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the config file
    config_path = '/home/aburabazam/PycharmProjects/Ditens/DistrictGenerator/config/config.json'
    # config_path = os.path.join(script_dir, 'config', 'config.json')

    # Load the config file
    with open(config_path) as f:
        config = json.load(f)
    # Create an EnergyHub instance from the configuration
    energy_hub = EnergyHub.from_config(config['district']['energy_hubs'][0], config['simulation_period'])
    energy_hub.init_controller()
    energy_hub.main()
    energy_hub.plot_energy_dict()
