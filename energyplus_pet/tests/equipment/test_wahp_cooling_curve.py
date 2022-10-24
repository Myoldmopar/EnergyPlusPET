from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.wahp_cooling_curve import WaterToAirHeatPumpCoolingCurveFit
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.tests.equipment.equipment_test_helper import EquipmentTestHelper


class TestWAHPCoolingCurve(EquipmentTestHelper):
    def test_interface(self):
        eq = WaterToAirHeatPumpCoolingCurveFit()
        eq.total_capacity_params = [0] * 5
        eq.sensible_capacity_params = [0] * 6
        eq.cooling_power_params = [0] * 5
        eq.set_required_constant_parameter(eq.rated_air_volume_flow_key, 10)
        eq.set_required_constant_parameter(eq.rated_water_volume_flow_key, 20)
        eq.set_required_constant_parameter(eq.rated_total_capacity_key, 100)
        eq.set_required_constant_parameter(eq.rated_cooling_power_key, 50)
        self.check_interface(eq, EquipType.WAHP_Cooling_CurveFit)

    def blah_generated_parameters(self):
        eq = WaterToAirHeatPumpCoolingCurveFit()
        cdm = CatalogDataManager()
        cdm.final_data_matrix = [
            [1, 1, 1, 1, 7188.99293286219, 4678.82243816255],
            [2, 2, 2, 2, 7586.12367491166, 5205.48233215548],
            [3, 3, 3, 3, 7983.25441696113, 5732.14222614841],
            [4, 4, 4, 4, 8380.3851590106, 6258.80212014134],
            [5, 5, 5, 1, 8277.51590106007, 5561.46201413428],
            [6, 6, 6, 2, 8674.64664310954, 6088.12190812721],
            [7, 7, 7, 3, 9071.77738515901, 6614.78180212014],
            [8, 8, 8, 4, 9468.90812720848, 7141.44169611307],
            [9, 9, 1, 1, 9218.19434628975, 6426.57508833922],
            [10, 10, 2, 2, 9615.32508833922, 6953.23498233216],
            [11, 11, 3, 3, 10012.4558303887, 7479.89487632509],
            [12, 12, 4, 4, 10409.5865724382, 8006.55477031802],
            [13, 13, 5, 1, 10306.7173144876, 7309.21466431095],
            [14, 14, 6, 2, 10703.8480565371, 7835.87455830389],
            [15, 15, 7, 3, 11100.9787985866, 8362.53445229682],
            [16, 16, 8, 4, 11498.109540636, 8889.19434628975],
            [17, 1, 1, 1, 7231.39575971731, 4778.3277385159],
            [18, 2, 2, 2, 7628.52650176678, 5304.98763250883],
            [19, 3, 3, 3, 8025.65724381625, 5831.64752650177],
            [20, 4, 4, 4, 8422.78798586572, 6358.3074204947],
            [21, 5, 5, 1, 8319.91872791519, 5660.96731448763],
            [22, 6, 6, 2, 8717.04946996466, 6187.62720848057],
            [23, 7, 7, 3, 9114.18021201413, 6714.2871024735],
            [24, 8, 8, 4, 9511.3109540636, 7240.94699646643],
            [25, 9, 1, 1, 9260.59717314488, 6526.08038869258],
            [26, 10, 2, 2, 9657.72791519435, 7052.74028268551],
            [27, 11, 3, 3, 10054.8586572438, 7579.40017667845],
            [28, 12, 4, 4, 10451.9893992933, 8106.06007067138],
            [29, 13, 5, 1, 10349.1201413428, 7408.71996466431],
            [30, 14, 6, 2, 10746.2508833922, 7935.37985865725],
            [31, 15, 7, 3, 11143.3816254417, 8462.03975265018],
            [32, 16, 8, 4, 11540.5123674912, 8988.69964664311],
        ]
        eq.set_required_constant_parameter(eq.rated_air_volume_flow_key, 10)
        eq.set_required_constant_parameter(eq.rated_water_volume_flow_key, 20)
        eq.set_required_constant_parameter(eq.rated_total_capacity_key, 360)
        eq.set_required_constant_parameter(eq.rated_sensible_capacity_key, 300)
        eq.set_required_constant_parameter(eq.rated_cooling_power_key, 60)
        eq.generate_parameters(cdm, lambda *_: None, lambda *_: None)
        expected = [10.2, 52.3, 7.5, 12.5, 50.2]
        calculated = eq.total_capacity_params
        [self.assertAlmostEqual(e, c, 1) for e, c in zip(expected, calculated)]
        expected = [37.1, 12.4, 35.2, 61.2, 84.9]
        calculated = eq.cooling_power_params
        [self.assertAlmostEqual(e, c, 1) for e, c in zip(expected, calculated)]

    def test_output_forms(self):
        pass
