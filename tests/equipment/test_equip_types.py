from unittest import TestCase

from energyplus_pet.equipment.equip_types import EquipType, EquipTypeUniqueStrings


class TestEquipTypeUniqueStrings(TestCase):
    def test_a(self):
        all_strings = (
            EquipTypeUniqueStrings.InvalidType,
            EquipTypeUniqueStrings.WAHP_Heating_CurveFit,
            EquipTypeUniqueStrings.WAHP_Heating_PE,
            EquipTypeUniqueStrings.WAHP_Cooling_CurveFit,
            EquipTypeUniqueStrings.WAHP_Cooling_PE,
            EquipTypeUniqueStrings.WWHP_Heating_CurveFit,
            EquipTypeUniqueStrings.WWHP_Cooling_CurveFit,
            EquipTypeUniqueStrings.Pump_ConstSpeed_ND,
        )
        for string in all_strings:
            self.assertIsInstance(EquipTypeUniqueStrings.get_equip_type_from_unique_string(string), EquipType)
