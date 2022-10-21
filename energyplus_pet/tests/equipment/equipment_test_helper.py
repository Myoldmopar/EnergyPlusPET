from unittest import TestCase

from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.column_header import ColumnHeaderArray


class EquipmentTestHelper(TestCase):
    def check_interface(self, eq: BaseEquipment, expected_type: EquipType):
        self.assertEqual(eq.this_type(), expected_type)
        long_name = eq.name()
        self.assertIsInstance(long_name, str)
        self.assertNotIn('\n', long_name)
        short_name = eq.short_name()
        self.assertIsInstance(short_name, str)
        self.assertLessEqual(len(short_name), 32)
        self.assertNotIn('\n', short_name)
        headers = eq.headers()
        self.assertIsInstance(headers, ColumnHeaderArray)
        self.assertGreater(len(headers.columns), 1)
        for param in eq.get_required_constant_parameters():
            self.assertIsInstance(param, BaseEquipment.RequiredConstantParameter)
        for output in [eq.to_eplus_idf_object(), eq.to_parameter_summary(), eq.to_eplus_epjson_object()]:
            self.assertIsInstance(output, str)
        self.assertIsInstance(eq.get_absolute_plot_data(), tuple)
        self.assertIsInstance(eq.get_error_plot_data(), tuple)
        self.assertIsInstance(eq.get_extra_regression_metrics(), tuple)
        self.assertIsInstance(eq.get_number_of_progress_steps(), int)
        self.assertIsInstance(eq.minimum_data_points_for_generation(), int)
