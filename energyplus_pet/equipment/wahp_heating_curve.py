from typing import List
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.types import EquipType


class WaterToAirHeatPumpHeatingCurveFit(BaseEquipment):

    def __init__(self):
        super().__init__()

    def this_type(self) -> EquipType:
        return EquipType.WAHP_Heating_CurveFit

    def header_units(self) -> List[str]:
        pass

    def header_strings(self) -> List[str]:
        pass

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
