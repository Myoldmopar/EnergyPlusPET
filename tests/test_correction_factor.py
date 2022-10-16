from unittest import TestCase

from energyplus_pet.correction_factor import CorrectionFactor
from energyplus_pet.equipment.wwhp_heating_curve import WaterToWaterHeatPumpHeatingCurveFit


class TestCorrectionFactor(TestCase):

    def test_correction_factor_a(self):
        eq = WaterToWaterHeatPumpHeatingCurveFit()
        c = CorrectionFactor(name="My Correction", equipment_instance=eq, remove_callback=lambda: None)
        # verify description returns a string, no need to check contents
        self.assertIsInstance(c.description(), str)
        # check the flag for removal
        self.assertFalse(c.remove_me)
        c.remove()
        self.assertTrue(c.remove_me)
        # check the new flag
        self.assertTrue(c.is_new_or_blank)
        c.not_new_anymore()
        self.assertFalse(c.is_new_or_blank)
