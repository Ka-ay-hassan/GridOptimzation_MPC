import unittest
import os
import json
from components.infrastructure.buildings.building import Building
from components.controller.Controller import PIDController

class TestBuildingSimulation(unittest.TestCase):
    def setUp(self):
        # Set up the test environment
        self.json_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config_building.json')
        with open(self.json_file, 'r') as f:
            self.config = json.load(f)

        # Initialize the PID controller with the desired setpoint
        self.pid_controller = PIDController(p=0.5, i=0.05, d=0.01, dt=60)
        self.control_action = 0

        # Define the activation function
        def activation_function():
            current_temp = self.building.T_indoor
            self.control_action = self.pid_controller.update(21.0 - current_temp, self.control_action)
            self.building.actuator_value = self.control_action

        # Initialize the building with the activation function
        self.building = Building(self.config, activation_function)

    def test_simulation(self):
        # Run the simulation
        self.building.propagate()
        self.building.save_results()
        self.building.plot_results()

        # Check if the result file is created
        result_path = os.path.join(self.building.config["result_path"],
                                   f"{self.building.house_type}_{self.building.dt_s}.csv")
        self.assertTrue(os.path.exists(result_path), "Result file does not exist after simulation.")

        # Check if the dataframe is not empty
        self.assertFalse(self.building.df.empty, "Dataframe is empty after simulation.")

    def tearDown(self):
        # Clean up the test environment if necessary
        pass

if __name__ == '__main__':
    unittest.main()
