from typing import Type, Union
from unittest import TestCase

from energyplus_pet.units import PowerUnits, FlowUnits, TempUnits, PressureUnits, LengthUnits, RotationSpeedUnits


class TestLayer(TestCase):

    def setUp(self) -> None:
        self.unit_type: Union[Type, None] = None

    def set_unit_type(self, unit_type: Type):
        self.unit_type = unit_type

    def worker_construction(self, value: float, unit: int):
        if self.unit_type is None:
            self.fail("Forgot to call set_unit_type before calling worker_construction")
        u = self.unit_type(value, unit)
        # verifies the interface
        gotten_units = u.get_units()
        self.assertIsInstance(gotten_units, list)
        for gu in gotten_units:
            self.assertIsInstance(gu, int)
        gotten_strings = u.get_unit_strings()
        for gs in gotten_strings:
            self.assertIsInstance(gs, str)
        self.assertIsInstance(u.calculation_unit(), int)
        self.assertIsInstance(u.base_ip_unit(), int)
        self.assertIsInstance(u.base_si_unit(), int)
        # verifies construction and members are set up properly
        self.assertEqual(value, u.value)
        self.assertEqual(unit, u.units)

    def worker_conversion(self, init_val: float, init_units: int, expected_val: float, places: int):
        if self.unit_type is None:
            self.fail("Forgot to call set_unit_type before calling worker_conversion")
        u = self.unit_type(init_val, init_units)
        u.convert_to_calculation_unit()
        self.assertAlmostEqual(expected_val, u.value, places)
        self.assertEqual(u.calculation_unit(), u.units)


class TestPowerUnits(TestLayer):
    def test_power_units(self):
        unit_type = PowerUnits
        self.set_unit_type(unit_type)
        self.worker_construction(1.0, unit_type.Kilowatts)
        self.worker_conversion(1.0, unit_type.Kilowatts, 1.0, 6)
        self.worker_conversion(1.0, unit_type.Watts, 0.001, 6)
        self.worker_conversion(1.0, unit_type.BTU_hour, 0.00029308, 8)
        self.worker_conversion(1.0, unit_type.MBTU_hour, 0.29308, 5)


class TestFlowUnits(TestLayer):
    def test_flow_units(self):
        unit_type = FlowUnits
        self.set_unit_type(unit_type)
        self.worker_construction(1.0, unit_type.M3S)
        self.worker_conversion(1.0, unit_type.M3S, 1.0, 6)
        self.worker_conversion(1.0, unit_type.CFM, 0.0004719, 6)
        self.worker_conversion(1.0, unit_type.GPM, 0.00006309, 8)


class TestTemperatureUnits(TestLayer):
    def test_temperature_units(self):
        unit_type = TempUnits
        self.set_unit_type(unit_type)
        self.worker_construction(1.0, unit_type.C)
        self.worker_conversion(1.0, unit_type.C, 1.0, 6)
        self.worker_conversion(1.0, unit_type.F, -17.2222, 4)
        self.worker_conversion(1.0, unit_type.K, -272.15, 5)


class TestPressureUnits(TestLayer):
    def test_pressure_units(self):
        unit_type = PressureUnits
        self.set_unit_type(unit_type)
        self.worker_construction(1.0, unit_type.Pa)
        self.worker_conversion(1.0, unit_type.Pa, 1.0, 6)
        self.worker_conversion(1.0, unit_type.KPa, 1000.0, 4)
        self.worker_conversion(1.0, unit_type.Atm, 101325.0, 6)
        self.worker_conversion(1.0, unit_type.PSI, 6894.757, 7)


class TestLengthUnits(TestLayer):
    def test_length_units(self):
        unit_type = LengthUnits
        self.set_unit_type(unit_type)
        self.worker_construction(1.0, unit_type.Meters)
        self.worker_conversion(1.0, unit_type.Meters, 1.0, 6)
        self.worker_conversion(1.0, unit_type.Feet, 0.3048, 4)
        self.worker_conversion(1.0, unit_type.Inches, 0.0254, 4)
        self.worker_conversion(1.0, unit_type.Centimeters, 0.01, 2)
        self.worker_conversion(1.0, unit_type.Millimeters, 0.001, 3)


class TestRotationSpeedUnits(TestLayer):
    def test_rotation_speed_units(self):
        unit_type = RotationSpeedUnits
        self.set_unit_type(unit_type)
        self.worker_conversion(1.0, unit_type.RevsPerSecond, 1.0, 6)
        self.worker_conversion(1.0, unit_type.RevsPerMinute, 0.01666, 4)
        self.worker_conversion(1.0, unit_type.RadiansPerSecond, 0.159154, 4)
