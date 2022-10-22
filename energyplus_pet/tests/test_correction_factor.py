from unittest import TestCase

from energyplus_pet.correction_factor import CorrectionFactor, CorrectionFactorType


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

    def test_check_ok(self):
        # TODO: Use this function in the correction factor data form prior to continuing the wizard
        cf = CorrectionFactor('foo')
        cf.columns_to_modify = [1, 2]

        # test zero correction rows
        cf.num_corrections = 0
        self.assertFalse(cf.check_ok())
        cf.num_corrections = 1
        # test invalid correction type
        cf.correction_type = 0
        self.assertFalse(cf.check_ok())
        cf.correction_type = CorrectionFactorType.Multiplier
        # test out of bounds base column index
        cf.base_column_index = -1
        self.assertFalse(cf.check_ok())
        cf.base_column_index = 0
        # test base column index exists in mod columns
        cf.base_column_index = 1
        self.assertFalse(cf.check_ok())
        cf.base_column_index = 0
        # test invalid length of corrections
        cf.base_correction = [0, 1, 2]
        self.assertFalse(cf.check_ok())
        cf.base_correction = [1.5]
        # test misshapen mod correction data map
        cf.mod_correction_data_column_map = {0: [1]}
        self.assertFalse(cf.check_ok())
        # test missing column (1) of data in mod map
        cf.mod_correction_data_column_map = {0: [1.1], 2: [3.1]}
        self.assertFalse(cf.check_ok())
        # test bad size of a mod data column
        cf.mod_correction_data_column_map = {1: [1.1], 2: [3.1, 2.1]}
        self.assertFalse(cf.check_ok())
        # now test it is all good!
        cf.mod_correction_data_column_map = {1: [1.1], 2: [3.1]}
        self.assertTrue(cf.check_ok())
