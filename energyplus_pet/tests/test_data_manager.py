from unittest import TestCase

from energyplus_pet.correction_factor import CorrectionFactor, CorrectionFactorType
from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.wahp_heating_curve import WaterToAirHeatPumpHeatingCurveFit


class TestDataManager(TestCase):

    def test_reset(self):
        cdm = CatalogDataManager()
        cf = CorrectionFactor('foo')
        cf.num_corrections = 0
        cdm.add_correction_factor(cf)
        cdm.add_base_data([[]])
        cdm.apply_correction_factors(0, -1, -1)
        self.assertTrue(cdm.data_processed)
        cdm.reset()
        self.assertFalse(cdm.data_processed)

    def test_empty_base_data(self):
        cdm = CatalogDataManager()
        # cf = CorrectionFactor('blah')
        # cdm.add_correction_factor(cf)
        # cdm.add_base_data([])
        status = cdm.apply_correction_factors(0, -1, -1)
        self.assertEqual(status, CatalogDataManager.ProcessResult.ERROR)
        cdm.reset()

    def test_final_data_with_fixed_column(self):
        cdm = CatalogDataManager()
        cdm.add_base_data([
            [0, 1, 2, 3],
            [0, 2, 3, 4],
            [0, 3, 4, 5]
        ])
        status = cdm.apply_correction_factors(3, -1, -1)
        self.assertEqual(status, CatalogDataManager.ProcessResult.ERROR)
        cdm.reset()

    def test_process_some_base_data(self):
        cdm = CatalogDataManager()
        cdm.add_base_data([
            [0, 1, 2, 3],
            [1, 2, 3, 4],
            [2, 3, 4, 5]
        ])
        status = cdm.apply_correction_factors(0, -1, -1)
        self.assertEqual(status, CatalogDataManager.ProcessResult.OK)
        self.assertEqual(3, len(cdm.final_data_matrix))
        self.assertIsInstance(cdm.summary(), dict)

    def test_process_not_enough_data(self):
        cdm = CatalogDataManager()
        cdm.add_base_data([
            [0, 1, 2, 3],
            [1, 2, 3, 4],
            [2, 3, 4, 5]
        ])
        self.assertEqual(CatalogDataManager.ProcessResult.ERROR, cdm.apply_correction_factors(4, -1, -1))

    def test_process_with_multiplier_factor(self):
        cdm = CatalogDataManager()
        cf = CorrectionFactor('multi')
        cf.correction_type = CorrectionFactorType.Multiplier
        cf.num_corrections = 1
        cf.base_column_index = 0
        cf.base_correction = [2.0]
        cf.columns_to_modify = [1, 2, 3]
        cf.mod_correction_data_column_map = {
            1: [0.5],  # column 1 should be halved (zero index)
            2: [5.0],  # column 2 should be five-d
            3: [2.0]  # column 3 should be doubled
        }
        cdm.add_correction_factor(cf)
        cdm.add_base_data([
            [1.0, 2.0, 3.0, 4.0]
        ])
        status = cdm.apply_correction_factors(0, -1, -1)
        self.assertEqual(status, CatalogDataManager.ProcessResult.OK)
        self.assertEqual(
            [
                [1.0, 2.0, 3.0, 4.0],
                [2.0, 1.0, 15.0, 8.0]  # cf added row
            ],
            cdm.final_data_matrix
        )

    def test_process_with_wb_db_factor(self):
        cdm = CatalogDataManager()
        cf = CorrectionFactor('db_wb')
        cf.correction_type = CorrectionFactorType.CombinedDbWb
        cf.num_corrections = 1
        cf.base_correction_db = [2.0]
        cf.base_correction_wb = [3.0]
        cf.columns_to_modify = [2, 3]
        cf.mod_correction_data_column_map = {
            2: [5.0],  # column 2 should be five-d
            3: [2.0]  # column 3 should be doubled
        }
        cdm.add_correction_factor(cf)
        cdm.add_base_data([
            [1.0, 2.0, 3.0, 4.0]
        ])
        status = cdm.apply_correction_factors(0, 0, 1)
        self.assertEqual(status, CatalogDataManager.ProcessResult.OK)
        self.assertEqual(
            [
                [1.0, 2.0, 3.0, 4.0],
                [2.0, 3.0, 15.0, 8.0]  # cf added row
            ],
            cdm.final_data_matrix
        )

    def test_lots_of_correction_factors(self):
        cdm = CatalogDataManager()

        cf = CorrectionFactor('replacement_1')
        cf.correction_type = CorrectionFactorType.Replacement
        cf.num_corrections = 2
        cf.base_column_index = 0
        cf.base_correction = [0, 2]
        cf.columns_to_modify = [4, 5]
        cf.mod_correction_data_column_map = {4: [0.5, 1.2], 5: [0.4, 1.1]}
        cdm.add_correction_factor(cf)

        cf = CorrectionFactor('replacement_2')
        cf.correction_type = CorrectionFactorType.Replacement
        cf.num_corrections = 2
        cf.base_column_index = 2
        cf.base_correction = [0, 3]
        cf.columns_to_modify = [4, 5]
        cf.mod_correction_data_column_map = {4: [0.6, 1.3], 5: [0.5, 1.8]}
        cdm.add_correction_factor(cf)

        cf = CorrectionFactor('multiplier_1')
        cf.correction_type = CorrectionFactorType.Multiplier
        cf.num_corrections = 2
        cf.base_column_index = 1
        cf.base_correction = [0.5, 1.2]
        cf.columns_to_modify = [4, 5]
        cf.mod_correction_data_column_map = {4: [0.8, 1.1], 5: [0.3, 1.7]}
        cdm.add_correction_factor(cf)

        cf = CorrectionFactor('multiplier_2')
        cf.correction_type = CorrectionFactorType.Multiplier
        cf.num_corrections = 2
        cf.base_column_index = 3
        cf.base_correction = [0.4, 1.4]
        cf.columns_to_modify = [4, 5]
        cf.mod_correction_data_column_map = {4: [0.6, 1.2], 5: [0.4, 1.4]}
        cdm.add_correction_factor(cf)

        cdm.add_base_data([
            [1, 1, 1, 1, 200, 10]
        ])
        status = cdm.apply_correction_factors(0, -1, -1)
        self.assertEqual(status, CatalogDataManager.ProcessResult.OK)
        self.assertEqual(81, len(cdm.final_data_matrix))

        # test end to end
        eq = WaterToAirHeatPumpHeatingCurveFit()
        eq.set_required_constant_parameter(eq.rated_air_volume_flow_key, 1)
        eq.set_required_constant_parameter(eq.rated_water_volume_flow_key, 1)
        eq.set_required_constant_parameter(eq.rated_heating_capacity_key, 10)
        eq.set_required_constant_parameter(eq.rated_heating_power_key, 1)
        eq.generate_parameters(cdm, lambda *_: None, lambda *_: None)
        # These coefficients were generated by manually expanding the base data row with all the correction
        #  factors and running the manually generated dataset using this tool.
        # This isn't strictly necessary in this unit test, which is primarily just testing that the data manager
        #  is properly applying correction factors, but it provides a nice end-to-end check.
        expected = [-2660.7247, 1018.2073, 1728.6412, 10.1805, 6.8708]
        calculated = eq.heating_capacity_params
        # since the expected values have 4 decimal places, it is reasonable to compare to 3 decimal places
        [self.assertAlmostEqual(e, c, 3) for e, c in zip(expected, calculated)]
        # since one of these expected has only 3 decimal places, then we need to compare to 2 decimal places
        expected = [-1914.568, 943.8333, 1017.4521, 9.1667, 16.1239]
        calculated = eq.heating_power_params
        [self.assertAlmostEqual(e, c, 2) for e, c in zip(expected, calculated)]
