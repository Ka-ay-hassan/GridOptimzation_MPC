import pandas as pd

files = {
    "PV Active Power": r'C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_results\3rd_try\res_net_active.csv',
    "PV Reactive Power": r'C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_results\3rd_try\res_net_reactive.csv',
    "ESS Active Power": r'C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_results\3rd_try\batt_total_active.csv',
    "ESS Reactive Power": r'C:\Users\kazmo\OneDrive\Desktop\Elektro- und Informationstechnik\FA IER\Code_IER\GridOptimization\MPC\1_mpc_results\3rd_try\batt_total_reactive.csv',
}

def inspect_and_print(path, label):
    df = pd.read_csv(path, delimiter=';')  # <-- important fix here
    print(f"\n--- {label} ---")
    print("Columns:", list(df.columns))
    print("Shape:", df.shape)
    print("Head:")
    print(df.head())

    first_col = df.columns[0]

    # Check if first column is timestamp-like (usually string)
    if pd.api.types.is_datetime64_any_dtype(df[first_col]) or not pd.api.types.is_numeric_dtype(df[first_col]):
        # Timestamp in first column, take next two columns
        data_cols = df.columns[1:3]
    else:
        # No timestamp, take first two columns
        data_cols = df.columns[:2]

    print(f"\nPrinting first two data columns: {list(data_cols)}")
    for idx, row in df.iterrows():
        try:
            print(f"{row[data_cols[0]]},{row[data_cols[1]]}")
        except IndexError:
            print(f"Incomplete row at index {idx}: {row.values}")

for label, path in files.items():
    inspect_and_print(path, label)
