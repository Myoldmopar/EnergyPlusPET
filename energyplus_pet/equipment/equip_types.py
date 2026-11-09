from enum import Enum, auto


class EquipType(Enum):
    """Enumeration class of all known equipment types"""
    InvalidType = auto()  # used to return an invalid selection wherever needed
    WAHP_Heating_CurveFit = auto()
    WAHP_Heating_PE = auto()
    WAHP_Cooling_CurveFit = auto()
    WAHP_Cooling_PE = auto()
    WWHP_Heating_CurveFit = auto()
    WWHP_Cooling_CurveFit = auto()
    Pump_ConstSpeed_ND = auto()
    ASHP_Heating_CurveFit = auto()
    ASHP_Cooling_CurveFit = auto()
    AWHP_Heating_CurveFit = auto()
    AWHP_Cooling_CurveFit = auto()


class EquipTypeUniqueStrings:
    InvalidType = 'InvalidType'
    WAHP_Heating_CurveFit = 'WAHP_Heating_CurveFit'
    WAHP_Heating_PE = 'WAHP_Heating_PE'
    WAHP_Cooling_CurveFit = 'WAHP_Cooling_CurveFit'
    WAHP_Cooling_PE = 'WAHP_Cooling_PE'
    WWHP_Heating_CurveFit = 'WWHP_Heating_CurveFit'
    WWHP_Cooling_CurveFit = 'WWHP_Cooling_CurveFit'
    Pump_ConstSpeed_ND = 'Pump_ConstSpeed_ND'
    ASHP_Heating_CurveFit = 'ASHP_Heating_CurveFit'
    ASHP_Cooling_CurveFit = 'ASHP_Cooling_CurveFit'
    AWHP_Heating_CurveFit = 'AWHP_Heating_CurveFit'
    AWHP_Cooling_CurveFit = 'AWHP_Cooling_CurveFit'

    @staticmethod
    def get_equip_type_from_unique_string(equip_type_string) -> EquipType:
        if equip_type_string == EquipTypeUniqueStrings.InvalidType:
            return EquipType.InvalidType
        elif equip_type_string == EquipTypeUniqueStrings.WAHP_Heating_CurveFit:
            return EquipType.WAHP_Heating_CurveFit
        elif equip_type_string == EquipTypeUniqueStrings.WAHP_Heating_PE:
            return EquipType.WAHP_Heating_PE
        elif equip_type_string == EquipTypeUniqueStrings.WAHP_Cooling_CurveFit:
            return EquipType.WAHP_Cooling_CurveFit
        elif equip_type_string == EquipTypeUniqueStrings.WAHP_Cooling_PE:
            return EquipType.WAHP_Cooling_PE
        elif equip_type_string == EquipTypeUniqueStrings.WWHP_Heating_CurveFit:
            return EquipType.WWHP_Heating_CurveFit
        elif equip_type_string == EquipTypeUniqueStrings.WWHP_Cooling_CurveFit:
            return EquipType.WWHP_Cooling_CurveFit
        elif equip_type_string == EquipTypeUniqueStrings.Pump_ConstSpeed_ND:
            return EquipType.Pump_ConstSpeed_ND
        elif equip_type_string == EquipTypeUniqueStrings.ASHP_Heating_CurveFit:
            return EquipType.ASHP_Heating_CurveFit
        elif equip_type_string == EquipTypeUniqueStrings.ASHP_Cooling_CurveFit:
            return EquipType.ASHP_Cooling_CurveFit
        elif equip_type_string == EquipTypeUniqueStrings.AWHP_Heating_CurveFit:
            return EquipType.AWHP_Heating_CurveFit
        elif equip_type_string == EquipTypeUniqueStrings.AWHP_Cooling_CurveFit:
            return EquipType.AWHP_Cooling_CurveFit
