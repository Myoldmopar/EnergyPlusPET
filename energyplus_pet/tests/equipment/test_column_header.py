from unittest import TestCase

from energyplus_pet.equipment.column_header import ColumnHeader, ColumnHeaderArray
from energyplus_pet.units import UnitType


class TestColumnHeaderArray(TestCase):
    def test_interface(self):
        array = ColumnHeaderArray([
            ColumnHeader("db", UnitType.Temperature, True),
            ColumnHeader("wb", UnitType.Temperature, False, True),
            ColumnHeader("flow", UnitType.Flow),
            ColumnHeader("q", UnitType.Power),
        ])
        self.assertEqual(
            [UnitType.Temperature, UnitType.Temperature, UnitType.Flow, UnitType.Power], array.unit_array()
        )
        self.assertEqual(
            ["db", "wb", "flow", "q"], array.name_array()
        )
        self.assertIsInstance(array.get_descriptive_summary(), str)
        self.assertIsInstance(array.get_descriptive_csv(), str)
        self.assertEqual(0, array.get_db_column())
        self.assertEqual(1, array.get_wb_column())
        self.assertIsInstance(len(array), int)  # ensures that __len__ works

    def test_missing_db_wb(self):
        array = ColumnHeaderArray([])
        self.assertEqual(-1, array.get_db_column())
        self.assertEqual(-1, array.get_wb_column())
