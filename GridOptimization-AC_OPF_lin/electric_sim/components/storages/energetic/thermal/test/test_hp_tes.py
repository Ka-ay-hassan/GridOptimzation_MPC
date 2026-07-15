from components.storages.energetic.thermal.thermal_storage import HotWaterTank
import matplotlib.pyplot as plt
import numpy as np
from utilities.simulation_period import SimulationPeriod
from datetime import datetime, timedelta
from components.controller.Controller import BangBangController

simulation_period = SimulationPeriod(
    start=datetime(2022, 1, 1),
    end=datetime(2022, 1, 25),
    resolution=timedelta(minutes=1))


def config_tes():
    # Define the parameters for the hot water tank
    init_vals = {
        'layers': {
            'T': [18, 30, 40, 60]  # Added a new layer at 60 degrees
        },
        'hr_1': {
            'P_el': 3000
        }
    }
    params = {
        'step_size': 300,
        'height': 2200,
        'diameter': 500,
        'T_env': 20.0,
        'htc_walls': 1.0,
        'htc_layers': 20,
        'n_layers': 4,  # Updated the number of layers
        'layers': [
            {'bottom': 0, 'top': 500},
            {'bottom': 500, 'top': 1000},
            {'bottom': 1000, 'top': 1500},
            {'bottom': 1500, 'top': 2200}  # New layer for 60 degrees
        ],
        'n_sensors': 5,  # Updated the number of sensors
        'connections': {
            'sh_in': {'pos': 150},
            'sh_out': {'pos': 1250},
            'dhw_in': {'pos': 100},
            'dhw_out': {'pos': 2100},
            'hp_in': {'pos': 1200},  # Updated hp_in position to 40 degrees layer
            'hp_out': {'pos': 800}  # Updated hp_out position to 30 degrees layer
        },
        'heating_rods': {
            'hr_1': {
                'pos': 2000,
                'P_th_stages': [0, 500, 1000, 2000, 3000],
                'T_max': 60,
                'eta': 0.95
            }
        }
    }
    return params, init_vals


def test_heat_pump_with_tes():
    # Configuration of the tank
    params, init_vals = config_tes()

    # Create a hot water tank
    tank = HotWaterTank(simulation_period, params, init_vals)
    bang_bang_controller = BangBangController(
        initial_state=0,
        Y_min=50,  # Lower threshold for the top layer temperature
        Y_max=60,  # Upper threshold for the top layer temperature
        U_min=0,
        U_max=3000  # Maximum power of the heating rod
    )

    # Simulation parameters
    simulation_time = 24 * 60 * 60  # 24 hours in seconds
    step_size = 60  # 1 minute in seconds

    # Heat pump parameters
    heat_pump_flow_rate = .356  # l/s
    heat_pump_temperature = 40  # °C

    # Lists to store data for plotting
    times = []
    socs = []
    in_flows = []
    out_flows = []
    heating_rod_usage = []
    layer_temps = [[] for _ in range(len(tank.layers))]
    space_heating_demand = []

    # Run the simulation
    for t in range(0, simulation_time, step_size):
        # Determine space heating demand
        hour = (t // 3600) % 24
        if 6 <= hour < 20:
            P_zone_heating = 10  # 10 kW
        else:
            P_zone_heating = 0

        # Set the flow and temperature for the heat pump
        tank.connections['hp_in'].F = heat_pump_flow_rate
        tank.connections['hp_out'].F = -heat_pump_flow_rate
        tank.connections['hp_in'].T = heat_pump_temperature
        tank.connections['sh_in'].T = 18

        # Define the space heating flow rate
        space_heating_flow_rate = P_zone_heating / (4.180 * (tank.connections['sh_out'].T) - tank.connections['sh_in'].T)
        print(tank.layers[-1].T - tank.connections['sh_out'].T)
        tank.connections['sh_out'].F = -space_heating_flow_rate
        tank.connections['sh_in'].F = space_heating_flow_rate

        # Use the BangBangController to control the heating rod
        bang_bang_controller.propagate(Y=tank.layers[-1].T)
        tank.heating_rods['hr_1'].P_th_set = bang_bang_controller.u


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
        out_flows.append(space_heating_flow_rate)
        space_heating_demand.append(P_zone_heating)
        for i, layer in enumerate(tank.layers):
            layer_temps[i].append(layer.T)

    # Convert lists to arrays for easier manipulation
    times = np.array(times)
    socs = np.array(socs)
    in_flows = np.array(in_flows)
    out_flows = np.array(out_flows)
    heating_rod_usage = np.array(heating_rod_usage)
    space_heating_demand = np.array(space_heating_demand)
    layer_temps = [np.array(layer_temp) for layer_temp in layer_temps]

    # Create subplots
    fig, axs = plt.subplots(5, figsize=(12, 12), sharex=True)

    # Plot SOC over time
    axs[0].plot(times, socs, label='SOC')
    axs[0].set_ylabel('SOC')
    axs[0].set_title('State of Charge (SOC) Over Time')
    axs[0].legend()
    axs[0].grid(True)

    # Plot in and out flows over time
    axs[1].plot(times, in_flows, label='In Flow (hp_in)')
    axs[1].plot(times, out_flows, label='Out Flow (sh_out)')
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

    # Plot space heating demand over time
    axs[4].plot(times, space_heating_demand, label='Space Heating Demand')
    axs[4].set_xlabel('Time (s)')
    axs[4].set_ylabel('Power (W)')
    axs[4].set_title('Space Heating Demand Over Time')
    axs[4].legend()
    axs[4].grid(True)

    plt.tight_layout()
    plt.show()

