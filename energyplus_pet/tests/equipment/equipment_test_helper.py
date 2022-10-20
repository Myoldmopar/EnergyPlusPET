from unittest import TestCase

from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.column_header import ColumnHeaderArray
from energyplus_pet.units import BaseUnit


class EquipmentTestHelper(TestCase):
    def check_interface(self, eq: BaseEquipment, expected_type: EquipType):
        self.assertEqual(eq.this_type(), expected_type)
        self.assertIsInstance(eq.name(), str)
        self.assertIsInstance(eq.headers(), ColumnHeaderArray)
        for param in eq.required_constant_parameters():
            self.assertIsInstance(param, BaseUnit)
        for output in [eq.to_eplus_idf_object(), eq.to_parameter_summary(), eq.to_eplus_epjson_object()]:
            self.assertIsInstance(output, str)
        self.assertIsInstance(eq.get_absolute_plot_data(), tuple)
        self.assertIsInstance(eq.get_error_plot_data(), tuple)
