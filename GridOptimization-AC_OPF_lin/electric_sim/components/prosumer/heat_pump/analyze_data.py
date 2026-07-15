#!/usr/bin/env python

"""analyze_data.py: Analyze heat_pump for heat pumps from hplib database:
https://github.com/FZJ-IEK3-VSA/hplib/blob/main/output/database.csv"""

__author__ = "Abdul Azzam"
__copyright__ = "Copyright (C) 2023 Abdul Azzam"
__license__ = "GPL"
__version__ = "1.0"

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from sklearn.metrics import r2_score, mean_squared_error

def main():
    # Load the heat_pump from the CSV file
    df = pd.read_csv('../../../data/heat_pump/database_reduced.csv')
    df = df[df['cop_minus7_l'].notna()]
    # df.to_csv('heat_pump/database_reduced.csv')

    # Get the unique types of heat pumps
    types = df['types'].unique()

    # Create a dictionary to store the DataFrames for each type
    dfs = {type: df[df['types'] == type] for type in types}

    cop_columns = ["cop_minus7_h", "cop_2_h", "cop_7_h", "cop_12_h"]
    mean_cops = {type: dfs[type][cop_columns].mean() for type in types}

    # Define the temperatures
    temperatures = [-7, 2, 7, 12]
    df['type_subtype'] = df['types'] + '_' + df['Subtype']

    # Get the unique type-subtype combinations
    type_subtypes = df['type_subtype'].unique()
    type_subtypes = np.array([subtype for subtype in type_subtypes.tolist() if str(subtype) != 'nan'])

    # Create a dictionary to store the DataFrames for each type-subtype combination
    dfs_type_subtype = {type_subtype: df[df['type_subtype'] == type_subtype] for type_subtype in type_subtypes}
    mean_cops_type_subtype = {type_subtype: dfs_type_subtype[type_subtype][cop_columns].mean() for type_subtype in type_subtypes}

    coeffs_type_subtype = {'linear': {}, 'quadratic': {}, 'cubic': {}}

    # Create figures for each fit type
    fig_linear, ax_linear = plt.subplots(figsize=(10, 6))
    fig_quadratic, ax_quadratic = plt.subplots(figsize=(10, 6))
    fig_cubic, ax_cubic = plt.subplots(figsize=(10, 6))

    # Now you can repeat your analysis for each subtype
    temperatures_kelvin = [temp + 273.15 for temp in temperatures]
    for subtype in type_subtypes:
        mean_cop_subtype = mean_cops_type_subtype[subtype]  # Get the Series of mean COPs for this subtype

        # Perform linear regression
        linear_coeffs_subtype = np.polyfit(temperatures, mean_cop_subtype, 1)
        linear_fit_subtype = np.polyval(linear_coeffs_subtype, temperatures)
        coeffs_type_subtype['linear'][subtype] = linear_coeffs_subtype

        # Perform quadratic regression
        quadratic_coeffs_subtype = np.polyfit(temperatures, mean_cop_subtype, 2)
        quadratic_fit_subtype = np.polyval(quadratic_coeffs_subtype, temperatures)
        coeffs_type_subtype['quadratic'][subtype] = quadratic_coeffs_subtype

        # Perform cubic regression
        cubic_coeffs_subtype = np.polyfit(temperatures, mean_cop_subtype, 3)
        cubic_fit_subtype = np.polyval(cubic_coeffs_subtype, temperatures)
        coeffs_type_subtype['cubic'][subtype] = cubic_coeffs_subtype

        # Calculate R-squared and RMSE for the linear fit
        r2_linear_subtype = r2_score(mean_cop_subtype, linear_fit_subtype)
        rmse_linear_subtype = np.sqrt(mean_squared_error(mean_cop_subtype, linear_fit_subtype))

        # Calculate R-squared and RMSE for the quadratic fit
        r2_quadratic_subtype = r2_score(mean_cop_subtype, quadratic_fit_subtype)
        rmse_quadratic_subtype = np.sqrt(mean_squared_error(mean_cop_subtype, quadratic_fit_subtype))

        # Calculate R-squared and RMSE for the cubic fit
        r2_cubic_subtype = r2_score(mean_cop_subtype, cubic_fit_subtype)
        rmse_cubic_subtype = np.sqrt(mean_squared_error(mean_cop_subtype, cubic_fit_subtype))

        # Print the results
        print(f'{subtype} Linear Fit: R-squared = {r2_linear_subtype}, RMSE = {rmse_linear_subtype}')
        print(f'{subtype} Quadratic Fit: R-squared = {r2_quadratic_subtype}, RMSE = {rmse_quadratic_subtype}')
        print(f'{subtype} Cubic Fit: R-squared = {r2_cubic_subtype}, RMSE = {rmse_cubic_subtype}')

        # Plot the mean COP and fits for each subtype
        ax_linear.scatter(temperatures, mean_cop_subtype, label=f'{subtype} Mean COP')
        ax_linear.plot(temperatures, linear_fit_subtype, label=f'{subtype} Linear Fit')

        ax_quadratic.scatter(temperatures, mean_cop_subtype, label=f'{subtype} Mean COP')
        ax_quadratic.plot(temperatures, quadratic_fit_subtype, label=f'{subtype} Quadratic Fit')

        ax_cubic.scatter(temperatures, mean_cop_subtype, label=f'{subtype} Mean COP')
        ax_cubic.plot(temperatures, cubic_fit_subtype, label=f'{subtype} Cubic Fit')

    for fit_type in ['linear', 'quadratic', 'cubic']:
        df_coeffs = pd.DataFrame(coeffs_type_subtype[fit_type]).transpose()
        df_coeffs.to_csv(f'{fit_type}_coeffs_high.csv')

    # Add labels and title for linear fit plot
    ax_linear.set_xlabel('Temperature (°C)')
    ax_linear.set_ylabel('Mean COP')
    ax_linear.set_title('Mean COP at Different Temperatures (Linear Fit)')
    ax_linear.legend()

    # Add labels and title for quadratic fit plot
    ax_quadratic.set_xlabel('Temperature (°C)')
    ax_quadratic.set_ylabel('Mean COP')
    ax_quadratic.set_title('Mean COP at Different Temperatures (Quadratic Fit)')
    ax_quadratic.legend()

    # Add labels and title for cubic fit plot
    ax_cubic.set_xlabel('Temperature (°C)')
    ax_cubic.set_ylabel('Mean COP')
    ax_cubic.set_title('Mean COP at Different Temperatures (Cubic Fit)')
    ax_cubic.legend()

    # Show the plots
    plt.show()

# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# from sklearn.metrics import r2_score, mean_squared_error
#
# def piecewise_fit(temperatures, mean_cop_subtype):
#     # Fit cubic polynomial within the range
#     cubic_coeffs = np.polyfit(temperatures, mean_cop_subtype, 3)
#     cubic_fit = np.polyval(cubic_coeffs, temperatures)
#
#     # Fit linear polynomials at the boundaries
#     linear_coeffs_low = np.polyfit(temperatures[:2], mean_cop_subtype[:2], 1)
#     linear_coeffs_high = np.polyfit(temperatures[-2:], mean_cop_subtype[-2:], 1)
#
#     def piecewise_function(x):
#         if x < temperatures[0]:
#             return np.polyval(linear_coeffs_low, x)
#         elif x > temperatures[-1]:
#             return np.polyval(linear_coeffs_high, x)
#         else:
#             return np.polyval(cubic_coeffs, x)
#
#     return piecewise_function
#
# def main():
#     # Load the heat_pump from the CSV file
#     df = pd.read_csv('../../../data/heat_pump/database_reduced.csv')
#     df = df[df['cop_minus7_l'].notna()]
#
#     # Define the temperatures
#     temperatures = [-7, 2, 7, 12]
#     df['type_subtype'] = df['types'] + '_' + df['Subtype']
#
#     # Get the unique type-subtype combinations
#     type_subtypes = df['type_subtype'].unique()
#     type_subtypes = np.array([subtype for subtype in type_subtypes.tolist() if str(subtype) != 'nan'])
#
#     # Create a dictionary to store the DataFrames for each type-subtype combination
#     dfs_type_subtype = {type_subtype: df[df['type_subtype'] == type_subtype] for type_subtype in type_subtypes}
#     mean_cops_type_subtype = {type_subtype: dfs_type_subtype[type_subtype][["cop_minus7_h", "cop_2_h", "cop_7_h", "cop_12_h"]].mean() for type_subtype in type_subtypes}
#
#     # Create a figure
#     plt.figure(figsize=(10, 6))
#
#     # Now you can repeat your analysis for each subtype
#     for subtype in type_subtypes:
#         mean_cop_subtype = mean_cops_type_subtype[subtype]  # Get the Series of mean COPs for this subtype
#
#         # Create the piecewise function
#         piecewise_func = piecewise_fit(temperatures, mean_cop_subtype)
#
#         # Generate data for plotting
#         x_vals = np.linspace(-10, 15, 100)
#         y_vals = [piecewise_func(x) for x in x_vals]
#
#         # Plot the mean COP and piecewise fit
#         plt.scatter(temperatures, mean_cop_subtype, label=f'{subtype} Mean COP')
#         plt.plot(x_vals, y_vals, label=f'{subtype} Piecewise Fit')
#
#     # Add labels and title
#     plt.xlabel('Temperature (°C)')
#     plt.ylabel('Mean COP')
#     plt.title('Mean COP at Different Temperatures with Piecewise Fit')
#
#     # Add a legend
#     plt.legend()
#
#     # Show the plot
#     plt.show()

if __name__ == "__main__":
    main()
