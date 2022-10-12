from typing import Type
from unittest import TestCase

from energyplus_pet.units import PowerUnits, FlowUnits, TempUnits, PressureUnits, LengthUnits, RotationSpeedUnits


def worker_construction(test_class: TestCase, unit_type: Type, value: float, unit: int):
    u = unit_type(value, unit)
    # verifies the interface
    gotten_units = u.get_units()
    test_class.assertIsInstance(gotten_units, list)
    for gu in gotten_units:
        test_class.assertIsInstance(gu, int)
    gotten_strings = u.get_unit_strings()
    for gs in gotten_strings:
        test_class.assertIsInstance(gs, str)
    test_class.assertIsInstance(u.calculation_unit(), int)
    test_class.assertIsInstance(u.base_ip_unit(), int)
    test_class.assertIsInstance(u.base_si_unit(), int)
    # verifies construction and members are set up properly
    test_class.assertEqual(value, u.value)
    test_class.assertEqual(unit, u.units)


def worker_conversion(
        test_cls: TestCase, unit_type: Type, init_val: float, init_units: int, expected_val: float, places: int
):
    u = unit_type(init_val, init_units)
    u.convert_to_calculation_unit()
    test_cls.assertAlmostEqual(expected_val, u.value, places)
    test_cls.assertEqual(u.calculation_unit(), u.units)


class TestPowerUnits(TestCase):
    def test_power_units(self):
        unit_type = PowerUnits
        worker_construction(self, unit_type, 1.0, unit_type.Kilowatts)
        worker_conversion(self, unit_type, 1.0, unit_type.Kilowatts, 1.0, 6)
        worker_conversion(self, unit_type, 1.0, unit_type.Watts, 0.001, 6)
        worker_conversion(self, unit_type, 1.0, unit_type.BTU_hour, 0.00029308, 8)
        worker_conversion(self, unit_type, 1.0, unit_type.MBTU_hour, 0.29308, 5)


class TestFlowUnits(TestCase):
    def test_flow_units(self):
        unit_type = FlowUnits
        worker_construction(self, unit_type, 1.0, unit_type.M3S)
        worker_conversion(self, unit_type, 1.0, unit_type.M3S, 1.0, 6)
        worker_conversion(self, unit_type, 1.0, unit_type.CFM, 0.0004719, 6)
        worker_conversion(self, unit_type, 1.0, unit_type.GPM, 0.00006309, 8)


class TestTemperatureUnits(TestCase):
    def test_temperature_units(self):
        unit_type = TempUnits
        worker_construction(self, unit_type, 1.0, unit_type.C)
        worker_conversion(self, unit_type, 1.0, unit_type.C, 1.0, 6)
        worker_conversion(self, unit_type, 1.0, unit_type.F, -17.2222, 4)
        worker_conversion(self, unit_type, 1.0, unit_type.K, -272.15, 5)


class TestPressureUnits(TestCase):
    def test_pressure_units(self):
        unit_type = PressureUnits
        worker_construction(self, unit_type, 1.0, unit_type.Pa)
        worker_conversion(self, unit_type, 1.0, unit_type.Pa, 1.0, 6)
        worker_conversion(self, unit_type, 1.0, unit_type.KPa, 1000.0, 4)
        worker_conversion(self, unit_type, 1.0, unit_type.Atm, 101325.0, 6)
        worker_conversion(self, unit_type, 1.0, unit_type.PSI, 6894.757, 7)


class TestLengthUnits(TestCase):
    def test_length_units(self):
        unit_type = LengthUnits
        worker_construction(self, unit_type, 1.0, unit_type.Meters)
        worker_conversion(self, unit_type, 1.0, unit_type.Meters, 1.0, 6)
        worker_conversion(self, unit_type, 1.0, unit_type.Feet, 0.3048, 4)
        worker_conversion(self, unit_type, 1.0, unit_type.Inches, 0.0254, 4)
        worker_conversion(self, unit_type, 1.0, unit_type.Centimeters, 0.01, 2)
        worker_conversion(self, unit_type, 1.0, unit_type.Millimeters, 0.001, 3)


class TestRotationSpeedUnits(TestCase):
    def test_rotation_speed_units(self):
        unit_type = RotationSpeedUnits
        worker_construction(self, unit_type, 1.0, unit_type.RevsPerSecond)
        worker_conversion(self, unit_type, 1.0, unit_type.RevsPerSecond, 1.0, 6)
        worker_conversion(self, unit_type, 1.0, unit_type.RevsPerMinute, 0.01666, 4)
        worker_conversion(self, unit_type, 1.0, unit_type.RadiansPerSecond, 0.159154, 4)
