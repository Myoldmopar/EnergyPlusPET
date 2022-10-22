from unittest import TestCase

from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.base import BaseEquipment


class TestBaseEquipmentFunctions(TestCase):
    def test_a(self):
        eq = BaseEquipment()
        self.assertEqual(eq.this_type(), EquipType.InvalidType)
        object_name = "Object"
        fields = [('Field1', 'value_a'), ('Field2', 'value_b')]
        expected = """Object,
    value_a,         !-Field1
    value_b;         !-Field2
"""
        output = eq.fill_eplus_object_format(object_name, fields)
        self.assertEqual(expected, output)
