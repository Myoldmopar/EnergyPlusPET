from abc import abstractmethod
from collections import OrderedDict
from enum import Enum, auto
from typing import List, Type, OrderedDict as TypingOD

from energyplus_pet.exceptions import EnergyPlusPetException


class UnitType(Enum):
    Power = auto()
    Flow = auto()
    Temperature = auto()
    Dimensionless = auto()
    Pressure = auto()
    Length = auto()
    RotationalSpeed = auto()


class BaseValueWithUnit:
    """
    This class represents an abstract floating point value with units attached.
    In this library, if a component is trying to define an interface, for example, defining a header column, it should
    just use the UnitType enumeration, because there is no value associated with that column.
    This class is mostly just used while tabular forms are open to handle users entering data in various units and
    normalizing them before sending the properly formed data to the equipment processing routines.
    """

    def __init__(
            self, initial_value: float, name: str = "<Unnamed>", description: str = '<...>', initial_unit_id: str = None
    ):
        self.value = initial_value
        self.name = name
        self.description = description
        if initial_unit_id is not None:
            if initial_unit_id not in self.get_unit_ids():
                raise EnergyPlusPetException(
                    f"Invalid unit ID in unit constructor for class {self.__class__.__name__} = {initial_unit_id}"
                )
            self.units = initial_unit_id
        else:
            self.units = self.calculation_unit_id()

    @abstractmethod
    def get_unit_type(self) -> UnitType:  # pragma: no cover
        pass

    @staticmethod
    @abstractmethod
    def get_unit_ids() -> List[str]:  # pragma: no cover
        pass

    @staticmethod
    @abstractmethod
    def get_unit_string_map() -> TypingOD[str, str]:  # pragma: no cover
        pass

    @classmethod
    def get_id_from_unit_string(cls, current_units_string: str) -> str:
        """
        Looks up the ID of a unit for the current type given the unit string

        :param current_units_string: A string of units to search for, such as 'kg/s'
        :return: An internal string ID of the unit matching what comes from get_unit_ids()
        """
        for k, v in cls.get_unit_string_map().items():
            if v == current_units_string:
                return k
        raise EnergyPlusPetException(
            f"No ID for unit string: {current_units_string}; possible units = {cls.get_unit_string_map().values()}"
        )

    @staticmethod
    @abstractmethod
    def calculation_unit_id() -> str:  # pragma: no cover
        pass

    @staticmethod
    @abstractmethod
    def base_ip_unit_id() -> str:  # pragma: no cover
        pass

    @staticmethod
    @abstractmethod
    def base_si_unit() -> str:  # pragma: no cover
        pass

    @abstractmethod
    def convert_to_calculation_unit(self):  # pragma: no cover
        pass

    def __str__(self) -> str:
        return f"{self.value} [{self.get_unit_string_map()[self.units]}]"


class DimensionlessValue(BaseValueWithUnit):
    Dimensionless = __qualname__ + "-"

    def get_unit_type(self) -> UnitType:
        return UnitType.Dimensionless

    @staticmethod
    def get_unit_ids() -> List[str]:
        return [DimensionlessValue.Dimensionless]

    @staticmethod
    def get_unit_string_map() -> TypingOD[str, str]:
        od = OrderedDict()
        od[DimensionlessValue.Dimensionless] = "--"
        return od

    @staticmethod
    def calculation_unit_id() -> str:
        return DimensionlessValue.Dimensionless

    @staticmethod
    def base_ip_unit_id() -> str:
        return DimensionlessValue.Dimensionless

    @staticmethod
    def base_si_unit() -> str:
        return DimensionlessValue.Dimensionless

    def convert_to_calculation_unit(self):
        return


