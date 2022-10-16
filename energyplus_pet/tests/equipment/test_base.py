from unittest import TestCase

from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.base import BaseEquipment


class TestBaseEquipmentFunctions(TestCase):
    def test_a(self):
        eq = BaseEquipment()
        self.assertEqual(eq.this_type(), EquipType.InvalidType)
        form = """Object,
{0},{1}!-Field1
{2};{3}!-Field2"""
        values = ['value_a', 'value_b']
        expected = """Object,
    value_a,         !-Field1
    value_b;         !-Field2"""
        output = eq.fill_eplus_object_format(values, form)
        self.assertEqual(expected, output)
