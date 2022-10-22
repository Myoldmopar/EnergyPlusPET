from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.wahp_heating_curve import WaterToAirHeatPumpHeatingCurveFit
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.tests.equipment.equipment_test_helper import EquipmentTestHelper


class TestWAHPHeatingCurve(EquipmentTestHelper):
    def test_interface(self):
        eq = WaterToAirHeatPumpHeatingCurveFit()
        # initialize the output parameters
        eq.heating_capacity_params = [0] * 5
        eq.heating_power_params = [0] * 5
        eq.set_required_constant_parameter(eq.rated_load_volume_flow_key, 10)
        eq.set_required_constant_parameter(eq.rated_source_volume_flow_key, 10)
        eq.set_required_constant_parameter(eq.rated_heating_capacity_key, 10)
        eq.set_required_constant_parameter(eq.rated_heating_power_key, 1)
        self.check_interface(eq, EquipType.WAHP_Heating_CurveFit)

    def test_generated_parameters_no_correction_factors(self):
        # This data was generated manually from a simple set of independent variables,
        # and the capacity and power were calculated using made-up coefficients.
        # Using the same rated data and catalog data, we should be able to get back essentially
        # the same exact coefficients that were used to generate the data in the first place
        eq = WaterToAirHeatPumpHeatingCurveFit()
        cdm = CatalogDataManager()
        cdm.final_data_matrix = [
            [1, 1, 1, 1, 28389.1700353357, 5535.105795053],
            [2, 2, 2, 2, 29697.8043816254, 5702.25858657244],
            [3, 3, 3, 3, 31006.4387279152, 5869.41137809187],
            [4, 4, 4, 4, 32315.0730742049, 6036.56416961131],
            [5, 5, 5, 1, 31259.2274204947, 5852.35696113074],
            [6, 6, 6, 2, 32567.8617667845, 6019.50975265018],
            [7, 7, 7, 3, 33876.4961130742, 6186.66254416961],
            [8, 8, 8, 4, 35185.130459364, 6353.81533568905],
            [9, 9, 1, 1, 33811.7724381625, 6110.58339222615],
            [10, 10, 2, 2, 35120.4067844523, 6277.73618374558],
            [11, 11, 3, 3, 36429.0411307421, 6444.88897526502],
            [12, 12, 4, 4, 37737.6754770318, 6612.04176678445],
            [13, 13, 5, 1, 36681.8298233216, 6427.83455830389],
            [14, 14, 6, 2, 37990.4641696113, 6594.98734982332],
            [15, 15, 7, 3, 39299.0985159011, 6762.14014134276],
            [16, 16, 8, 4, 40607.7328621908, 6929.29293286219],
            [17, 1, 1, 1, 29085.2548409894, 5703.02098939929],
            [18, 2, 2, 2, 30393.8891872792, 5870.17378091873],
            [19, 3, 3, 3, 31702.5235335689, 6037.32657243816],
            [20, 4, 4, 4, 33011.1578798587, 6204.4793639576],
            [21, 5, 5, 1, 31955.3122261484, 6020.27215547703],
            [22, 6, 6, 2, 33263.9465724382, 6187.42494699647],
            [23, 7, 7, 3, 34572.5809187279, 6354.5777385159],
            [24, 8, 8, 4, 35881.2152650177, 6521.73053003533],
            [25, 9, 1, 1, 34507.8572438163, 6278.49858657244],
            [26, 10, 2, 2, 35816.491590106, 6445.65137809187],
            [27, 11, 3, 3, 37125.1259363958, 6612.80416961131],
            [28, 12, 4, 4, 38433.7602826855, 6779.95696113074],
            [29, 13, 5, 1, 37377.9146289753, 6595.74975265018],
            [30, 14, 6, 2, 38686.548975265, 6762.90254416961],
            [31, 15, 7, 3, 39995.1833215548, 6930.05533568905],
            [32, 16, 8, 4, 41303.8176678445, 7097.20812720848],
        ]
        eq.set_required_constant_parameter(eq.rated_load_volume_flow_key, 50)
        eq.set_required_constant_parameter(eq.rated_source_volume_flow_key, 50)
        eq.set_required_constant_parameter(eq.rated_heating_capacity_key, 360)
        eq.set_required_constant_parameter(eq.rated_heating_power_key, 60)
        eq.generate_parameters(cdm, lambda *_: None, lambda *_: None)
        expected = [12.1, 31.2, 34.2, 82.1, 88.1]
        calculated = eq.heating_capacity_params
        [self.assertAlmostEqual(e, c, 1) for e, c in zip(expected, calculated)]
        expected = [8.1, 34.8, 49.5, 73.2, 51.2]
        calculated = eq.heating_power_params
        [self.assertAlmostEqual(e, c, 1) for e, c in zip(expected, calculated)]

    def test_output_forms(self):
        pass
