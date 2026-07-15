import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
from utilities.simulation_period import SimulationPeriod
from components.prosumer.heat_pump.heat_pump import HeatPump

def test():
    """Main function to create HeatPump objects and calculate the COP for each temperature."""
    # Create a simulation period
    simulation_period = SimulationPeriod(
        start=datetime(2022, 1, 1),
        end=datetime(2022, 1, 5),
        resolution=timedelta(minutes=1)
    )

    # Define the temperature range for initialization
    init_temperatures = range(20, 81, 10)

    # Define the temperature range for COP calculation
    temperatures = range(-15, 26)

    # Initialize lists to store COP values for each heat pump
    all_cops = []

    # Create a HeatPump object for each initialization temperature and calculate COPs
    for init_temp in init_temperatures:
        hp = HeatPump(simulation_period, 'Outdoor Air/Water_Regulated', 7, init_temp)
        cops = [hp.calculate_cop_thermal(temp, method='curves') or hp.cop_thermal for temp in temperatures]
        all_cops.append((init_temp, cops))

    # Plot the COP at different temperatures for each heat pump
    plt.figure(figsize=(10, 6))
    for init_temp, cops in all_cops:
        plt.plot(temperatures, cops, label=f'Cubic Fit ({init_temp}° Vorlauftemperatur)')
    plt.xlabel('Temperature (°C)')
    plt.ylabel('COP')
    plt.title('COP at Different Temperatures for Various Initial Temperatures')
    plt.legend()
    plt.grid(True)
    plt.show()

    test_temperatures = [
        (10, 35),  # source = 10°C, sink = 35°C
        (0, 35),  # source = 0°C, sink = 35°C
        (-10, 35),  # source = -10°C, sink = 35°C
        (10, 40),  # source = 10°C, sink = 40°C
        (0, 40),  # source = 0°C, sink = 40°C
        (-10, 40)  # source = -10°C, sink = 40°C
    ]

    # Test the calculate_cop_thermal function with the tests temperatures
    # for t_source, t_sink in test_temperatures:
    #     hp_interpolated.set_temperature(t_sink)
    #     hp_interpolated.calculate_cop_thermal(t_source, method='curves')
    #     cop = hp_interpolated.cop_thermal
    #     print(f"For source = {t_source}°C and sink = {t_sink}°C, COP = {cop}")
    #
    # # Test the calculate_partial_load_factor function with different electrical powers
    # electrical_powers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # plfs = []
    # for P_el in electrical_powers:
    #     hp_interpolated.p_el = P_el
    #     plf = hp_interpolated.calculate_partial_load_factor
    #     plfs.append(plf)
    #     print(f"For set electrical power = {P_el} kW, partial load factor = {plf}")
    #
    # # Plot the partial load factor at different electrical powers
    # plt.figure(figsize=(10, 6))
    # plt.plot(electrical_powers, plfs, 'o-')
    # plt.xlabel('Set Electrical Power (kW)')
    # plt.ylabel('Partial Load Factor')
    # plt.title('Partial Load Factor at Different Electrical Powers')
    # plt.grid(True)
    # plt.show()

if __name__ == '__main__':
    test()
