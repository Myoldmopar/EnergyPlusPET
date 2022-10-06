from unittest import TestCase

from energyplus_pet.utility import add


class TestUtilityAdd(TestCase):

    def test_add(self):
        self.assertEqual(3, add(1, 2))