class PowerValue(BaseValueWithUnit):
    Kilowatts = __qualname__ + "kW"
    Watts = __qualname__ + "W"
    BTU_hour = __qualname__ + "BtuH"
    MBTU_hour = __qualname__ + "MBtuH"

    def get_unit_type(self) -> UnitType:
        return UnitType.Power

    @staticmethod
    def get_unit_ids() -> List[str]:
        return [PowerValue.Watts, PowerValue.Kilowatts, PowerValue.BTU_hour, PowerValue.MBTU_hour]

    @staticmethod
    def get_unit_string_map() -> TypingOD[str, str]:
        od = OrderedDict()
        od[PowerValue.Kilowatts] = "kW"
        od[PowerValue.Watts] = "W"
        od[PowerValue.BTU_hour] = "Btu/hr"
        od[PowerValue.MBTU_hour] = "MBtu/hr"
        return od

    @staticmethod
    def calculation_unit_id() -> str:
        return PowerValue.Kilowatts

    @staticmethod
    def base_ip_unit_id() -> str:
        return PowerValue.MBTU_hour

    @staticmethod
    def base_si_unit() -> str:
        return PowerValue.Kilowatts

    def convert_to_calculation_unit(self):
        if self.units == self.calculation_unit_id():
            return
        elif self.units == PowerValue.Watts:
            self.value /= 1000.0
        elif self.units == PowerValue.BTU_hour:
            factor = 1 / (3.412 * 1000)
            self.value *= factor
        elif self.units == PowerValue.MBTU_hour:
            factor = 1000 / (3.412 * 1000)
            self.value *= factor
        self.units = self.calculation_unit_id()


class FlowValue(BaseValueWithUnit):
    GPM = __qualname__ + "GPM"
    CFM = __qualname__ + "CFM"
    M3S = __qualname__ + "M3S"

    def get_unit_type(self) -> UnitType:
        return UnitType.Flow

    @staticmethod
    def get_unit_ids() -> List[str]:
        return [FlowValue.GPM, FlowValue.CFM, FlowValue.M3S]

    @staticmethod
    def get_unit_string_map() -> TypingOD[str, str]:
        od = OrderedDict()
        od[FlowValue.GPM] = "GPM"
        od[FlowValue.CFM] = "CFM"
        od[FlowValue.M3S] = "m^3/s"
        return od

    @staticmethod
    def calculation_unit_id() -> str:
        return FlowValue.M3S

    @staticmethod
    def base_ip_unit_id() -> str:
        return FlowValue.GPM

    @staticmethod
    def base_si_unit() -> str:
        return FlowValue.M3S

    def convert_to_calculation_unit(self):
        if self.units == self.calculation_unit_id():
            return
        elif self.units == FlowValue.CFM:
            self.value *= 0.0004719474432
        elif self.units == FlowValue.GPM:
            self.value *= 0.00006309
        self.units = self.calculation_unit_id()


class TemperatureValue(BaseValueWithUnit):
    F = __qualname__ + "F"
    C = __qualname__ + "C"
    K = __qualname__ + "K"

    def get_unit_type(self) -> UnitType:
        return UnitType.Temperature

    @staticmethod
    def get_unit_ids() -> List[int]:
        return [TemperatureValue.F, TemperatureValue.C, TemperatureValue.K]

    @staticmethod
    def get_unit_string_map() -> TypingOD[str, str]:
        od = OrderedDict()
        od[TemperatureValue.F] = "deg F"
        od[TemperatureValue.C] = "deg C"
        od[TemperatureValue.K] = "Kelvin"
        return od

    @staticmethod
    def calculation_unit_id() -> str:
        return TemperatureValue.C

    @staticmethod
    def base_ip_unit_id() -> str:
        return TemperatureValue.F

    @staticmethod
    def base_si_unit() -> str:
        return TemperatureValue.C

    def convert_to_calculation_unit(self):
        if self.units == self.calculation_unit_id():
            return
        elif self.units == TemperatureValue.F:
            self.value = (self.value - 32.0) / 1.8
        elif self.units == TemperatureValue.K:
            self.value -= 273.15
        self.units = self.calculation_unit_id()


class PressureValue(BaseValueWithUnit):
    Pa = __qualname__ + "Pa"
    KPa = __qualname__ + "kPa"
    Atm = __qualname__ + "Atm"
    PSI = __qualname__ + "PSI"

    def get_unit_type(self) -> UnitType:
        return UnitType.Pressure

    @staticmethod
    def get_unit_ids() -> List[str]:
        return [PressureValue.Pa, PressureValue.KPa, PressureValue.Atm, PressureValue.PSI]

    @staticmethod
    def get_unit_string_map() -> TypingOD[str, str]:
        od = OrderedDict()
        od[PressureValue.Pa] = "Pa"
        od[PressureValue.KPa] = "kPa"
        od[PressureValue.Atm] = "atm"
        od[PressureValue.PSI] = "psi"
        return od

    @staticmethod
    def calculation_unit_id() -> str:
        return PressureValue.Pa

    @staticmethod
    def base_ip_unit_id() -> str:
        return PressureValue.PSI

    @staticmethod
    def base_si_unit() -> str:
        return PressureValue.Pa

    def convert_to_calculation_unit(self):
        if self.units == self.calculation_unit_id():
            return
        elif self.units == PressureValue.KPa:
            self.value *= 1000.0
        elif self.units == PressureValue.Atm:
            self.value *= 101325.0
        elif self.units == PressureValue.PSI:
            self.value *= 6894.757
        self.units = self.calculation_unit_id()


