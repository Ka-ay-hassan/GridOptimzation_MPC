import unittest
import numpy as np

from components.controller.ems import EnergyManagementSystem

class TestEnergyManagementSystem(unittest.TestCase):
    def setUp(self):
        self.energy_management_system = EnergyManagementSystem(slack_device="grid")

    def test_set_and_get(self):
        self.energy_management_system.set_power("device1", [10, 20])
        self.assertEqual(self.energy_management_system.get_power("device1"), [10, 20])

    # def test_add(self):
    #     self.energy_management_system.set_power("device1", [10, 20])
    #     self.energy_management_system.add_power("device1", [5, 10])
    #     self.assertEqual(self.energy_management_system.get_power("device1"), [15, 30])

    def test_calculate_slack(self):
        self.energy_management_system.set_power("device1", [10, 20])
        self.energy_management_system.calculate_slack()
        self.assertEqual(self.energy_management_system.power_dict_kw[self.energy_management_system.slack_device], {"in": -10, "out": -20})

if __name__ == "__main__":
    unittest.main()
