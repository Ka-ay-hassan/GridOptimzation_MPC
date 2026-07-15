import numpy as np
from collections import defaultdict
import pandas as pd
from functools import partial
from itertools import repeat

def create_nested_defaultdict(default_factory, depth=1):
    """Create a nested defaultdict with a specified depth."""
    result = partial(defaultdict, default_factory)
    for _ in repeat(None, depth - 1):
        result = partial(defaultdict, result)
    return result()

class EnergyManagementSystem:
    """
    Class defining an EnergyManagementSystem to calculate the energy exchange.
    All loads are modelled in the consumer system, meaning load is positive and generation is
    negative active power. Please pay attention to the correct signing of the reactive power as
    well. This is referenced by pandapower.
    """

    def __init__(self, slack_device=None, dtype=float):
        """Initialize the EnergyManagementSystem."""
        self.slack_device = slack_device  # The device that balances power in the system
        self.power_dict_kw = create_nested_defaultdict(float,
                                                       depth=3)  # Dictionary to store power values and control setpoints of devices
        self.dtype = dtype  # Data type of power values
        if slack_device is not None:
            self.power_dict_kw[slack_device]['power'].update(
                {"in": 0, "out": 0})  # Initialize slack device power values
            self.power_dict_kw[slack_device]['setpoint'] = {}  # Initialize slack device control setpoints
            self.power_dict_kw[slack_device]['measurements'] = {}  # Initialize slack device measurement values

    def adjust_dtype(self, power_kw):
        """Adjust the data type of the power values."""
        power_kw = power_kw.tolist() if isinstance(power_kw, np.ndarray) else power_kw
        power_kw = power_kw if isinstance(power_kw, list) else [power_kw]
        return power_kw

    def set_power(self, device, power_kw):
        """Update device power."""
        if device == self.slack_device:
            raise ValueError("Cannot directly set power of the slack device.")
        power_kw = self.adjust_dtype(power_kw)
        if len(power_kw) != 2:
            raise ValueError("Must provide two power values: 'in' and 'out'.")
        # Ensure 'in' power is negative and 'out' power is positive
        power_kw = np.array([-abs(power_kw[0]), abs(power_kw[1])], dtype=self.dtype)
        self.power_dict_kw[device]['power'].update({"in": power_kw[0], "out": power_kw[1]})
        self.calculate_slack()

    def calculate_balance(self):
        """
        Calculate the energy balance for the hub.
        """
        total_in = sum(device['power']['in'] for device in self.power_dict_kw.values())
        total_out = sum(device['power']['out'] for device in self.power_dict_kw.values())
        balance = total_out + total_in  # Should be zero if balanced

        return balance

    def set_setpoint(self, device, setpoint):
        """Set control setpoint for a device."""
        self.power_dict_kw[device]['setpoint'] = setpoint

    def get_setpoint(self, device, power):
        """Get control setpoint for a device."""
        return self.power_dict_kw[device]['setpoint'].get(power, None)

    def set_measurements(self, device, measurements):
        """Set measurements for a device."""
        self.power_dict_kw[device]['measurements'] = measurements

    def get_measurements(self, device):
        """Get measurements for a device."""
        return self.power_dict_kw[device].get('measurements', None)

    def add_power(self, device, power_kw):
        """Add power to existing value of a device."""
        if device == self.slack_device:
            raise ValueError("Cannot directly add power to the slack device.")
        power_kw = self.adjust_dtype(power_kw)
        power_kw[0] += self.power_dict_kw[device]['power']["in"]
        power_kw[1] += self.power_dict_kw[device]['power']["out"]
        self.set_power(device, power_kw)

    def get_power(self, device):
        """Get power values of a device."""
        return [abs(self.power_dict_kw[device]['power']["in"]), self.power_dict_kw[device]['power']["out"]]

    def calculate_slack(self):
        """Calculate power on slack device."""
        if self.slack_device is not None:
            total_power = -sum(sum(device[1]['power'].values()) for device in self.power_dict_kw.items() if device[0] != self.slack_device)
            self.power_dict_kw[self.slack_device]['power'].update({"in": min(total_power, 0), "out": max(total_power, 0)})

    def set_sum(self, name, power_kw):
        """updates bus power

        Args:
          power_kw: list with 1 signed power value: [out], consumed power ("in") is negative.
          name:
        """
        power_kw = self.adjust_dtype(power_kw)
        if len(power_kw) == 1:
            # if only one number is given adopt with given sign
            power_kw = np.array([min(0, power_kw[0]), max(0, power_kw[0])], dtype=self.dtype)
        else:
            raise ValueError("wrong input dimension")
        self.set_power(name, power_kw)

    def get_sum(self, name):
        """

        Args:
          name:

        Returns:

        """
        return sum(self.power_dict_kw[name]['power'].values())

    def get_DataFrame(self):
        """ """
        return pd.DataFrame.from_dict(self.power_dict_kw)

    def get_sum_DataFrame(self, index=0):
        """

        Args:
          index:  (Default value = 0)

        Returns:

        """
        df = pd.DataFrame(data=self.get_DataFrame().sum(axis=0)).T
        df.index = [index]
        return df

    def __str__(self):
        return str(self.power_dict_kw)


def test_EnergyManagementSystem():
    # Create an instance of EnergyManagementSystem with 'grid' as the slack device
    ems = EnergyManagementSystem(slack_device='grid')

    # Set power for 'device1'
    ems.set_power('device1', [10, 5])
    ems.set_setpoint('device1', {'voltage': 230, 'frequency': 50})

    # Set power for 'device2'
    ems.set_power('device2', [20, 10])
    ems.set_setpoint('device2', {'voltage': 240, 'frequency': 60})

    # Print the entire energy dictionary
    print(ems.power_dict_kw)

    # Test get_power method for 'device1'
    device1_power = ems.get_power('device1')
    print(f"Device1 Power: {device1_power}")
    assert device1_power == [10.0, 5.0], f"Expected [10.0, 5.0], but got {device1_power}"
    #
    # Test get_power method for 'device2'
    device2_power = ems.get_power('device2')
    print(f"Device2 Power: {device2_power}")
    assert device2_power == [20.0, 10.0], f"Expected [20.0, 10.0], but got {device2_power}"
    #
    # Test get_power method for slack device 'grid'
    grid_power = ems.get_power('grid')
    print(f"Grid Power: {grid_power}")
    #
    # # Calculate the expected grid power values
    # total_in_power = sum(
    #     device['power']['in'] for device in ems.power_dict_kw.values() if device != ems.power_dict_kw['grid'])
    # total_out_power = sum(
    #     device['power']['out'] for device in ems.power_dict_kw.values() if device != ems.power_dict_kw['grid'])
    # expected_grid_power = [abs(total_in_power), total_out_power]
    #
    # assert grid_power == expected_grid_power, f"Expected {expected_grid_power}, but got {grid_power}"


if __name__ == "__main__":
    test_EnergyManagementSystem()
