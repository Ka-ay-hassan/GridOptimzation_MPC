import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from components.prosumer.heat_pump.LC_heat_pump import LargeScaleHeatPump
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

# Assuming HeatPump and SimulationPeriod classes are already defined

def generate_data(simulation_period, power_nom_kw, temperature_range, power_range, num_samples, hp_temp):
    hp = LargeScaleHeatPump(simulation_period, power_nom_kw, hp_temp)

    data = []

    for _ in range(num_samples):
        # Randomly select a temperature and power within the specified ranges
        temperature = np.random.uniform(*temperature_range)
        power = np.random.uniform(*power_range)

        hp.p_el = power

        # Propagate the heat pump model
        t_source = np.random.uniform(temperature_range[0], temperature_range[1])  # Convert to Kelvin
        timestamp = datetime.now()
        hp.propagate(t_source, timestamp)

        # Record the input and output
        data.append([power, t_source+273.15, hp.p_thermal])

    # Convert the data to a DataFrame
    df = pd.DataFrame(data, columns=['Electric Power (kW)', 'Source Temperature (K)', 'Thermal Power (kW)'])

    return df

def main():
    from datetime import timedelta
    from utilities.simulation_period import SimulationPeriod
    import scienceplots

    # Define the simulation period
    simulation_period = SimulationPeriod(
        start=datetime(2022, 1, 1),
        end=datetime(2022, 1, 2),
        resolution=timedelta(minutes=1)
    )

    # Define the heat pump type and nominal power
    heat_pump_type = 'Outdoor Air/Water_Regulated'
    power_nom_kw = 6e3

    # Define the temperature and power ranges
    temperature_range = (40, 50)  # Celsius
    power_range = (0, power_nom_kw)  # kW
    hp_temp = 100

    # Generate data
    num_samples = 10000
    df = generate_data(simulation_period, power_nom_kw, temperature_range, power_range, num_samples, hp_temp)

    # Save the data to a CSV file
    df.to_csv('heat_pump_data.csv', index=False)

    # Plot the data
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(df['Electric Power (kW)'], df['Source Temperature (K)'], df['Thermal Power (kW)'], alpha=0.5, label='Data')

    # Create a linear fit with intercept forced to zero
    X = df[['Electric Power (kW)', 'Source Temperature (K)']].values
    y = df['Thermal Power (kW)'].values
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    # Calculate R² and RMSE
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    # Use the 'science' style

    plt.style.use('science')
    plt.figsize = (9, 9)

    ax.tick_params(axis='both', which='major', labelsize=15)
    ax.tick_params(axis='z', which='major', labelsize=15)

    ax.plot_trisurf(df['Electric Power (kW)'], df['Source Temperature (K)'], y_pred, color='red', alpha=0.5,
                    label='Linear Fit')
    ax.set_xlabel('Electric Power [kW]', fontsize=16, labelpad=15)
    ax.set_ylabel('Source Temp.[K]', fontsize=16, labelpad=15)
    ax.set_zlabel('Thermal Power [kW]', fontsize=16, labelpad=15)
    # ax.set_title(f'Linear Fit\nR²: {r2:.2f}, RMSE: {rmse:.2f}', fontsize=13)
    ax.view_init(elev=30, azim=45)

    plt.tight_layout()
    plt.show()

    # Print R² and RMSE
    print(f'R²: {r2}')
    print(f'RMSE: {rmse}')

    # Print the coefficients of the linear function
    coef = model.coef_
    intercept = model.intercept_
    print(f'Coefficients: {coef}')
    print(f'Intercept: {intercept}')

    # Print the fitting function
    print(f'Fitting function: Thermal Power (kW) = {coef[0]} * Electric Power (kW) + {coef[1]} * Source Temperature (K) + {intercept}')

if __name__ == '__main__':
    main()
