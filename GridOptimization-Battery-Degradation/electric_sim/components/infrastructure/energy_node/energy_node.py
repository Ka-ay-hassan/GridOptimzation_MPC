from typing import Literal, Any

from components.prosumer.prosumer import Prosumer
from components.infrastructure.buildings.building import Building
from components.prosumer.heat_pump.heat_pump import HeatPump
from components.prosumer.electrical_load import ElectricalLoad
from components.prosumer.dwh_load import DHWLoad
from components.storages.energetic.thermal.thermal_storage import HotWaterTank, config_tes
from components.storages.energetic.electrical.battery import BatterySystem
from components.prosumer.pv import PV

from utilities.simulation_period import SimulationPeriod


class EnergyNode:
    weather_data = None

    def __init__(self, id: str, elements: list, simulation_period: SimulationPeriod, activation_fcn=None) -> None:
        """
        Initialize a Node object.
        """
        self._id = id
        self.elements = elements
        self.simulation_period = simulation_period
        self.activation_fcn = activation_fcn

    @classmethod
    def from_config(cls, id: int, simulation_period: dict, elements: list[dict], activation_fcn=None) -> 'EnergyNode':
        sim_period = SimulationPeriod.from_iso(simulation_period['start'], simulation_period['end'],
                                               simulation_period['resolution'])
        elements = [
            cls.create_element(simulation_period=sim_period, activation_fcn=activation_fcn, **element_info) for
            element_info in elements]
        return cls(id, elements, sim_period, activation_fcn)

    @staticmethod
    def create_element(simulation_period: SimulationPeriod, element_type: str, activation_fcn=None, **kwargs) -> Any:
        kwargs['simulation_period'] = simulation_period
        match element_type:
            case "building":
                print("Building initialization")
                return Building(**kwargs, activation_fcn=activation_fcn)
            case "heat_pump":
                print("HP initialization")
                return HeatPump(**kwargs)
            case "pv":
                print("PV initialization")
                pv_instance = PV(**kwargs)
                EnergyNode.weather_data = pv_instance.weather
                return pv_instance
            case "general_electric_load":
                print("El_Load initialization")
                return ElectricalLoad(**kwargs)
            case "dhw_load":
                print("DHW_Load initialization")
                return DHWLoad(**kwargs)
            case "hot_water_tank":
                print("TES initialization")
                params, init_vals = config_tes()
                params['step_size'] = simulation_period.resolution_seconds
                kwargs.update(params=params, init_vals=init_vals)
                return HotWaterTank(**kwargs)
            case "battery_system":
                print("Batt initialization")
                return BatterySystem(**kwargs)
        raise ValueError(f"{element_type = } unknown")

    @property
    def id(self) -> str:
        return self._id

    @property
    def power_type(self) -> str:
        if self._power_type is None:
            raise ValueError("No power type provided.")
        return self._power_type

    def add_element(self, element: Prosumer) -> None:
        """
        Add an element to this EnergyNode.
        """
        self.elements.append(element)

    def remove_element(self, element: Prosumer) -> None:
        """
        Remove an element from this EnergyNode.
        """
        if element in self.elements:
            self.elements.remove(element)


import json
import unittest
from components.prosumer.prosumer import Prosumer

class TestEnergyNode(unittest.TestCase):
    def test_from_config(self):
        # Load the configuration file
        with open('/home/abu/PycharmProjects/DiTEnS/DistrictGenerator/config/config.json') as f:
            config = json.load(f)

        # Create EnergyNode instances from the configuration
        energy_nodes = [EnergyNode.from_config(hub['id'], config['simulation_period'], hub['elements']) for hub in config['district']['energy_hubs']]

        # Check that the correct number of EnergyNode instances have been created
        self.assertEqual(len(energy_nodes), len(config['district']['energy_hubs']))

        # Check that each EnergyNode has the correct number of elements
        for i, energy_node in enumerate(energy_nodes):
            self.assertEqual(len(energy_node.elements), len(config['district']['energy_hubs'][i]['elements']))

        # Check that each EnergyNode has a Building instance
        for energy_node in energy_nodes:
            self.assertTrue(any(isinstance(element, Building) for element in energy_node.elements))

        # Check the power type of each component in each EnergyNode
        for energy_node in energy_nodes:
            print(energy_node.id)
            for element in energy_node.elements:
                print(element, element.power_type)
                self.assertTrue(element.power_type.issubset(Prosumer.POWER_TYPE_MAP[element.__class__.__name__]))

# Run the test
if __name__ == '__main__':
    unittest.main()



