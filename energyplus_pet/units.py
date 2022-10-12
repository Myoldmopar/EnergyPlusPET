from abc import abstractmethod
from enum import Enum, auto
from typing import List


class UnitType(Enum):
    power = auto()
    flow = auto()
    temp = auto()
    none = auto()
    pressure = auto()
    length = auto()
    rotational_speed = auto()


class BaseUnit:

    def __init__(self, initial_value: float, initial_units: int):
        self.value = initial_value
        self.units = initial_units

    @abstractmethod
    def get_units(self) -> List[int]: pass

    @abstractmethod
    def get_unit_strings(self) -> List[str]: pass

    @abstractmethod
    def calculation_unit(self) -> int: pass

    @abstractmethod
    def base_ip_unit(self) -> int: pass

    @abstractmethod
    def base_si_unit(self) -> int: pass

    @abstractmethod
    def convert_to_calculation_unit(self): pass


class PowerUnits(BaseUnit):
    Watts = 0
    Kilowatts = 1
    BTU_hour = 2
    MBTU_hour = 3

    def get_units(self) -> List[int]:
        return [PowerUnits.Watts, PowerUnits.Kilowatts, PowerUnits.BTU_hour, PowerUnits.MBTU_hour]

    def get_unit_strings(self) -> List[str]:
        return ["Watts", "Kilowatts", "Btu/hr", "MBtu/hr"]

    def calculation_unit(self) -> int:
        return PowerUnits.Kilowatts

    def base_ip_unit(self) -> int:
        return PowerUnits.MBTU_hour

    def base_si_unit(self) -> int:
        return PowerUnits.Kilowatts

    def convert_to_calculation_unit(self):
        if self.units == self.calculation_unit():
            return
        elif self.units == PowerUnits.Watts:
            self.value /= 1000.0
        elif self.units == PowerUnits.BTU_hour:
            factor = 1 / (3.412 * 1000)
            self.value *= factor
        elif self.units == PowerUnits.MBTU_hour:
            factor = 1000 / (3.412 * 1000)
            self.value *= factor
        self.units = self.calculation_unit()


class FlowUnits(BaseUnit):
    GPM = 0
    CFM = 1
    M3S = 2

    def get_units(self) -> List[int]:
        return [FlowUnits.GPM, FlowUnits.CFM, FlowUnits.M3S]

    def get_unit_strings(self) -> List[str]:
        return ["GPM", "CFM", "m^3/s"]

    def calculation_unit(self) -> int:
        return FlowUnits.M3S

    def base_ip_unit(self) -> int:
        return FlowUnits.GPM

    def base_si_unit(self) -> int:
        return FlowUnits.M3S

    def convert_to_calculation_unit(self):
        if self.units == self.calculation_unit():
            return
        elif self.units == FlowUnits.CFM:
            self.value *= 0.0004719474432
        elif self.units == FlowUnits.GPM:
            self.value *= 0.00006309
        self.units = self.calculation_unit()


class TempUnits(BaseUnit):
    F = 0
    C = 1
    K = 2

    def get_units(self) -> List[int]:
        return [TempUnits.F, TempUnits.C, TempUnits.K]

    def get_unit_strings(self) -> List[str]:
        return ["deg F", "deg C", "deg K"]

    def calculation_unit(self) -> int:
        return TempUnits.C

    def base_ip_unit(self) -> int:
        return TempUnits.F

    def base_si_unit(self) -> int:
        return TempUnits.C

    def convert_to_calculation_unit(self):
        if self.units == self.calculation_unit():
            return
        elif self.units == TempUnits.F:
            self.value = (self.value - 32.0) / 1.8
        elif self.units == TempUnits.K:
            self.value -= 273.15
        self.units = self.calculation_unit()


class PressureUnits(BaseUnit):
    Pa = 0
    KPa = 1
    Atm = 2
    PSI = 3

    def get_units(self) -> List[int]:
        return [PressureUnits.Pa, PressureUnits.KPa, PressureUnits.Atm, PressureUnits.PSI]

    def get_unit_strings(self) -> List[str]:
        return ["Pa", "kPa", "atm", "psi"]

    def calculation_unit(self) -> int:
        return PressureUnits.Pa

    def base_ip_unit(self) -> int:
        return PressureUnits.PSI

    def base_si_unit(self) -> int:
        return PressureUnits.Pa

    def convert_to_calculation_unit(self):
        if self.units == self.calculation_unit():
            return
        elif self.units == PressureUnits.KPa:
            self.value *= 1000.0
        elif self.units == PressureUnits.Atm:
            self.value *= 101325.0
        elif self.units == PressureUnits.PSI:
            self.value *= 6894.757
        self.units = self.calculation_unit()


class LengthUnits(BaseUnit):
    Meters = 0
    Feet = 1
    Inches = 2
    Centimeters = 3
    Millimeters = 4

    def get_units(self) -> List[int]:
        return [
            LengthUnits.Meters, LengthUnits.Feet, LengthUnits.Inches, LengthUnits.Centimeters, LengthUnits.Millimeters
        ]

    def get_unit_strings(self) -> List[str]:
        return ["Meters", "Feet", "Inches", "Centimeters", "Millimeters"]

    def calculation_unit(self) -> int:
        return LengthUnits.Meters

    def base_ip_unit(self) -> int:
        return LengthUnits.Inches

    def base_si_unit(self) -> int:
        return LengthUnits.Meters

    def convert_to_calculation_unit(self):
        if self.units == self.calculation_unit():
            return
        elif self.units == LengthUnits.Feet:
            self.value *= 0.3048
        elif self.units == LengthUnits.Inches:
            self.value *= 0.0254
        elif self.units == LengthUnits.Centimeters:
            self.value *= 0.01
        elif self.units == LengthUnits.Millimeters:
            self.value *= 0.001
        self.units = self.calculation_unit()


class RotationSpeedUnits(BaseUnit):
    RevsPerSecond = 0
    RevsPerMinute = 1
    RadiansPerSecond = 2

    def get_units(self) -> List[int]:
        return [RotationSpeedUnits.RevsPerSecond, RotationSpeedUnits.RevsPerMinute, RotationSpeedUnits.RadiansPerSecond]

    def get_unit_strings(self) -> List[str]:
        return ["Revs/Sec", "Revs/Min", "Rads/Sec"]

    def calculation_unit(self) -> int:
        return RotationSpeedUnits.RevsPerSecond

    def base_ip_unit(self) -> int:
        return RotationSpeedUnits.RevsPerMinute

    def base_si_unit(self) -> int:
        return RotationSpeedUnits.RevsPerSecond

    def convert_to_calculation_unit(self):
        if self.units == self.calculation_unit():
            return
        elif self.units == RotationSpeedUnits.RadiansPerSecond:
            self.value /= 6.2831853
        elif self.units == RotationSpeedUnits.RevsPerMinute:
            self.value /= 60.0
        self.units = self.calculation_unit()
