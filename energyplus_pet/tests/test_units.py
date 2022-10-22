from typing import Union
from unittest import TestCase

from energyplus_pet.exceptions import EnergyPlusPetException
from energyplus_pet.units import (
    PowerValue, FlowValue, TemperatureValue, PressureValue, LengthValue, RotationSpeedValue,
    unit_class_factory, unit_instance_factory, UnitType, DimensionlessValue
)


class TestLayer(TestCase):

    def setUp(self) -> None:
        self.unit_type: Union[UnitType, None] = None

    def set_unit_type(self, unit_type: UnitType):
        self.unit_type = unit_type

    def worker_construction(self, value: float, unit_id: str):
        if self.unit_type is None:  # pragma: no cover, should never get here, fix the unit test
            self.fail("Forgot to call set_unit_type before calling worker_construction")
        unit = unit_class_factory(self.unit_type)
        # verify the interface, not needing an instance of a unit value yet
        gotten_units = unit.get_unit_ids()
        self.assertIsInstance(gotten_units, list)
        gotten_unit_string_map = unit.get_unit_string_map()
        for gu in gotten_units:
            self.assertIsInstance(gu, str)
            self.assertIsInstance(gotten_unit_string_map[gu], str)
        self.assertIsInstance(unit.calculation_unit_id(), str)
        self.assertIsInstance(unit.base_ip_unit_id(), str)
        self.assertIsInstance(unit.base_si_unit(), str)
        # then verify an actual instance
        unit_value_instance = unit(value, "dummy name", "dummy description", unit_id)
        self.assertIsInstance(str(unit_value_instance), str)  # just verifies the __str__ function returns a string
        self.assertEqual(value, unit_value_instance.value)
        self.assertEqual(unit_id, unit_value_instance.units)
        self.assertEqual(self.unit_type, unit_value_instance.get_unit_type())
        calculation_unit_id = unit.calculation_unit_id()
        calculation_unit_string = unit.get_unit_string_map()[calculation_unit_id]
        looked_up_id = unit.get_id_from_unit_string(calculation_unit_string)
        self.assertEqual(looked_up_id, calculation_unit_id)
        with self.assertRaises(EnergyPlusPetException):
            unit.get_id_from_unit_string('MADE UP STRING')

    def worker_conversion(self, init_val: float, init_unit_id: str, expected_val: float, places: int):
        if self.unit_type is None:  # pragma: no cover, should never get here, fix the unit test
            self.fail("Forgot to call set_unit_type before calling worker_conversion")
        unit = unit_class_factory(self.unit_type)
        u = unit(init_val, "dummy name", "dummy description", init_unit_id)
        u.convert_to_calculation_unit()
        self.assertAlmostEqual(expected_val, u.value, places)
        self.assertEqual(u.calculation_unit_id(), u.units)


class TestMisc(TestLayer):
    def test_bad_unit_id(self):
        # ensure bad units raises an exception
        with self.assertRaises(EnergyPlusPetException):
            LengthValue(0.0, 'n', 'd', PowerValue.Kilowatts)


class TestPowerUnits(TestLayer):
    def test_power_units(self):
        self.set_unit_type(UnitType.Power)
        self.worker_construction(1.0, PowerValue.Kilowatts)
        self.worker_conversion(1.0, PowerValue.Kilowatts, 1.0, 6)
        self.worker_conversion(1.0, PowerValue.Watts, 0.001, 6)
        self.worker_conversion(1.0, PowerValue.BTU_hour, 0.00029308, 8)
        self.worker_conversion(1.0, PowerValue.MBTU_hour, 0.29308, 5)


class TestFlowUnits(TestLayer):
    def test_flow_units(self):
        self.set_unit_type(UnitType.Flow)
        self.worker_construction(1.0, FlowValue.M3S)
        self.worker_conversion(1.0, FlowValue.M3S, 1.0, 6)
        self.worker_conversion(1.0, FlowValue.CFM, 0.0004719, 6)
        self.worker_conversion(1.0, FlowValue.GPM, 0.00006309, 8)


class TestTemperatureUnits(TestLayer):
    def test_temperature_units(self):
        self.set_unit_type(UnitType.Temperature)
        self.worker_construction(1.0, TemperatureValue.C)
        self.worker_conversion(1.0, TemperatureValue.C, 1.0, 6)
        self.worker_conversion(1.0, TemperatureValue.F, -17.2222, 4)
        self.worker_conversion(1.0, TemperatureValue.K, -272.15, 5)


class TestPressureUnits(TestLayer):
    def test_pressure_units(self):
        self.set_unit_type(UnitType.Pressure)
        self.worker_construction(1.0, PressureValue.Pa)
        self.worker_conversion(1.0, PressureValue.Pa, 1.0, 6)
        self.worker_conversion(1.0, PressureValue.KPa, 1000.0, 4)
        self.worker_conversion(1.0, PressureValue.Atm, 101325.0, 6)
        self.worker_conversion(1.0, PressureValue.PSI, 6894.757, 7)


class TestLengthUnits(TestLayer):
    def test_length_units(self):
        self.set_unit_type(UnitType.Length)
        self.worker_construction(1.0, LengthValue.Meters)
        self.worker_conversion(1.0, LengthValue.Meters, 1.0, 6)
        self.worker_conversion(1.0, LengthValue.Feet, 0.3048, 4)
        self.worker_conversion(1.0, LengthValue.Inches, 0.0254, 4)
        self.worker_conversion(1.0, LengthValue.Centimeters, 0.01, 2)
        self.worker_conversion(1.0, LengthValue.Millimeters, 0.001, 3)


class TestRotationSpeedUnits(TestLayer):
    def test_rotation_speed_units(self):
        self.set_unit_type(UnitType.RotationalSpeed)
        self.worker_construction(1.0, RotationSpeedValue.RevsPerSecond)
        self.worker_conversion(1.0, RotationSpeedValue.RevsPerSecond, 1.0, 6)
        self.worker_conversion(1.0, RotationSpeedValue.RevsPerMinute, 0.01666, 4)
        self.worker_conversion(1.0, RotationSpeedValue.RadiansPerSecond, 0.159154, 4)


class TestDimensionlessUnits(TestLayer):
    def test_dimensionless_units(self):
        self.set_unit_type(UnitType.Dimensionless)
        self.worker_construction(1.0, DimensionlessValue.Dimensionless)
        self.worker_conversion(1.0, DimensionlessValue.Dimensionless, 1.0, 6)


class TestUnitFactory(TestCase):
    def test_all_types(self):
        self.assertIsInstance(unit_instance_factory(0.0, UnitType.Power), PowerValue)
        self.assertIsInstance(unit_instance_factory(0.0, UnitType.Flow), FlowValue)
        self.assertIsInstance(unit_instance_factory(0.0, UnitType.Temperature), TemperatureValue)
        self.assertIsInstance(unit_instance_factory(0.0, UnitType.Dimensionless), DimensionlessValue)
        self.assertIsInstance(unit_instance_factory(0.0, UnitType.Pressure), PressureValue)
        self.assertIsInstance(unit_instance_factory(0.0, UnitType.Length), LengthValue)
        self.assertIsInstance(unit_instance_factory(0.0, UnitType.RotationalSpeed), RotationSpeedValue)
        with self.assertRaises(EnergyPlusPetException):
            # noinspection PyTypeChecker
            unit_instance_factory(0.0, 42828)  # purposefully passing an invalid unit type here
