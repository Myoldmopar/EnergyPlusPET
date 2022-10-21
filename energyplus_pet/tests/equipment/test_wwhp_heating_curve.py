from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.wwhp_heating_curve import WaterToWaterHeatPumpHeatingCurveFit
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.tests.equipment.equipment_test_helper import EquipmentTestHelper


class TestWWHPHeatingCurve(EquipmentTestHelper):
    def test_interface(self):
        eq = WaterToWaterHeatPumpHeatingCurveFit()
        self.check_interface(eq, EquipType.WWHP_Heating_CurveFit)

    def test_generated_parameters(self):
        eq = WaterToWaterHeatPumpHeatingCurveFit()
        cdm = CatalogDataManager()
        eq.generate_parameters(cdm, lambda *_: None, lambda *_: None)

    def test_output_forms(self):
        pass
