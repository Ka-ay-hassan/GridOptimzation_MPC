from components.controller.rbc.rbc_rule_engine import *

def test_rule_engine():
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

    # Define the rules
    rules = [
        Rule(condition1, action1),
        Rule(condition2, action2),
        Rule(condition3, action3),
    ]

    # Create a RuleEngine instance
    rule_engine = RuleEngine(rules, None)

    # Execute the rule engine with the sample data
    actions = rule_engine.execute(data)

    # Print the conditions and actions
    for rule in rule_engine.rules:
        condition_result = rule.condition(data)
        print(f"Condition: {rule.condition.__name__}, Condition Result: {condition_result}")
        if condition_result:
            action = rule.action(data)
            print(f"Action: {action}")

# Call the test function
test_rule_engine()

