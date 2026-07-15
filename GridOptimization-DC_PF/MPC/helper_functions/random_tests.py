import pandas as pd
import numpy as np

res_path = 'C:\\Users\\kazmo\\OneDrive\\Desktop\\Elektro- und Informationstechnik\\FA IER\\Code_IER\\GridOptimization\\MPC\\mpc_el_data.csv'

time_intervals = 288

res_data = pd.read_csv(res_path)
p_res_data1 = res_data['pv_power'].values[:time_intervals]
p_res_data2 = res_data['pv_power'].values[:time_intervals]

p_res_data = np.column_stack((p_res_data1, p_res_data2))


#print(matrix)

print(p_res_data[:, 0])