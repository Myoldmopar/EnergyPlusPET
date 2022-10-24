from unittest import TestCase

from energyplus_pet.equipment.manager import EquipmentFactory
from energyplus_pet.equipment.equip_types import EquipType


class TestEquipmentFactory(TestCase):
    def test_equipment_factory_function(self):
        # create a set of expressions based on whether we expect it to return None
        expected_outcome = {
            # change to assertIsNotNone as they are implemented
            EquipType.InvalidType: self.assertIsNone,
            EquipType.WAHP_Heating_CurveFit: self.assertIsNotNone,
            EquipType.WAHP_Heating_PE: self.assertIsNone,
            EquipType.WAHP_Cooling_CurveFit: self.assertIsNotNone,
            EquipType.WAHP_Cooling_PE: self.assertIsNone,
            EquipType.WWHP_Heating_CurveFit: self.assertIsNotNone,
            EquipType.WWHP_Cooling_CurveFit: self.assertIsNotNone,
            EquipType.Pump_ConstSpeed_ND: self.assertIsNone,
        }
        # make sure we have the full set of equipment in our list
        self.assertEqual(len(expected_outcome), len(list(EquipType)))
        # call
        for t, f in expected_outcome.items():
            f(EquipmentFactory.instance_factory(t))
