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
