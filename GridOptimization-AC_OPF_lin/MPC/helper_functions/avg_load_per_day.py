import pandas as pd
import numpy as np

def sum_daily_energy(load_df):
    """
    load_df: pd.DataFrame
        Rows: sequential 15-min intervals (no timestamps)
        Columns: buses with load values in MW

    Returns:
        pd.DataFrame: daily energy per bus in MWh
                      index = day number starting from 0
    """
    intervals_per_day = 96
    n_rows = load_df.shape[0]

    # Calculate number of complete days in data
    n_days = n_rows // intervals_per_day

    # Trim data to full days only
    trimmed_df = load_df.iloc[:n_days * intervals_per_day]

    # Add a 'day' column to group by
    day_indices = np.repeat(np.arange(n_days), intervals_per_day)

    trimmed_df = trimmed_df.copy()
    trimmed_df['day'] = day_indices

    # Calculate energy per timestep (MW * 0.25h)
    trimmed_df.iloc[:, :-1] = trimmed_df.iloc[:, :-1] * 0.25

    # Group by day and sum
    daily_energy = trimmed_df.groupby('day').sum()

    # Drop 'day' column if it exists as a column
    daily_energy = daily_energy.drop(columns=['day'], errors='ignore')

    return daily_energy

import pandas as pd

def total_energy_one_day(load_df):
    """
    load_df: pd.DataFrame
        Rows: sequential 15-min intervals for one day (96 rows)
        Columns: buses with load in MW
    
    Returns:
        float: total energy for all buses combined in MWh for that day
    """
    intervals_per_day = 96
    assert load_df.shape[0] >= intervals_per_day, "Data must have at least 96 rows for one full day."
    
    # Take first 96 rows (one day)
    day_data = load_df.iloc[:intervals_per_day]

    # Calculate energy per timestep (MW * 0.25 hours)
    energy_per_timestep = day_data * 0.25

    # Sum over all buses and all timesteps
    total_energy = energy_per_timestep.sum().sum()

    return total_energy




# Example usage:
load_df = pd.read_csv('C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\grid_sim\\results\\aggregated_bus_time_series.csv', index_col=0, parse_dates=True)
res_path = pd.read_csv('C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\combined_pv_outputs.csv', index_col=0, parse_dates=True)


daily_energy = sum_daily_energy(load_df)
print(daily_energy)
total = total_energy_one_day(load_df)
print(f"Total energy for all buses combined in one day: {total:.2f} MWh")

daily_energy = sum_daily_energy(res_path)
print(daily_energy)
total = total_energy_one_day(res_path)
print(f"Total energy for all PV combined in one day: {total:.2f} kWh")
