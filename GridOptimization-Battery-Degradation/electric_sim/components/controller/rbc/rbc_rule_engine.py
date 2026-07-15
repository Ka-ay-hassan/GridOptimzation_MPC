class Rule(object):
    def __init__(self, condition, action):
        self.condition = condition
        self.action = action

class RuleEngine(object):
    def __init__(self, rules, simulation):
        self.rules = rules
        self.simulation = simulation

    def execute(self, data):
        actions = []
        for rule in self.rules:
            if rule.condition(data):
                actions.append(rule.action(data))
        return actions

# Define your conditions and actions based on the control scheme
def condition1(data):
    return data['PV_Power'] > 0 and (data['SH'] or data['DHW'])

def action1(data):
    if data['TES_SOC'] < data['SOCmax']:
        if data['T_out'] > data['T_out_limit']:
            return ("HP_on + charge_TES_from_PV_Grid", 5.0)
        else:
            return ("EH_on + charge_TES_from_PV_Grid", 5.0)
    else:
        return ("No_charge_from_Batt_possible", True)

def condition2(data):
    return data['PV_Power'] > 0 and not (data['SH'] or data['DHW'])

def action2(data):
    if data['TES_SOC'] > data['SOCmin']:
        if data['Batt_SOC'] > data['SOCmax']:
            return ("No Action", True)
        else:
            return ("Charge Battery", True)
    elif 0 < data['TES_SOC'] < data['SOCmin']:
        if data['T_out'] > data['T_out_limit']:
            return ("HP_on + charge_TES_from_Battery", True)
        else:
            return ("EH_on + charge_TES_from_Battery", True)
    elif data['TES_SOC'] >= data['SOCmin']:
        if data['T_out'] > data['T_out_limit']:
        #if data['COP_HP'] > data['COP_EH']:
            return ("HP_on + charge_TES_from_Grid", True)
        else:
            return ("EH_on + charge_TES_from_Grid", True)

def condition3(data):
    return not (data['PV_Power'] > 0) and (data['SH'] or data['DHW'])

def action3(data):
    if data['TES_SOC'] < data['SOCmax']:
        return ("No Action", True)
    elif data['Batt_SOC'] < data['SOCmin'] and data['EH'] > data['Battery_Charge_Threshold'] and data['Grid_Feed'] > data['Max_Rate_Limit']:
        return ("Grid Feed In", True)
    elif data['T_out'] > data['T_out_limit'] and data['EH'] > data['Battery_Charge_Threshold'] and data['Grid_Feed'] > data['Max_Rate_Limit']:
        return ("Discharge TES", True)
