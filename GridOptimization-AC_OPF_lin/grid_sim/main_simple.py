import pandapower as pp
import pandapower.plotting.plotly as plt
import pandas as pd
from pandapower.timeseries import DFData, run_timeseries
from pandapower.control import ConstControl
from datetime import datetime, timedelta
from pathlib import Path

# # --- Paths and Input ---
# DATA_PATH = Path("/home/abu/PycharmProjects/IEH_Grid_Generator/data")  # Set to your folder where data files are located
# GRID_FILE = DATA_PATH / "uni_grid.xlsx"
# LINE_STD_FILE = DATA_PATH / "line_std_types.xlsx"
# RESULTS_PATH = Path("results")

# --- Paths and Input for Kareem ---
DATA_PATH = Path('C:/Users/kazmo/OneDrive/Desktop/Elektro- und Informationstechnik/FA IER/Project_Code_IER/GridOptimization/grid_sim/data')
GRID_FILE = DATA_PATH / "uni_grid.xlsx"
LINE_STD_FILE = DATA_PATH / "line_std_types.xlsx"
RESULTS_PATH = Path('C:/Users/kazmo/OneDrive/Desktop/Elektro- und Informationstechnik/FA IER/Project_Code_IER/GridOptimization/grid_sim/results')

# --- Helper Functions ---
def load_grid_data(file: Path) -> pp.pandapowerNet:
    """Loads grid data from Excel and initializes the network."""
    net = pp.from_excel(file)

    return net


def add_time_series_to_loads(net: pp.pandapowerNet, profiles_file: Path) -> None:
    """Assigns time series data to loads."""
    profiles = pd.read_csv(profiles_file, index_col=0)  # Time series data in CSV format
    ds = DFData(profiles)

    # Create a ConstControl for dynamic power assignment
    ConstControl(
        net, element="load", variable='p_mw',
        element_index=net.load.index,
        data_source=ds,
        profile_name=net.load.name.values
    )


# --- Main Script ---
def main():
    # Load grid
    net = load_grid_data(GRID_FILE)

    # Define simulation period
    start_time = datetime(2023, 1, 1, 0, 0)
    end_time = datetime(2023, 1, 2, 0, 0)
    resolution = timedelta(minutes=15)
    time_steps = pd.date_range(start=start_time, end=end_time, freq=resolution, inclusive="left")

    # Assign time series to loads
    profiles_file = RESULTS_PATH / "timeseries_mw.csv"  # Generated time series file
    #profiles_file = 'C:/Users/kazmo/OneDrive/Desktop/Elektro- und Informationstechnik/FA IER/Project_Code_IER/GridOptimization/grid_sim/results/timeseries.csv'
    add_time_series_to_loads(net, profiles_file)

    # Run time series simulation
    print("Running time series power flow...")
    run_timeseries(net, time_steps=range(len(time_steps)), verbose=True)

    # Print results
    print(net.res_bus)
    print(net.res_load)
   
    pp.plotting.plotly.simple_plotly(net,
                                     respect_switches=True,
                                     map_style='basic',
                                     figsize=1.0,
                                     aspectratio='auto', 
                                     line_width=1.0, 
                                     bus_size=10.0, 
                                     ext_grid_size=20.0, 
                                     bus_color='blue', 
                                     line_color='grey', 
                                     trafo_color='green', 
                                     trafo3w_color='dark green', 
                                     ext_grid_color='yellow', 
                                     filename='uni_grid-plot.html', 
                                     auto_open=True, 
                                     showlegend=True, 
                                     additional_traces=None)
    
                                             


if __name__ == "__main__":
    main()