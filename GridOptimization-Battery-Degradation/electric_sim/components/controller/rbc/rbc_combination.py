# action_handler.py

class Rule(object):
    def __init__(self, condition, action):
        self.condition = condition
        self.action = action

class RuleEngine(object):
    def __init__(self, rules):
        self.rules = rules

    def execute(self, data):
        actions = []
        for rule in self.rules:
            if rule.condition(data):
                actions.append(rule.action(data))
        return actions

class ActionHandler:
    def __init__(self, simulation):
        self.simulation = simulation

        # Define your conditions based on the control scheme
        self.conditions = {
            'condition1': lambda data: data['PV_Power'] > 0 and (data['SH'] or data['DHW']) > 0,
            'condition2': lambda data: data['PV_Power'] > 0 and not (data['SH'] or data['DHW']) > 0,
            'condition3': lambda data: data['TES_SOC'] < data['SOCmax'],
            'condition4': lambda data: data['Batt_SOC'] < data['SOCmax'],
            'condition5': lambda data: data['T_out'] < data['T_out_limit'],
            'condition6': lambda data: data['PV_Power'] >= data['HP_Power'],
            'condition7': lambda data: data['TES_SOC'] > data['SOCmin'],
            'condition8': lambda data: data['Batt_SOC'] > data['SOCmin']
        }

        # Define your actions based on the control scheme
        self.actions = [
            self.action1,
            self.action2,
            self.action3
        ]

        # Define your rules
        self.rules = [Rule(self.conditions[condition], action) for condition, action in zip(self.conditions, self.actions)]

        # Create a RuleEngine instance
        self.rule_engine = RuleEngine(self.rules)

    def execute(self, data):
        actions = self.rule_engine.execute(data)
        for action, value in actions:
            self.simulation.control_dict[action] = value

    # Define your actions
    #todo: implement heating rod as secon possibility and think about how to handle the setpoints
    def action1(self):
        if self.conditions['condition1']:
            if self.conditions['condition6']:
                self.simulation.control_dict.update(
                    {"heat_pump": self.simulation.heat_pump.nom_power_kw, "tank": self.simulation.heat_pump.p_thermal})
                return self.simulation.control_dict
            elif self.conditions['condition5']:
                self.simulation.control_dict.update(
                    {"heat_pump": self.simulation.heat_pump.nom_power_kw, "tank": self.simulation.heat_pump.p_thermal})
            else:
                return self.simulation.control_dict.update(
                    {"heat_pump": 0, "tank": self.simulation.heat_pump.p_thermal})
        return self.simulation.control_dict.update(
                    {"heat_pump": 0, "tank": 0})

    def action2(self):
        if self.conditions['condition2']:
            if self.conditions['condition3']:
                if self.conditions['condition5']:
                    return ("HP_on + charge_TES_from_PV + charge Batt if possible", 5.0)
                else:
                    return ("EH_on + charge_TES_from_PV_or_grid", 5.0)
            elif self.conditions['condition4']:
                return ("charge Batt if possible", 5.0)
            else:
                return ("Feed Grid", 5.0)
        return self.simulation.control_dict.update(
                    {"heat_pump": 0, "tank": 0})

    def action3(self):
        if not self.conditions['condition2']:
            if self.conditions['condition7']:
                return ("Discharge TES", 5.0)
            elif self.conditions['condition8']:
                if self.conditions['condition5']:
                    return ("EH_on + charge_TES_from_Battery", 5.0)
                else:
                    return ("HP_on + charge_TES_Battery", 5.0)
            else:
                if self.conditions['condition5']:
                    return ("EH_on + charge_TES_from_Grid", 5.0)
                else:
                    return ("HP_on + charge_TES_from_Grid", 5.0)
        return self.simulation.control_dict.update(
                    {"heat_pump": 0, "tank": 0})



def test_action_handler():
    # Define a mock simulation object with the necessary attributes for the handlers
    class MockSimulation:
        def __init__(self):
            self.control_dict = {}

    # Create an instance of the ActionHandler with the mock simulation
    action_handler = ActionHandler(MockSimulation())

    # Define a list of mock data objects for the conditions
    data_values = [
        {
            'PV_Power': 10,
            'SH': True,
            'DHW': False,
            'TES_SOC': 0.5,
            'SOCmax': 1.0,
            'T_out': 15,
            'T_out_limit': 10
        },
        {
            'PV_Power': 20,
            'SH': False,
            'DHW': True,
            'TES_SOC': 0.7,
            'SOCmax': 1.0,
            'T_out': 10,
            'T_out_limit': 15
        },
        # ... add more data dictionaries for additional tests ...
    ]

    # Execute the action handler with each mock data object
    for data in data_values:
        action_handler.execute(data, 5.0)

        # Check that the control_dict was updated correctly
        assert action_handler.simulation.control_dict["HP_on + charge_TES_from_PV + charge Batt if possible"] == 5.0
        assert action_handler.simulation.control_dict["EH_on + charge_TES_from_PV_or_grid"] == 5.0
        assert action_handler.simulation.control_dict["charge Batt if possible"] == 5.0
        # ... add more assertions for other actions ...


