from components.storages.energetic.thermal.thermal_storage import HotWaterTank
def test_propagate():


    init_vals = {
        'layers': {
            'T': [30, 50, 70]
        },
        'hr': {
            'P_el': 0
        }
    }

    hwt_params = {
        'height': 2100,
        'diameter': 1200,
        'T_env': 20.0,
        'htc_walls': 1.0,
        'htc_layers': 20,
        'n_layers': 3,
        'T_init': [30, 50, 70],
        'n_sensors': 3,
        'connections': {
            'cc_in': {'pos': 0},
            'cc_out': {'pos': 2099},
            'gcb_in': {'pos': 1700},
            'gcb_out': {'pos': 900}
        }
    }
    # Initialize the hot water tank with some parameters and initial values
    tank = HotWaterTank(hwt_params, init_vals)

    # Define the flow rates and temperatures for the connections
    connection_flows = {'cc_in': 0.6, 'cc_out': 0.6, 'gcb_in': 0.6, 'gcb_out': -0.6}
    connection_temps = {'cc_in': 15}

    # Call the propagate method with the defined flow rates and temperatures
    tank.propagate(connection_flows, connection_temps)

    # Check that the flow rates and temperatures have been set correctly
    for connection_name, flow_rate in connection_flows.items():
        assert tank.connections[connection_name].F == flow_rate, f"Flow rate for {connection_name} not set correctly"

    for connection_name, temperature in connection_temps.items():
        assert tank.connections[connection_name].T == temperature, f"Temperature for {connection_name} not set correctly"

    # Add more assertions here to test other aspects of the propagate method
