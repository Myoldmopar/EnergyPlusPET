from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.wahp_heating_curve import WaterToAirHeatPumpHeatingCurveFit
from energyplus_pet.equipment.equip_types import EquipType
from .equipment_test_helper import EquipmentTestHelper


class TestWAHPHeatingCurve(EquipmentTestHelper):
    def test_interface(self):
        eq = WaterToAirHeatPumpHeatingCurveFit()
        self.check_interface(eq, EquipType.WAHP_Heating_CurveFit)

    def test_generated_parameters(self):
        eq = WaterToAirHeatPumpHeatingCurveFit()
        cdm = CatalogDataManager()
        eq.generate_parameters(cdm, lambda *_: None, lambda *_: None, lambda *_: None)

    def test_output_forms(self):
        pass
