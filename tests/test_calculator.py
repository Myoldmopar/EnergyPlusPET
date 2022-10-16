from unittest import TestCase

from energyplus_pet.calculator import ParameterCalculator
from energyplus_pet.data_manager import CatalogDataManager


class TestCalculator(TestCase):
    def test_a(self):
        cdm = CatalogDataManager()
        pc = ParameterCalculator(cdm)
        self.assertIsInstance(pc.output(), str)
