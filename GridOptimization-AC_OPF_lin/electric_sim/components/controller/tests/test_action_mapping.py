from components.controller.rbc.rbc_action_mapping import ACTION_MAPPING

def test_action_mapping():
    # Define a sample data for testing
    data = {
        'PV_Power': 10,
        'SH': True,
        'DHW': False,
        'TES_SOC': 0.5,
        'SOCmax': 1,
        'T_out': 15,
        'T_out_limit': 10,
        'Batt_SOC': 0.8,
        'SOCmin': 0,
        'EH': 0,
        'Battery_Charge_Threshold': 0,
        'Grid_Feed': 0,
        'Max_Rate_Limit': 0,
    }

    # Iterate over each condition in the action mapping
    for condition, action_map in ACTION_MAPPING.items():
        # Evaluate the condition with the sample data
        condition_result = condition(data)
        # Get the corresponding action based on the condition result
        action = action_map[condition_result]
        # If the action is a dictionary, it means there are nested conditions
        if isinstance(action, dict):
            # Iterate over each nested condition
            for nested_condition, nested_action_map in action.items():
                # Evaluate the nested condition with the sample data
                nested_condition_result = nested_condition(data)
                # Get the corresponding action based on the nested condition result
                nested_action = nested_action_map[nested_condition_result]
                # Print the condition, condition result, action description, and action value
                print(f"Condition: {nested_condition.__name__}, Condition Result: {nested_condition_result}, Action: {nested_action}")
        else:
            # Print the condition, condition result, action description, and action value
            print(f"Condition: {condition.__name__}, Condition Result: {condition_result}, Action: {action}")


# Call the test function
test_action_mapping()
