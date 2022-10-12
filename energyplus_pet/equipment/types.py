from abc import abstractmethod
from enum import Enum, auto
from typing import List


class EquipType(Enum):
    InvalidType = auto()  # used to return an invalid selection wherever needed
    WAHP_Heating_CurveFit = auto()
    WAHP_Heating_PE = auto()
    WAHP_Cooling_CurveFit = auto()
    WAHP_Cooling_PE = auto()
    WWHP_Heating_CurveFit = auto()
    WWHP_Cooling_CurveFit = auto()
    Pump_ConstSpeed_ND = auto()


class BaseEquipment:
    def __init__(self):
        self.header_strings = []
        self.header_units = []

    @abstractmethod
    def header_strings(self) -> List[str]: pass

    @abstractmethod
    def header_units(self) -> List[str]: pass

    @abstractmethod
    def to_eplus_idf_object(self) -> str: pass

    @abstractmethod
    def to_parameter_summary(self) -> str: pass

    @abstractmethod
    def to_eplus_epjson_object(self) -> str: pass

    @abstractmethod
    def generate_parameters(self): pass

    @abstractmethod
    def generate_absolute_plot(self): pass

    @abstractmethod
    def generate_error_plot(self): pass


class WaterToAirHeatPump(BaseEquipment):
    def __init__(self):
        super().__init__()

    def to_eplus_idf_object(self) -> str:
        pass

    def to_parameter_summary(self) -> str:
        pass

    def to_eplus_epjson_object(self) -> str:
        pass

    def generate_parameters(self):
        pass

    def generate_absolute_plot(self):
        pass

    def generate_error_plot(self):
        pass
