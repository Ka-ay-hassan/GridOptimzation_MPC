"""
Minimalistic example for using the pylpg package
"""
from config.config import PROJ_PATH

import matplotlib.pyplot as plt
from pylpg import lpg_execution, lpgdata


# Simulate the predefined household CHR01 (couple, both employed) for the year 2022
data = lpg_execution.execute_lpg_single_household(
    2022,
    lpgdata.Households.CHR05_Family_3_children_both_with_work,
    lpgdata.HouseTypes.HT03_House_with_a_solar_thermal_System_and_300_L_storage_tank_gas_heating,
)

data_path = PROJ_PATH / "data" / "load_profiles"

data["Hot water_House"].to_csv(data_path / "DHW_load.csv")
# Extract the generated electricity load profile
# electricity_profile = data["Electricity_HH1"]
# print(electricity_profile)
#
# # Resample to 15 minute resolution
# profile = electricity_profile.resample("15min").sum()
#
# # Show a carpet plot
# utils_load.carpet_plot(profile)
# plt.show()