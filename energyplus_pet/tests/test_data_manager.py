from unittest import TestCase

from energyplus_pet.correction_factor import CorrectionFactor
from energyplus_pet.data_manager import CatalogDataManager


class TestDataManager(TestCase):
    def test_nearly_empty_success(self):
        cdm = CatalogDataManager()
        cf = CorrectionFactor('blah')
        cdm.add_correction_factor(cf)
        cdm.add_base_data([[0.0]])
        status, message = cdm.process()
        self.assertEqual(status, CatalogDataManager.ProcessResult.OK)
        self.assertIsInstance(message, str)
        cdm.reset()
