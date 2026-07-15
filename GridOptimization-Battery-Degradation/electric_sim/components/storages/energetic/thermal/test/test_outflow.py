import matplotlib.pyplot as plt
from components.storages.energetic.thermal.thermal_storage import HotWaterTank

C_W = 4180  # specific heat capacity of water in J/(kgK)
RHO = 1  # density of water [kg/l]

def test_hot_water_tank_outflow():
    # Define the parameters for the hot water tank
    init_vals = {
        'layers': {
            'T': [40, 60, 80]
        },
        'hr': {
            'P_el': 0
        }
    }
    params = {
        'height': 2100,
        'diameter': 1200,
        'T_env': 20.0,
        'htc_walls': 1.0,
        'htc_layers': 20,
        'n_layers': 3,
        # 'layers': [
        #     {'bottom': 0, 'top': 700},
        #     {'bottom': 700, 'top': 1400},
        #     {'bottom': 1400, 'top': 2100}
        # ],
        'n_sensors': 3,
        'connections': {
            'cc_in': {'pos': 0},
            'cc_out': {'pos': 2099},
            'gcb_in': {'pos': 1200},
            'gcb_out': {'pos': 2000}
        },
        # 'heating_rods': {
        #     'hr_1': {
        #         'pos': 1700,
        #         'P_th_stages': [0, 500, 1000, 2000, 3000],
        #         'T_max': 80,
        #         'eta': 0.95
        #     }
        # }
    }
    # Create a HotWaterTank instance
    tank = HotWaterTank(params, init_vals)

    # Initialize lists to store the layer temperatures, state of charge, and power at each time step
    layer_temps = [[] for _ in range(params['n_layers'])]
    layer_powers = [[] for _ in range(params['n_layers'])]  # New list to store the power of each layer
    t_mean = []
    T_sensors = [[] for _ in range(params['n_sensors'])]
    soc_values = []
    outflow_powers = []  # New list to store the outflow power

    # Initialize variables to store the previous power of each layer and the outflow
    prev_layer_powers = [0 for _ in range(params['n_layers'])]
    prev_outflow_power = 0

    calculated_mass_flow_rates = []

    # Loop over a certain number of time steps
    for i in range(1440):  # Simulate for one day
        # The tank is being discharged, so hot water is being taken out
        tank.connections['cc_in'].F = 0.6
        tank.connections['gcb_out'].F = -0.6
        tank.connections['cc_in'].T = 15
        # Propagate the hot water tank
        tank.step(60)  # Step size in seconds

        # Store the layer temperatures, state of charge, and power at this time step
        for j, layer in enumerate(tank.layers):
            layer_temps[j].append(layer.T)
            layer_power = layer.volume * RHO * C_W * (layer.T - tank.T_env)  # Calculate the power of the layer
            layer_powers[j].append(layer_power - prev_layer_powers[j])  # Store the change in power
            prev_layer_powers[j] = layer_power  # Update the previous power

        for j, sensor in enumerate(tank.sensors.values()):
            T_sensors[j].append(sensor.T)


        t_mean.append(tank.T_mean)
        soc = tank.SOC()
        soc_values.append(soc)

        outflow_power = tank.connections['gcb_out'].calculate_power(T_min=15)
        outflow_powers.append(outflow_power - prev_outflow_power)  # Store the change in outflow power
        prev_outflow_power = outflow_power  # Update the previous outflow power

        # Calculate the mass flow rate using the calculate_mass_flow_rate function
        calculated_mass_flow_rate = tank.connections['gcb_out'].calculate_mass_flow_rate(outflow_power, T_min=15)
        calculated_mass_flow_rates.append(calculated_mass_flow_rate)

    # Plot the layer temperatures
    plt.figure(figsize=(12, 6))
    for i, temps in enumerate(layer_temps):
        plt.plot(temps, label=f'Layer {i + 1}')
    plt.xlabel('Time step')
    plt.ylabel('Temperature (°C)')
    plt.legend()
    plt.title('Layer Temperatures Over Time')
    plt.show()

    # Plot the change in layer powers
    plt.figure(figsize=(12, 6))
    for i, powers in enumerate(layer_powers):
        plt.plot(powers, label=f'Layer {i + 1}')
    plt.xlabel('Time step')
    plt.ylabel('Change in Power (W)')
    plt.legend()
    plt.title('Change in Layer Power Over Time')
    plt.show()

    # Plot the state of charge
    plt.figure(figsize=(12, 6))
    plt.plot(t_mean)
    plt.xlabel('Time step')
    plt.ylabel('Mean Temperature (°C)')
    plt.title('Mean Temp. TES')
    plt.show()

    plt.figure(figsize=(12, 6))
    plt.plot(soc_values)
    plt.xlabel('Time step')
    plt.ylabel('State of Charge')
    plt.title('State of Charge Over Time')
    plt.show()

    # Plot the change in outflow power
    plt.figure(figsize=(12, 6))
    plt.plot(outflow_powers)
    plt.xlabel('Time step')
    plt.ylabel('Change in Outflow Power (W)')
    plt.title('Change in Outflow Power Over Time')
    plt.show()

    # Plot the calculated mass flow rates
    plt.figure(figsize=(12, 6))
    plt.plot(calculated_mass_flow_rates)
    plt.xlabel('Time step')
    plt.ylabel('Calculated Mass Flow Rate (l/s)')
    plt.title('Calculated Mass Flow Rate Over Time')
    plt.show()

