from unittest import TestCase

from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.units import BaseUnit
from energyplus_pet.equipment.column_header import ColumnHeaderArray
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.wwhp_heating_curve import WaterToWaterHeatPumpHeatingCurveFit


class TestWWHPHeatingCurve(TestCase):
    def test_interface(self):
        eq = WaterToWaterHeatPumpHeatingCurveFit()
        self.assertEqual(eq.this_type(), EquipType.WWHP_Heating_CurveFit)
        self.assertIsInstance(eq.name(), str)
        self.assertIsInstance(eq.headers(), ColumnHeaderArray)
        for param in eq.required_constant_parameters():
            self.assertIsInstance(param, BaseUnit)
        for output in [eq.to_eplus_idf_object(), eq.to_parameter_summary(), eq.to_eplus_epjson_object()]:
            self.assertIsInstance(output, str)
        self.assertIsNone(eq.generate_absolute_plot())
        self.assertIsNone(eq.generate_error_plot())

    def test_generated_parameters(self):
        eq = WaterToWaterHeatPumpHeatingCurveFit()
        cdm = CatalogDataManager()
        eq.generate_parameters(cdm, lambda *_: None, lambda *_: None, lambda *_: None)

    def test_output_forms(self):
        pass
