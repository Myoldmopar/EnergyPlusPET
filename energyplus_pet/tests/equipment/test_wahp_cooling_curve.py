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

    def test_generated_parameters(self):
        eq = WaterToAirHeatPumpCoolingCurveFit()
        cdm = CatalogDataManager()
        cdm.final_data_matrix = [
            [1, 1, 1, 1, 1, 23293.4275618375, 10162.8070671378, 3975.98268551237],
            [2, 2, 2, 2, 2, 24355.0176678445, 11264.0763250883, 4154.65300353357],
            [3, 3, 3, 3, 1, 24334.6077738516, 10853.3455830389, 4178.52332155477],
            [4, 4, 4, 4, 2, 25396.1978798587, 11954.6148409894, 4357.19363957597],
            [5, 5, 5, 1, 1, 25277.9787985866, 11522.9653710247, 4362.88727915194],
            [6, 6, 6, 2, 2, 26339.5689045936, 12624.2346289753, 4541.55759717315],
            [7, 7, 7, 3, 1, 26319.1590106007, 12213.5038869258, 4565.42791519435],
            [8, 8, 8, 4, 2, 27380.7491166078, 13314.7731448763, 4744.09823321555],
            [9, 9, 1, 1, 1, 27262.5300353357, 12859.6042402827, 4749.79187279152],
            [10, 10, 2, 2, 2, 28324.1201413428, 13960.8734982332, 4928.46219081272],
            [11, 11, 3, 3, 1, 28303.7102473498, 13550.1427561837, 4952.33250883392],
            [12, 12, 4, 4, 2, 29365.3003533569, 14651.4120141343, 5131.00282685512],
            [13, 13, 5, 1, 1, 29247.0812720848, 14219.7625441696, 5136.6964664311],
            [14, 14, 6, 2, 2, 30308.6713780919, 15321.0318021201, 5315.3667844523],
            [15, 15, 7, 3, 1, 30288.2614840989, 14910.3010600707, 5339.2371024735],
            [16, 16, 8, 4, 2, 31349.851590106, 16011.5703180212, 5517.9074204947],
            [17, 1, 1, 1, 1, 23727.6325088339, 10270.0014134276, 4011.60106007067],
            [18, 2, 2, 2, 2, 24789.222614841, 11371.2706713781, 4190.27137809187],
            [19, 3, 3, 3, 1, 24768.8127208481, 10960.5399293286, 4214.14169611307],
            [20, 4, 4, 4, 2, 25830.4028268551, 12061.8091872792, 4392.81201413428],
            [21, 5, 5, 1, 1, 25712.183745583, 11630.1597173145, 4398.50565371025],
            [22, 6, 6, 2, 2, 26773.7738515901, 12731.428975265, 4577.17597173145],
            [23, 7, 7, 3, 1, 26753.3639575972, 12320.6982332156, 4601.04628975265],
            [24, 8, 8, 4, 2, 27814.9540636042, 13421.9674911661, 4779.71660777385],
            [25, 9, 1, 1, 1, 27696.7349823322, 12966.7985865724, 4785.41024734982],
            [26, 10, 2, 2, 2, 28758.3250883392, 14068.067844523, 4964.08056537103],
            [27, 11, 3, 3, 1, 28737.9151943463, 13657.3371024735, 4987.95088339223],
            [28, 12, 4, 4, 2, 29799.5053003534, 14758.606360424, 5166.62120141343],
            [29, 13, 5, 1, 1, 29681.2862190813, 14326.9568904594, 5172.3148409894],
            [30, 14, 6, 2, 2, 30742.8763250883, 15428.2261484099, 5350.9851590106],
            [31, 15, 7, 3, 1, 30722.4664310954, 15017.4954063604, 5374.8554770318],
            [32, 16, 8, 4, 2, 31784.0565371025, 16118.764664311, 5553.525795053],
        ]
        eq.set_required_constant_parameter(eq.rated_air_volume_flow_key, 10)
        eq.set_required_constant_parameter(eq.rated_water_volume_flow_key, 20)
        eq.set_required_constant_parameter(eq.rated_total_capacity_key, 100)
        eq.set_required_constant_parameter(eq.rated_sensible_capacity_key, 80)
        eq.set_required_constant_parameter(eq.rated_cooling_power_key, 20)
        eq.generate_parameters(cdm, lambda *_: None, lambda *_: None)
        expected = [81.4, 69.2, 76.8, 54.1, 93.8]
        calculated = eq.total_capacity_params
        [self.assertAlmostEqual(e, c, 1) for e, c in zip(expected, calculated)]
        expected = [62.5, 10.4, 18.5, 23.7, 94.5, 82.6]
        calculated = eq.sensible_capacity_params
        [self.assertAlmostEqual(e, c, 1) for e, c in zip(expected, calculated)]
        expected = [97.4, 64.3, 31.5, 38.7, 94.5]
        calculated = eq.cooling_power_params
        [self.assertAlmostEqual(e, c, 1) for e, c in zip(expected, calculated)]

    def test_output_forms(self):
        pass
