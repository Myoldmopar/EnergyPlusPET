from abc import abstractmethod
from typing import List

from energyplus_pet.equipment.types import EquipType


class BaseEquipment:
    def __init__(self):
        self.header_strings = []
        self.header_units = []

    def this_type(self) -> EquipType:
        return EquipType.InvalidType

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
