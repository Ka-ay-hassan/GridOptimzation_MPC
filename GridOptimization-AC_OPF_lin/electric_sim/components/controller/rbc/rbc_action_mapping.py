def condition1(data):
    return data['PV_Power'] > 0 and (data['SH'] or data['DHW']) and data['TES_SOC'] < data['SOCmax']

def condition1_nested(data):
    return data['T_out'] > data['T_out_limit']

def condition2(data):
    return data['PV_Power'] > 0 and not (data['SH'] or data['DHW']) and data['TES_SOC'] > data['SOCmin']

def condition2_nested1(data):
    return data['Batt_SOC'] > data['SOCmax']

def condition2_nested2(data):
    return 0 < data['TES_SOC'] < data['SOCmin']

def condition2_nested2_nested(data):
    return data['T_out'] > data['T_out_limit']

def condition3(data):
    return not (data['PV_Power'] > 0) and (data['SH'] or data['DHW']) and data['TES_SOC'] < data['SOCmax']

def condition3_nested1(data):
    return data['Batt_SOC'] < data['SOCmin'] and data['EH'] > data['Battery_Charge_Threshold'] and data['Grid_Feed'] > data['Max_Rate_Limit']

def condition3_nested2(data):
    return data['T_out'] > data['T_out_limit'] and data['EH'] > data['Battery_Charge_Threshold'] and data['Grid_Feed'] > data['Max_Rate_Limit']


# Define a dictionary to map conditions to actions
ACTION_MAPPING = {
    condition1: {
        True: ("HP_on + charge_TES_from_PV_Grid", 5.0),
        False: ("EH_on + charge_TES_from_PV_Grid", 5.0),
    },
    condition1_nested: {
        True: ("HP_on + charge_TES_from_PV_Grid", 5.0),
        False: ("EH_on + charge_TES_from_PV_Grid", 5.0),
    },
    condition2: {
        True: ("Charge Battery", True),
        False: {
            condition2_nested1: {
                True: ("HP_on + charge_TES_from_Battery", True),
                False: ("EH_on + charge_TES_from_Battery", True),
            },
            condition2_nested2: {
                True: ("HP_on + charge_TES_from_Grid", True),
                False: {
                    condition2_nested2_nested: {
                        True: ("HP_on + charge_TES_from_Grid", True),
                        False: ("EH_on + charge_TES_from_Grid", True),
                    }
                },
            },
        },
    },
    condition3: {
        True: ("Grid Feed In", True),
        False: {
            condition3_nested1: {
                True: ("Grid Feed In", True),
                False: ("Discharge TES", True),
            },
            condition3_nested2: {
                True: ("Grid Feed In", True),
                False: ("Discharge TES", True),
            },
        },
    },
}
