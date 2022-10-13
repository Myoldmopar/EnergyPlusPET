from tkinter import Tk
from unittest import TestCase

from energyplus_pet.correction_factor import CorrectionFactor


class TestCorrectionFactor(TestCase):

    def setUp(self) -> None:
        self.root_tk = Tk()

    def test_correction_factor_a(self):
        c = CorrectionFactor(name="My Correction")
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
