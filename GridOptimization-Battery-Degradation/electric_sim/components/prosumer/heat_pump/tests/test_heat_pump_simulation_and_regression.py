def test_heat_pump_simulation_and_regression():
    from datetime import timedelta
    import numpy as np
    from sklearn.linear_model import LinearRegression
    import matplotlib.pyplot as plt
    from utilities.simulation_period import SimulationPeriod
    from datetime import timedelta
    from datetime import datetime
    from components.prosumer.heat_pump.heat_pump import HeatPump

    # Create a HeatPump object
    simulation_period = SimulationPeriod(
        start=datetime(2022, 1, 1),
        end=datetime(2022, 1, 5),
        resolution=timedelta(minutes=1)
    )
    hp = HeatPump(simulation_period, 'Outdoor Air/Water_Regulated', 7, 35.1)

    # Initialize lists to store the thermal power and electric power at each time step
    P_thermal_history = []
    P_el_history = []

    # Define the on and off periods for the heat pump (in minutes)
    on_period = 60
    off_period = 60

    # Initialize a counter for the current period
    period_counter = 0

    # Define parameters for the sinusoidal temperature curve
    amplitude = 10
    period = 24 * 60
    phase = 0
    mean_temp = 10

    # Loop over a certain number of time steps
    for i, timestamp in enumerate(simulation_period):
        # Determine the current period (on or off)
        hp.p_el = 7 if period_counter < on_period else 0

        # Update the period counter
        period_counter = (period_counter + 1) % (on_period + off_period)

        # Calculate the source temperature as a sinusoidal function of time
        t_source = amplitude * np.sin(2 * np.pi * (i / period - phase)) + mean_temp

        # Propagate the heat pump
        hp.propagate(t_source, timestamp)

        # Store the thermal power and electric power at this time step
        P_thermal_history.append(hp.p_thermal)
        P_el_history.append(hp.p_el)

    # Prepare the data for regression
    X = np.array(P_el_history).reshape(-1, 1)  # Input feature: electric power
    y = np.array(P_thermal_history)  # Target variable: thermal power

    # Create and train a linear regression model
    model = LinearRegression().fit(X, y)

    # Print the coefficients of the linear regression model
    print("Coefficient: ", model.coef_)
    print("Intercept: ", model.intercept_)

    # Plot the original data along with the fitted line
    plt.scatter(X, y, color='blue', label='Original data')
    plt.plot(X, model.predict(X), color='red', label='Fitted line')
    plt.xlabel('Electric Power Input (kW)')
    plt.ylabel('Heat Output (kW)')
    plt.legend()
    plt.show()
