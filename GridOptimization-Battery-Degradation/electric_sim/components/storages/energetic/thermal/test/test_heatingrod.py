from components.storages.energetic.thermal.thermal_storage import HotWaterTank, config_tes
import matplotlib.pyplot as plt
import numpy as np
from utilities.simulation_period import SimulationPeriod
from datetime import datetime, timedelta

simulation_period = SimulationPeriod(
    start=datetime(2022, 1, 1),
    end=datetime(2022, 1, 25),
    resolution=timedelta(minutes=1)
)

def test_hot_water_tank():
    # Configuration of the tank
    params, init_vals = config_tes()

    # Create a hot water tank
    tank = HotWaterTank(simulation_period, params, init_vals)

    # Simulation parameters
    simulation_time = 480 * 60 * 60  # 48 hours in seconds
    step_size = 60  # 1 minute in seconds

    # Heat pump parameters
    heat_pump_flow_rate = 0.1  # l/s
    heat_pump_temperature = 40  # °C (increased temperature)

    # Heating rod parameters
    heating_rod_power = 5000  # W

    # Lists to store data for plotting
    times = []
    socs = []
    in_flows = []
    out_flows = []
    heating_rod_usage = []
    layer_temps = [[] for _ in range(len(tank.layers))]

    # Run the simulation
    for t in range(0, simulation_time, step_size):
        # Set the flow and temperature for the heat pump
        heat_pump_flow_rate = 25 + 0.05 * np.sin(2 * np.pi * t / simulation_time)  # Varying flow rate
        tank.connections['hp_in'].F = heat_pump_flow_rate
        tank.connections['hp_in'].T = heat_pump_temperature

        # Define the domestic hot water flow rate
        if t % (3 * 60 * 60) < 2 * 60:  # Every 3 hours, for 2 minutes
            domestic_hot_water_flow_rate = 0  # l/s
        else:
            domestic_hot_water_flow_rate = 0  # l/s

        tank.connections['sh_out'].F = -heat_pump_flow_rate
        tank.connections['dhw_out'].F = -domestic_hot_water_flow_rate
        tank.connections['dhw_in'].F = domestic_hot_water_flow_rate
        tank.connections['dhw_in'].T = 18

        # Check the temperature of the top layer
        if tank.layers[-1].T < 60:
            # If the temperature is less than 60°C, turn on the heating rod
            tank.heating_rods['hr_1'].P_th_set = heating_rod_power
        else:
            # Otherwise, turn off the heating rod
            tank.heating_rods['hr_1'].P_th_set = 0

        # Update the heating rod
        tank.heating_rods['hr_1'].update()

        # Perform the simulation step
        tank.step(step_size)

        # Check if the heating rod is used
        heating_rod_usage.append(1 if tank.heating_rods['hr_1'].P_th > 0 else 0)

        # Store data for plotting
        times.append(t)
        socs.append(tank.SOC)
        in_flows.append(heat_pump_flow_rate)
        out_flows.append(domestic_hot_water_flow_rate)
        for i, layer in enumerate(tank.layers):
            layer_temps[i].append(layer.T)

    # Convert lists to arrays for easier manipulation
    times = np.array(times)
    socs = np.array(socs)
    in_flows = np.array(in_flows)
    out_flows = np.array(out_flows)
    heating_rod_usage = np.array(heating_rod_usage)
    layer_temps = [np.array(layer_temp) for layer_temp in layer_temps]

    # Create subplots
    fig, axs = plt.subplots(4, figsize=(12, 10), sharex=True)

    # Plot SOC over time
    axs[0].plot(times, socs, label='SOC')
    axs[0].set_ylabel('SOC')
    axs[0].set_title('State of Charge (SOC) Over Time')
    axs[0].legend()
    axs[0].grid(True)

    # Plot in and out flows over time
    axs[1].plot(times, in_flows, label='In Flow (hp_in)')
    axs[1].plot(times, out_flows, label='Out Flow (dhw_out)')
    axs[1].set_ylabel('Flow Rate (l/s)')
    axs[1].set_title('In and Out Flows Over Time')
    axs[1].legend()
    axs[1].grid(True)

    # Plot heating rod usage over time
    axs[2].plot(times, heating_rod_usage, label='Heating Rod Usage')
    axs[2].set_xlabel('Time (s)')
    axs[2].set_ylabel('Usage (On/Off)')
    axs[2].set_title('Heating Rod Usage Over Time')
    axs[2].legend()
    axs[2].grid(True)

    # Plot layer temperatures over time
    for i, layer_temp in enumerate(layer_temps):
        axs[3].plot(times, layer_temp, label=f'Layer {i+1}')
    axs[3].set_xlabel('Time (s)')
    axs[3].set_ylabel('Temperature (°C)')
    axs[3].set_title('Layer Temperatures Over Time')
    axs[3].legend()
    axs[3].grid(True)

    plt.tight_layout()
    plt.show()

# Run the test function
test_hot_water_tank()
