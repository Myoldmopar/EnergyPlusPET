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
        eq.set_required_constant_parameter(eq.rated_air_volume_flow_key, 10)
        eq.set_required_constant_parameter(eq.rated_water_volume_flow_key, 10)
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
            [1, 1, 1, 1, 12511.9540636042, 9908.69876325088],
            [2, 2, 2, 2, 13311.8038869258, 10206.6466431095],
            [3, 3, 3, 3, 14111.6537102473, 10504.5945229682],
            [4, 4, 4, 4, 14911.5035335689, 10802.5424028269],
            [5, 5, 5, 1, 13707.3533568905, 10956.4902826855],
            [6, 6, 6, 2, 14507.203180212, 11254.4381625442],
            [7, 7, 7, 3, 15307.0530035336, 11552.3860424028],
            [8, 8, 8, 4, 16106.9028268551, 11850.3339222615],
            [9, 9, 1, 1, 14723.2473498233, 11912.9743816254],
            [10, 10, 2, 2, 15523.0971731449, 12210.9222614841],
            [11, 11, 3, 3, 16322.9469964664, 12508.8701413428],
            [12, 12, 4, 4, 17122.796819788, 12806.8180212014],
            [13, 13, 5, 1, 15918.6466431095, 12960.7659010601],
            [14, 14, 6, 2, 16718.4964664311, 13258.7137809187],
            [15, 15, 7, 3, 17518.3462897526, 13556.6616607774],
            [16, 16, 8, 4, 18318.1961130742, 13854.609540636],
            [17, 1, 1, 1, 12750.5406360424, 10017.25],
            [18, 2, 2, 2, 13550.390459364, 10315.1978798587],
            [19, 3, 3, 3, 14350.2402826855, 10613.1457597173],
            [20, 4, 4, 4, 15150.0901060071, 10911.093639576],
            [21, 5, 5, 1, 13945.9399293286, 11065.0415194346],
            [22, 6, 6, 2, 14745.7897526502, 11362.9893992933],
            [23, 7, 7, 3, 15545.6395759717, 11660.9372791519],
            [24, 8, 8, 4, 16345.4893992933, 11958.8851590106],
            [25, 9, 1, 1, 14961.8339222615, 12021.5256183746],
            [26, 10, 2, 2, 15761.683745583, 12319.4734982332],
            [27, 11, 3, 3, 16561.5335689046, 12617.4213780919],
            [28, 12, 4, 4, 17361.3833922261, 12915.3692579505],
            [29, 13, 5, 1, 16157.2332155477, 13069.3171378092],
            [30, 14, 6, 2, 16957.0830388693, 13367.2650176678],
            [31, 15, 7, 3, 17756.9328621908, 13665.2128975265],
            [32, 16, 8, 4, 18556.7826855124, 13963.1607773852],
        ]
        eq.set_required_constant_parameter(eq.rated_air_volume_flow_key, 10)
        eq.set_required_constant_parameter(eq.rated_water_volume_flow_key, 20)
        eq.set_required_constant_parameter(eq.rated_heating_capacity_key, 100)
        eq.set_required_constant_parameter(eq.rated_heating_power_key, 50)
        eq.generate_parameters(cdm, lambda *_: None, lambda *_: None)
        expected = [15.1, 63.5, 42.2, 50.1, 52.3]
        calculated = eq.heating_capacity_params
        [self.assertAlmostEqual(e, c, 1) for e, c in zip(expected, calculated)]
        expected = [92.8, 64.6, 38.4, 7.2, 97.5]
        calculated = eq.heating_power_params
        [self.assertAlmostEqual(e, c, 1) for e, c in zip(expected, calculated)]

    def test_output_forms(self):
        pass
