# Test function for the provided code
from components.controller.rbc.rbc_combination import *
def test_rule_engine_and_action_handler():
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

    # Create a RuleEngine instance
    rule_engine = RuleEngine(rules, simulation_instance)  # Pass the simulation instance to the RuleEngine

    # Create an ActionHandler instance
    action_handler = ActionHandler(simulation_instance)  # Pass the simulation instance to the ActionHandler

    # Execute the rule engine with the sample data
    actions = rule_engine.execute(data)

    # Execute the action handler with the actions
    for action, value in actions:
        action_handler.execute(action, value, None)

    print("Test passed!")

# Call the test function
test_rule_engine_and_action_handler()
