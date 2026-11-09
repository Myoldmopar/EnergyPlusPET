import json

from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.awhp_curve import (
    AirToWaterHeatPumpCoolingCurveFit,
    AirToWaterHeatPumpHeatingCurveFit,
)
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.tests.equipment.equipment_test_helper import EquipmentTestHelper


class TestAirToWaterHeatPumpCurve(EquipmentTestHelper):
    @staticmethod
    def catalog_rows(coil):
        rows = []
        rated_air = coil.rated_air_temperature
        rated_water = coil.rated_water_temperature
        for air_temperature in (rated_air - 10, rated_air, rated_air + 10):
            for water_temperature in (rated_water - 5, rated_water, rated_water + 5):
                air_delta = air_temperature - rated_air
                water_delta = water_temperature - rated_water
                capacity_fraction = (
                    1
                    + 0.01 * air_delta
                    - 0.0002 * air_delta ** 2
                    - 0.005 * water_delta
                    + 0.0001 * water_delta ** 2
                    + 0.00002 * air_delta * water_delta
                )
                eir_fraction = (
                    1
                    - 0.007 * air_delta
                    + 0.0002 * air_delta ** 2
                    + 0.01 * water_delta
                    + 0.0001 * water_delta ** 2
                    - 0.00001 * air_delta * water_delta
                )
                capacity = coil.rated_capacity * capacity_fraction
                power = coil.rated_power * capacity_fraction * eir_fraction
                rows.append([air_temperature, water_temperature, capacity, power])
        return rows

    @staticmethod
    def idf_values(idf_text):
        object_text = idf_text.split("HeatPump:AirToWater,\n", 1)[1].split("Curve:Biquadratic,", 1)[0]
        return [
            line.partition("!-")[0].strip().rstrip(",;")
            for line in object_text.splitlines()
            if "!-" in line
        ]

    def check_curve_fit(self, coil, expected_type, is_heating):
        self.assertEqual(len(coil.capacity_curve_params), 6)
        self.assertEqual(len(coil.eir_curve_params), 6)
        coil.set_required_constant_parameter(coil.rated_capacity_key, 12000.0)
        coil.set_required_constant_parameter(coil.rated_power_key, 3000.0)
        coil.set_required_constant_parameter(coil.rated_air_flow_key, 0.6)
        coil.set_required_constant_parameter(coil.rated_water_flow_key, 0.0007)
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
        self.assertLess(coil.capacity_avg_err, 1e-8)
        self.assertLess(coil.eir_avg_err, 1e-8)
        for row, predicted_capacity, predicted_power in zip(
            data_manager.final_data_matrix, coil.predicted_capacity, coil.predicted_power
        ):
            capacity_fraction = self._curve_value(
                coil.capacity_curve_params, row[0], row[1]
            )
            eir_fraction = self._curve_value(coil.eir_curve_params, row[0], row[1])
            self.assertAlmostEqual(predicted_capacity, row[2], places=5)
            self.assertAlmostEqual(predicted_power, row[3], places=5)
            self.assertAlmostEqual(capacity_fraction, row[2] / coil.rated_capacity, places=7)
            self.assertAlmostEqual(
                eir_fraction,
                (row[3] / row[2]) * (coil.rated_capacity / coil.rated_power),
                places=7,
            )
        self.assertAlmostEqual(
            self._curve_value(
                coil.capacity_curve_params,
                coil.rated_air_temperature,
                coil.rated_water_temperature,
            ),
            1.0,
            places=8,
        )

        epjson = json.loads(coil.to_eplus_epjson_object())
        self.assertEqual(epjson["Version"]["Version 1"]["version_identifier"], 25.2)
        self.assertIn("HeatPump:AirToWater", epjson)
        self.assertIn("Curve:Biquadratic", epjson)
        self.assertIn("Curve:Quadratic", epjson)
        heat_pump = epjson["HeatPump:AirToWater"][f"Your {coil.mode} Heat Pump Name"]
        if is_heating:
            self.assertEqual(heat_pump["number_of_speeds_for_heating"], 1)
            self.assertEqual(heat_pump["number_of_speeds_for_cooling"], 0)
            self.assertEqual(
                heat_pump["normalized_heating_capacity_function_of_temperature_curve_name_at_speed_1"],
                coil.capacity_curve_name,
            )
        else:
            self.assertEqual(heat_pump["number_of_speeds_for_heating"], 0)
            self.assertEqual(heat_pump["number_of_speeds_for_cooling"], 1)
            self.assertEqual(
                heat_pump["normalized_cooling_capacity_function_of_temperature_curve_name_at_speed_1"],
                coil.capacity_curve_name,
            )

        idf = coil.to_eplus_idf_object()
        self.assertIn("Version Identifier", idf)
        self.assertIn("25.2", idf.split("HeatPump:AirToWater", 1)[0])
        self.assertIn("HeatPump:AirToWater", idf)
        idf_fields = self.idf_values(idf)
        self.assertEqual(len(idf_fields), 79)
        self.assertEqual(idf_fields[37], "FixedSpeed")
        if is_heating:
            self.assertEqual(idf_fields[41], "1")
            self.assertEqual(idf_fields[73], "0")
            self.assertEqual(idf_fields[44], coil.capacity_curve_name)
        else:
            self.assertEqual(idf_fields[41], "0")
            self.assertEqual(idf_fields[73], "1")
            self.assertEqual(idf_fields[76], coil.capacity_curve_name)

    @staticmethod
    def _curve_value(params, air_temperature, water_temperature):
        return AirToWaterHeatPumpHeatingCurveFit._curve_value(
            params, air_temperature, water_temperature
        )

    def test_heating_curve_fit(self):
        self.check_curve_fit(
            AirToWaterHeatPumpHeatingCurveFit(),
            EquipType.AWHP_Heating_CurveFit,
            True,
        )

    def test_cooling_curve_fit(self):
        self.check_curve_fit(
            AirToWaterHeatPumpCoolingCurveFit(),
            EquipType.AWHP_Cooling_CurveFit,
            False,
        )