class LengthValue(BaseValueWithUnit):
    Meters = __qualname__ + "M"
    Feet = __qualname__ + "Ft"
    Inches = __qualname__ + "In"
    Centimeters = __qualname__ + "CM"
    Millimeters = __qualname__ + "MM"

    def get_unit_type(self) -> UnitType:
        return UnitType.Length

    @staticmethod
    def get_unit_ids() -> List[str]:
        return [
            LengthValue.Meters, LengthValue.Feet, LengthValue.Inches, LengthValue.Centimeters, LengthValue.Millimeters
        ]

    @staticmethod
    def get_unit_string_map() -> TypingOD[str, str]:
        od = OrderedDict()
        od[LengthValue.Meters] = "Meters"
        od[LengthValue.Feet] = "Feet"
        od[LengthValue.Inches] = "Inches"
        od[LengthValue.Centimeters] = "Centimeters"
        od[LengthValue.Millimeters] = "Millimeters"
        return od

    @staticmethod
    def calculation_unit_id() -> str:
        return LengthValue.Meters

    @staticmethod
    def base_ip_unit_id() -> str:
        return LengthValue.Inches

    @staticmethod
    def base_si_unit() -> str:
        return LengthValue.Meters

    def convert_to_calculation_unit(self):
        if self.units == self.calculation_unit_id():
            return
        elif self.units == LengthValue.Feet:
            self.value *= 0.3048
        elif self.units == LengthValue.Inches:
            self.value *= 0.0254
        elif self.units == LengthValue.Centimeters:
            self.value *= 0.01
        elif self.units == LengthValue.Millimeters:
            self.value *= 0.001
        self.units = self.calculation_unit_id()


class RotationSpeedValue(BaseValueWithUnit):
    RevsPerSecond = __qualname__ + "Rps"
    RevsPerMinute = __qualname__ + "Rpm"
    RadiansPerSecond = __qualname__ + "RadPs"

    def get_unit_type(self) -> UnitType:
        return UnitType.RotationalSpeed

    @staticmethod
    def get_unit_ids() -> List[str]:
        return [RotationSpeedValue.RevsPerSecond, RotationSpeedValue.RevsPerMinute, RotationSpeedValue.RadiansPerSecond]

    @staticmethod
    def get_unit_string_map() -> TypingOD[str, str]:
        od = OrderedDict()
        od[RotationSpeedValue.RevsPerSecond] = "Revs/Sec"
        od[RotationSpeedValue.RevsPerMinute] = "Revs/Min"
        od[RotationSpeedValue.RadiansPerSecond] = "Rads/Sec"
        return od

    @staticmethod
    def calculation_unit_id() -> str:
        return RotationSpeedValue.RevsPerSecond

    @staticmethod
    def base_ip_unit_id() -> str:
        return RotationSpeedValue.RevsPerMinute

    @staticmethod
    def base_si_unit() -> str:
        return RotationSpeedValue.RevsPerSecond

    def convert_to_calculation_unit(self):
        if self.units == self.calculation_unit_id():
            return
        elif self.units == RotationSpeedValue.RadiansPerSecond:
            self.value /= 6.2831853
        elif self.units == RotationSpeedValue.RevsPerMinute:
            self.value /= 60.0
        self.units = self.calculation_unit_id()


def unit_class_factory(unit_type: UnitType) -> Type[BaseValueWithUnit]:
    if unit_type == UnitType.Power:
        return PowerValue
    elif unit_type == UnitType.Flow:
        return FlowValue
    elif unit_type == UnitType.Temperature:
        return TemperatureValue
    elif unit_type == UnitType.Dimensionless:
        return DimensionlessValue
    elif unit_type == UnitType.Pressure:
        return PressureValue
    elif unit_type == UnitType.Length:
        return LengthValue
    elif unit_type == UnitType.RotationalSpeed:
        return RotationSpeedValue
    else:
        raise EnergyPlusPetException(f"Bad unit_type input sent to unit_class_factory: \"{str(unit_type)}\", aborting.")


def unit_instance_factory(value: float, unit_type: UnitType) -> BaseValueWithUnit:
    return unit_class_factory(unit_type)(value)
