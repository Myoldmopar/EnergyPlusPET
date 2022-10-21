from unittest import TestCase

from energyplus_pet.correction_factor import CorrectionFactor


class TestCorrectionFactor(TestCase):
    def test_correction_factor(self):
        # The CF class is really just a minimal data holder, no need to exhaustively test much, just verify interface
        cf = CorrectionFactor('foo')
        self.assertIsInstance(cf.describe(), str)
        # verify the columns_to_modify property is updating the map size properly
        self.assertEqual(0, len(cf.columns_to_modify))
        cf.columns_to_modify = [1, 2, 3]
        self.assertEqual(3, len(cf.columns_to_modify))
        self.assertEqual(3, len(cf.mod_correction_data_column_map))
