from unittest import TestCase

from energyplus_pet.data_manager import CatalogDataManager


class TestDataManager(TestCase):
    def test_a(self):
        cdm = CatalogDataManager()
        cdm.add_correction_factor('blah')
        cdm.add_base_data('FooBar')
        self.assertIsInstance(cdm.process(), str)
        cdm.reset()
