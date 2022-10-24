from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.wwhp_heating_curve import WaterToWaterHeatPumpHeatingCurveFit
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.tests.equipment.equipment_test_helper import EquipmentTestHelper


class TestWWHPHeatingCurve(EquipmentTestHelper):
    def test_interface(self):
        eq = WaterToWaterHeatPumpHeatingCurveFit()
        eq.total_capacity_params = [0] * 5
        eq.heating_power_params = [0] * 5
        eq.set_required_constant_parameter(eq.rated_load_volume_flow_key, 10)
        eq.set_required_constant_parameter(eq.rated_source_volume_flow_key, 20)
        eq.set_required_constant_parameter(eq.rated_total_capacity_key, 100)
        eq.set_required_constant_parameter(eq.rated_heating_power_key, 50)
        self.check_interface(eq, EquipType.WWHP_Heating_CurveFit)

    def test_generated_parameters(self):
        eq = WaterToWaterHeatPumpHeatingCurveFit()
        cdm = CatalogDataManager()
        cdm.final_data_matrix = [
            [1, 1, 1, 1, 8806.98056537102, 4982.18816254417],
            [2, 2, 2, 2, 10091.5901060071, 5491.08215547703],
            [3, 3, 3, 3, 11376.1996466431, 5999.97614840989],
            [4, 4, 4, 4, 12660.8091872792, 6508.87014134276],
            [5, 5, 5, 1, 10661.4187279152, 5553.76413427562],
            [6, 6, 6, 2, 11946.0282685512, 6062.65812720848],
            [7, 7, 7, 3, 13230.6378091873, 6571.55212014134],
            [8, 8, 8, 4, 14515.2473498233, 7080.44611307421],
            [9, 9, 1, 1, 12427.6590106007, 6076.15282685512],
            [10, 10, 2, 2, 13712.2685512368, 6585.04681978799],
            [11, 11, 3, 3, 14996.8780918728, 7093.94081272085],
            [12, 12, 4, 4, 16281.4876325088, 7602.83480565371],
            [13, 13, 5, 1, 14282.0971731449, 6647.72879858657],
            [14, 14, 6, 2, 15566.7067137809, 7156.62279151944],
            [15, 15, 7, 3, 16851.316254417, 7665.5167844523],
            [16, 16, 8, 4, 18135.925795053, 8174.41077738516],
            [17, 1, 1, 1, 9000.33745583039, 5122.11749116608],
            [18, 2, 2, 2, 10284.9469964664, 5631.01148409894],
            [19, 3, 3, 3, 11569.5565371025, 6139.9054770318],
            [20, 4, 4, 4, 12854.1660777385, 6648.79946996467],
            [21, 5, 5, 1, 10854.7756183746, 5693.69346289753],
            [22, 6, 6, 2, 12139.3851590106, 6202.58745583039],
            [23, 7, 7, 3, 13423.9946996466, 6711.48144876325],
            [24, 8, 8, 4, 14708.6042402827, 7220.37544169611],
            [25, 9, 1, 1, 12621.0159010601, 6216.08215547703],
            [26, 10, 2, 2, 13905.6254416961, 6724.9761484099],
            [27, 11, 3, 3, 15190.2349823322, 7233.87014134276],
            [28, 12, 4, 4, 16474.8445229682, 7742.76413427562],
            [29, 13, 5, 1, 14475.4540636042, 6787.65812720848],
            [30, 14, 6, 2, 15760.0636042403, 7296.55212014134],
            [31, 15, 7, 3, 17044.6731448763, 7805.44611307421],
            [32, 16, 8, 4, 18329.2826855124, 8314.34010600707],
        ]
        eq.set_required_constant_parameter(eq.rated_load_volume_flow_key, 10)
        eq.set_required_constant_parameter(eq.rated_source_volume_flow_key, 20)
        eq.set_required_constant_parameter(eq.rated_total_capacity_key, 100)
        eq.set_required_constant_parameter(eq.rated_heating_power_key, 50)
        eq.generate_parameters(cdm, lambda *_: None, lambda *_: None)
        expected = [12.1, 31.2, 34.2, 82.1, 88.1]
        calculated = eq.total_capacity_params
        [self.assertAlmostEqual(e, c, 1) for e, c in zip(expected, calculated)]
        expected = [8.1, 34.8, 49.5, 73.2, 51.2]
        calculated = eq.heating_power_params
        [self.assertAlmostEqual(e, c, 1) for e, c in zip(expected, calculated)]

    def test_output_forms(self):
        pass
