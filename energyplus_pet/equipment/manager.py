from typing import Type, Union

from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.wahp_heating_curve import WaterToAirHeatPumpHeatingCurveFit
from energyplus_pet.equipment.wahp_cooling_curve import WaterToAirHeatPumpCoolingCurveFit
from energyplus_pet.equipment.wwhp_heating_curve import WaterToWaterHeatPumpHeatingCurveFit
from energyplus_pet.equipment.wwhp_cooling_curve import WaterToWaterHeatPumpCoolingCurveFit


class EquipmentFactory:
    """Handles construction of equipment"""

    @staticmethod
    def class_factory(equipment_type: EquipType) -> Union[Type[BaseEquipment], None]:
        """Returns a class Type for the given EquipType enum value, or None if no match"""
        type_map = {
            EquipType.InvalidType: None,
            EquipType.WAHP_Heating_CurveFit: WaterToAirHeatPumpHeatingCurveFit,
            EquipType.WAHP_Heating_PE: None,
            EquipType.WAHP_Cooling_CurveFit: WaterToAirHeatPumpCoolingCurveFit,
            EquipType.WAHP_Cooling_PE: None,
            EquipType.WWHP_Heating_CurveFit: WaterToWaterHeatPumpHeatingCurveFit,
            EquipType.WWHP_Cooling_CurveFit: WaterToWaterHeatPumpCoolingCurveFit,
            EquipType.Pump_ConstSpeed_ND: None,
        }
        return type_map.get(equipment_type, None)

    @staticmethod
    def instance_factory(equipment_type: EquipType) -> Union[BaseEquipment, None]:
        """Returns a class instance for the given EquipType enum value, or None if no match"""
        equip_type = EquipmentFactory.class_factory(equipment_type)
        if equip_type is None:
            return None
        return equip_type()
