from unittest import TestCase

from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.correction_factor import CorrectionFactor
from energyplus_pet.equipment.wwhp_heating_curve import WaterToWaterHeatPumpHeatingCurveFit


class TestDataManager(TestCase):
    def test_a(self):
        cdm = CatalogDataManager()
        eq = WaterToWaterHeatPumpHeatingCurveFit()
        cdm.add_correction_factor(CorrectionFactor("blah", eq, lambda: None))
        cdm.add_base_data('FooBar')
        self.assertIsInstance(cdm.process(), str)
        cdm.reset()
