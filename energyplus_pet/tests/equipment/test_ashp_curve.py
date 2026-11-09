import json

from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.ashp_curve import (
    AirSourceHeatPumpCoolingCurveFit,
    AirSourceHeatPumpHeatingCurveFit,
)
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.tests.equipment.equipment_test_helper import EquipmentTestHelper


class TestAirSourceHeatPumpCurve(EquipmentTestHelper):
    @staticmethod
    def catalog_rows(coil):
        rows = []
        rated_indoor = coil.indoor_temperature_default
        rated_outdoor = coil.outdoor_temperature_default
        for indoor in (rated_indoor - 5, rated_indoor, rated_indoor + 5):
            for outdoor in (rated_outdoor - 15, rated_outdoor, rated_outdoor + 10):
                for flow_fraction in (0.8, 1.0, 1.2):
                    indoor_delta = indoor - rated_indoor
                    outdoor_delta = outdoor - rated_outdoor
                    flow_delta = flow_fraction - 1.0
                    capacity_fraction = (
                        1
                        + 0.004 * indoor_delta
                        + 0.0001 * indoor_delta ** 2
                        - 0.01 * outdoor_delta
                        - 0.0001 * outdoor_delta ** 2
                        + 0.0002 * indoor_delta * outdoor_delta
                    ) * (1 + 0.1 * flow_delta - 0.03 * flow_delta ** 2)
                    eir_fraction = (
                        1
                        - 0.003 * indoor_delta
                        + 0.0001 * indoor_delta ** 2
                        + 0.012 * outdoor_delta
                        + 0.0002 * outdoor_delta ** 2
                        - 0.0001 * indoor_delta * outdoor_delta
                    ) * (1 - 0.08 * flow_delta + 0.02 * flow_delta ** 2)
                    capacity = coil.rated_capacity * capacity_fraction
                    power = (
                        coil.rated_power
                        * capacity_fraction
                        * eir_fraction
                    )
                    rows.append(
                        [
                            outdoor,
                            indoor,
                            coil.rated_air_flow * flow_fraction,
                            capacity,
                            power,
                        ]
                    )
        return rows

    def check_curve_fit(self, coil, expected_type, indoor_is_wet_bulb):
        self.assertEqual(len(coil.capacity_temperature_params), 6)
        self.assertEqual(len(coil.capacity_flow_params), 3)
        self.assertEqual(len(coil.eir_temperature_params), 6)
        self.assertEqual(len(coil.eir_flow_params), 3)
        self.assertEqual(coil.headers().columns[1].wet_bulb_column_flag, indoor_is_wet_bulb)
        coil.set_required_constant_parameter(coil.rated_capacity_key, 12000.0)
        coil.set_required_constant_parameter(coil.rated_power_key, 3000.0)
        coil.set_required_constant_parameter(coil.rated_air_flow_key, 0.6)
        if coil.mode == "Heating":
            coil.set_required_constant_parameter(coil.minimum_outdoor_temperature_key, -25.0)
        self.check_interface(coil, expected_type)

        data_manager = CatalogDataManager()
        data_manager.final_data_matrix = self.catalog_rows(coil)
        progress = []
        completed = []
        coil.generate_parameters(
            data_manager,
            lambda: progress.append(True),
            lambda success: completed.append(success),
        )

        self.assertEqual(progress, [True, True, True])
        self.assertEqual(completed, [True])
        self.assertLess(coil.capacity_avg_err, 1e-6)
        self.assertLess(coil.eir_avg_err, 1e-6)
        for row, predicted, catalog in zip(
            data_manager.final_data_matrix, coil.predicted_capacity, coil.catalog_capacity
        ):
            self.assertAlmostEqual(predicted, catalog, places=5)
            indoor_temp = row[1]
            outdoor_temp = row[0]
            flow_fraction = row[2] / coil.rated_air_flow
            capacity_curve_value = coil._temperature_curve_value(
                coil.capacity_temperature_params, indoor_temp, outdoor_temp
            ) * coil._flow_curve_value(coil.capacity_flow_params, flow_fraction)
            eir_curve_value = coil._temperature_curve_value(
                coil.eir_temperature_params, indoor_temp, outdoor_temp
            ) * coil._flow_curve_value(coil.eir_flow_params, flow_fraction)
            self.assertAlmostEqual(
                capacity_curve_value,
                predicted / coil.rated_capacity,
                places=7,
            )
            self.assertAlmostEqual(
                eir_curve_value,
                (row[4] / row[3]) * (coil.rated_capacity / coil.rated_power),
                places=7,
            )
        for predicted, catalog in zip(coil.predicted_power, coil.catalog_power):
            self.assertAlmostEqual(predicted, catalog, places=5)

        epjson = json.loads(coil.to_eplus_epjson_object())
        self.assertIn(coil.coil_object_type, epjson)
        self.assertIn("Curve:Biquadratic", epjson)
        self.assertIn("Curve:Quadratic", epjson)
        self.assertIn(coil.capacity_temperature_curve_name, epjson["Curve:Biquadratic"])
        self.assertIn(coil.eir_flow_curve_name, epjson["Curve:Quadratic"])
        self.assertIn(coil.coil_object_type, coil.to_eplus_idf_object())
        coil_object = epjson[coil.coil_object_type][f"Your {coil.mode} Coil Name"]
        if coil.mode == "Heating":
            self.assertEqual(
                coil_object["minimum_outdoor_dry_bulb_temperature_for_compressor_operation"],
                -25.0,
            )
        self.assertAlmostEqual(
            coil._temperature_curve_value(
                coil.capacity_temperature_params,
                coil.rated_indoor_temperature,
                coil.rated_outdoor_temperature,
            ),
            1.0,
            places=8,
        )
        self.assertAlmostEqual(coil._flow_curve_value(coil.capacity_flow_params, 1.0), 1.0, places=8)

    def test_heating_curve_fit(self):
        coil = AirSourceHeatPumpHeatingCurveFit()
        self.check_curve_fit(coil, EquipType.ASHP_Heating_CurveFit, False)

    def test_cooling_curve_fit(self):
        coil = AirSourceHeatPumpCoolingCurveFit()
        self.check_curve_fit(coil, EquipType.ASHP_Cooling_CurveFit, True)
