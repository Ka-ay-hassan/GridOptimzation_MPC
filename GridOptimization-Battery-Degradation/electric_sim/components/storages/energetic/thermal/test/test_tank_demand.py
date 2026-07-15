from utilities.simulation_period import SimulationPeriod
import matplotlib.pyplot as plt
from components.storages.energetic.thermal.thermal_storage import HotWaterTank
from components.prosumer.dwh_load import DHWLoad
from datetime import timedelta, datetime


def test_hot_water_tank_with_dhw_load():
    # Define the parameters for the hot water tank
    params = {
        'height': 2100,
        'diameter': 1200,
        'T_env': 20.0,
        'htc_walls': 1.0,
        'htc_layers': 20,
        'n_layers': 3,
        'n_sensors': 3,
        'connections': {
            'cc_in': {'pos': 0},
            'cc_out': {'pos': 2099},
        },
    }

    # Initialize the hot water tank
    tank = HotWaterTank(params)

    # Define the simulation period
    simulation_period = SimulationPeriod(
        start=datetime(2024, 1, 1),
        end=datetime(2024, 12, 31),
        resolution=timedelta(minutes=1)
    )

    # Initialize the DHW load
    load = DHWLoad(simulation_period=simulation_period)

    # Initialize lists to store the layer temperatures and state of charge at each time step
    layer_temps = [[] for _ in range(params['n_layers'])]
    states_of_charge = []

    # Loop over the simulation period
    for timestamp in simulation_period:
        # Get the DHW demand for the current time step
        dhw_demand = load.dwh_demand(timestamp)

        # The tank is being discharged, so hot water is being taken out
        tank.connections['cc_in'].F = dhw_demand# No water is being put in
        tank.connections['cc_in'].T = 20  # Temperature in °C
        tank.connections['cc_out'].F = -dhw_demand  # Flow rate in L/s
        tank.connections['cc_out'].T = 35  # Temperature in °C

        # Propagate the hot water tank
        tank.step(15*60)  # Step size in seconds

        # Store the layer temperatures and state of charge at this time step
        for j, layer in enumerate(tank.layers):
            layer_temps[j].append(layer.T)
        states_of_charge.append(tank.T_mean)

    # Plot the layer temperatures
    plt.figure(figsize=(12, 6))
    for i, temps in enumerate(layer_temps):
        plt.plot(temps, label=f'Layer {i+1}')
    plt.xlabel('Time step')
    plt.ylabel('Temperature (°C)')
    plt.legend()
    plt.title('Layer Temperatures Over Time')
    plt.show()

    # Plot the state of charge
    plt.figure(figsize=(12, 6))
    plt.plot(states_of_charge)
    plt.xlabel('Time step')
    plt.ylabel('State of Charge (°C)')
    plt.title('State of Charge Over Time')
    plt.show()

