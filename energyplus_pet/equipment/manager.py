from typing import Union

from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.types import EquipType
from energyplus_pet.equipment.wahp_heating_curve import WaterToAirHeatPumpHeatingCurveFit


class EquipmentFactory:

    @staticmethod
    def factory(equipment_type: EquipType) -> Union[BaseEquipment, None]:
        type_map = {
            EquipType.WAHP_Heating_CurveFit: WaterToAirHeatPumpHeatingCurveFit,
            EquipType.WAHP_Heating_PE: None,
            EquipType.WAHP_Cooling_CurveFit: None,
            EquipType.WAHP_Cooling_PE: None,
            EquipType.WWHP_Heating_CurveFit: None,
            EquipType.WWHP_Cooling_CurveFit: None,
            EquipType.Pump_ConstSpeed_ND: None,
        }
        equip_type = type_map[equipment_type]
        if equip_type is None:
            return None
        return equip_type()
