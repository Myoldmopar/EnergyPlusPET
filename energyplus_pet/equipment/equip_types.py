from enum import Enum, auto


class EquipType(Enum):
    InvalidType = auto()  # used to return an invalid selection wherever needed
    WAHP_Heating_CurveFit = auto()
    WAHP_Heating_PE = auto()
    WAHP_Cooling_CurveFit = auto()
    WAHP_Cooling_PE = auto()
    WWHP_Heating_CurveFit = auto()
    WWHP_Cooling_CurveFit = auto()
    Pump_ConstSpeed_ND = auto()



# class EquipType:
#     InvalidType = -1  # used to return an invalid selection wherever needed
#     WAHP_Heating_CurveFit = 0
#     WAHP_Heating_PE = 1
#     WAHP_Cooling_CurveFit = 2
#     WAHP_Cooling_PE = 3
#     WWHP_Heating_CurveFit = 4
#     WWHP_Cooling_CurveFit = 5
#     Pump_ConstSpeed_ND = 6
