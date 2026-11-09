from json import dumps
from typing import Callable, Dict, List, Tuple

from scipy.optimize import least_squares

from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.column_header import ColumnHeader, ColumnHeaderArray
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.exceptions import EnergyPlusPetException
from energyplus_pet.units import UnitType


class AirToWaterHeatPumpCurveFit(BaseEquipment):
    """Fits single-speed air-to-water heat-pump temperature curves."""

    energyplus_version = 25.2
    mode = ""
    equipment_type = EquipType.InvalidType
    capacity_label = ""
    power_label = ""
    rated_air_temperature_default = 0.0
    rated_water_temperature_default = 0.0
    capacity_curve_name = ""
    eir_curve_name = ""
    eir_plr_curve_name = ""

    def __init__(self):
        self.rated_capacity_key = "rated_capacity"
        self.rated_capacity = 10000.0
        self.rated_power_key = "rated_power"
        self.rated_power = 2500.0
        self.rated_air_flow_key = "rated_air_flow"
        self.rated_air_flow = 0.5
        self.rated_water_flow_key = "rated_water_flow"
        self.rated_water_flow = 0.0005
        self.rated_air_temperature_key = "rated_air_temperature"
        self.rated_air_temperature = self.rated_air_temperature_default
        self.rated_water_temperature_key = "rated_water_temperature"
        self.rated_water_temperature = self.rated_water_temperature_default
        self.catalog_capacity = []
        self.catalog_power = []
        self.capacity_curve_params = [0.0] * 6
        self.eir_curve_params = [0.0] * 6
        self.predicted_capacity = []
        self.predicted_power = []
        self.percent_error_capacity = []
        self.percent_error_power = []
        self.capacity_avg_err = 0.0
        self.eir_avg_err = 0.0
        self._headers = ColumnHeaderArray(
            [
                ColumnHeader("Outdoor Entering Dry-bulb Temperature", UnitType.Temperature),
                ColumnHeader("Leaving Water Temperature", UnitType.Temperature),
                ColumnHeader(self.capacity_label, UnitType.Power),
                ColumnHeader(self.power_label, UnitType.Power),
            ]
        )

    def this_type(self) -> EquipType:
        return self.equipment_type

    def name(self) -> str:
        return f"Air-to-Water Heat Pump, {self.mode} Mode, Single-Speed Curve Fit"

    def short_name(self) -> str:
        return f"AWHP-{self.mode}-CurveFit"

    def get_required_constant_parameters(self) -> List[BaseEquipment.RequiredConstantParameter]:
        return [
            BaseEquipment.RequiredConstantParameter(
                self.rated_capacity_key,
                f"Rated {self.capacity_label}",
                f"Rated {self.capacity_label.lower()} used to normalize the capacity curve",
                UnitType.Power,
                10000.0,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_power_key,
                f"Rated {self.power_label}",
                f"Rated {self.power_label.lower()} used to normalize the EIR curve",
                UnitType.Power,
                2500.0,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_air_flow_key,
                "Rated Air Flow Rate",
                "Rated outdoor air volume flow through the heat pump",
                UnitType.Flow,
                0.5,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_water_flow_key,
                "Rated Water Flow Rate",
                "Rated hot- or chilled-water volume flow through the heat pump",
                UnitType.Flow,
                0.0005,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_air_temperature_key,
                "Rated Outdoor Air Dry-bulb Temperature",
                "Outdoor air temperature used to normalize the performance curves",
                UnitType.Temperature,
                self.rated_air_temperature_default,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_water_temperature_key,
                "Rated Leaving Water Temperature",
                "Leaving water temperature used to normalize the performance curves",
                UnitType.Temperature,
                self.rated_water_temperature_default,
            ),
        ]

    def set_required_constant_parameter(self, parameter_id: str, new_value: float) -> None:
        if parameter_id == self.rated_capacity_key:
            self.rated_capacity = new_value
        elif parameter_id == self.rated_power_key:
            self.rated_power = new_value
        elif parameter_id == self.rated_air_flow_key:
            self.rated_air_flow = new_value
        elif parameter_id == self.rated_water_flow_key:
            self.rated_water_flow = new_value
        elif parameter_id == self.rated_air_temperature_key:
            self.rated_air_temperature = new_value
        elif parameter_id == self.rated_water_temperature_key:
            self.rated_water_temperature = new_value
        else:
            raise EnergyPlusPetException("Bad parameter ID in set_required_constant_parameter")

    def headers(self) -> ColumnHeaderArray:
        return self._headers

    def get_number_of_progress_steps(self) -> int:
        return 3

    def minimum_data_points_for_generation(self) -> int:
        return 6

    @staticmethod
    def _curve_value(params, air_temperature, water_temperature):
        return (
            params[0]
            + params[1] * air_temperature
            + params[2] * air_temperature ** 2
            + params[3] * water_temperature
            + params[4] * water_temperature ** 2
            + params[5] * air_temperature * water_temperature
        )

    @staticmethod
    def _fit_curve(air_temps, water_temps, outputs, rated_air_temp, rated_water_temp):
        air_delta = [value - rated_air_temp for value in air_temps]
        water_delta = [value - rated_water_temp for value in water_temps]

        def evaluate(parameters, index):
            a, b, c, d, e = parameters
            air_delta_i = air_delta[index]
            water_delta_i = water_delta[index]
            return (
                1.0
                + a * air_delta_i
                + b * air_delta_i ** 2
                + c * water_delta_i
                + d * water_delta_i ** 2
                + e * air_delta_i * water_delta_i
            )

        solution = least_squares(
            lambda parameters: [
                evaluate(parameters, i) - output for i, output in enumerate(outputs)
            ],
            [0.0] * 5,
            x_scale="jac",
        )
        if not solution.success:
            raise EnergyPlusPetException(f"Unable to fit air-to-water heat-pump curves: {solution.message}")

        a, b, c, d, e = solution.x
        curve_params = [
            1.0 - a * rated_air_temp + b * rated_air_temp ** 2
            - c * rated_water_temp + d * rated_water_temp ** 2
            + e * rated_air_temp * rated_water_temp,
            a - 2.0 * b * rated_air_temp - e * rated_water_temp,
            b,
            c - 2.0 * d * rated_water_temp - e * rated_air_temp,
            d,
            e,
        ]
        predictions = [evaluate(solution.x, i) for i in range(len(outputs))]
        rms_error = (
            sum((predicted - actual) ** 2 for predicted, actual in zip(predictions, outputs))
            / len(outputs)
        ) ** 0.5
        return curve_params, predictions, rms_error

    def generate_parameters(
        self,
        data_manager: CatalogDataManager,
        cb_progress_increment: Callable,
        cb_progress_done: Callable,
    ):
        if min(self.rated_capacity, self.rated_power, self.rated_air_flow, self.rated_water_flow) <= 0:
            raise EnergyPlusPetException("Rated capacity, power, and flow rates must be greater than zero")
        rows = data_manager.final_data_matrix
        if len(rows) < self.minimum_data_points_for_generation():
            raise EnergyPlusPetException(
                f"At least {self.minimum_data_points_for_generation()} catalog data points are required"
            )
        if any(row[2] <= 0 or row[3] <= 0 for row in rows):
            raise EnergyPlusPetException("Catalog capacity and power values must be greater than zero")

        air_temps = [row[0] for row in rows]
        water_temps = [row[1] for row in rows]
        self.catalog_capacity = [row[2] for row in rows]
        self.catalog_power = [row[3] for row in rows]
        capacity_fractions = [value / self.rated_capacity for value in self.catalog_capacity]
        eir_fractions = [
            (power / capacity) * (self.rated_capacity / self.rated_power)
            for power, capacity in zip(self.catalog_power, self.catalog_capacity)
        ]
        cb_progress_increment()

        self.capacity_curve_params, predicted_capacity_fractions, self.capacity_avg_err = self._fit_curve(
            air_temps,
            water_temps,
            capacity_fractions,
            self.rated_air_temperature,
            self.rated_water_temperature,
        )
        cb_progress_increment()

        self.eir_curve_params, predicted_eir_fractions, self.eir_avg_err = self._fit_curve(
            air_temps,
            water_temps,
            eir_fractions,
            self.rated_air_temperature,
            self.rated_water_temperature,
        )
        cb_progress_increment()

        self.predicted_capacity = [value * self.rated_capacity for value in predicted_capacity_fractions]
        self.predicted_power = [
            capacity * eir * self.rated_power / self.rated_capacity
            for capacity, eir in zip(self.predicted_capacity, predicted_eir_fractions)
        ]
        self.percent_error_capacity = [
            100.0 * (predicted - actual) / actual
            for predicted, actual in zip(self.predicted_capacity, self.catalog_capacity)
        ]
        self.percent_error_power = [
            100.0 * (predicted - actual) / actual
            for predicted, actual in zip(self.predicted_power, self.catalog_power)
        ]
        cb_progress_done(True)

    def get_absolute_plot_data(self) -> Tuple:
        return (
            (f"{self.mode} Capacity Model", "line", "red", self.predicted_capacity),
            (f"{self.mode} Capacity Catalog", "point", "red", self.catalog_capacity),
            (f"{self.mode} Power Model", "line", "green", self.predicted_power),
            (f"{self.mode} Power Catalog", "point", "green", self.catalog_power),
        )

    def get_error_plot_data(self) -> Tuple:
        return (
            (f"{self.mode} Capacity % Error", "line", "red", self.percent_error_capacity),
            (f"{self.mode} Power % Error", "line", "green", self.percent_error_power),
        )

    def get_extra_regression_metrics(self) -> Tuple:
        return (
            ("Capacity curve-fit RMS error (fraction)", self.capacity_avg_err),
            ("EIR curve-fit RMS error (fraction)", self.eir_avg_err),
        )

    @staticmethod
    def _curve_idf_object(name: str, params: List[float], biquadratic: bool) -> str:
        if biquadratic:
            fields = [
                ("Name", name),
                *[(f"Coefficient{i + 1}", value) for i, value in enumerate(params)],
                ("Minimum Value of x", -100),
                ("Maximum Value of x", 100),
                ("Minimum Value of y", -100),
                ("Maximum Value of y", 100),
                ("Minimum Curve Output", 0),
                ("Maximum Curve Output", 10),
            ]
            return BaseEquipment.fill_eplus_object_format("Curve:Biquadratic", fields)
        fields = [
            ("Name", name),
            *[(f"Coefficient{i + 1}", value) for i, value in enumerate(params)],
            ("Minimum Value of x", 0),
            ("Maximum Value of x", 1),
            ("Minimum Curve Output", 0),
            ("Maximum Curve Output", 10),
        ]
        return BaseEquipment.fill_eplus_object_format("Curve:Quadratic", fields)

    def _idf_heat_pump_fields(self) -> List[Tuple[str, object]]:
        is_heating = self.mode == "Heating"
        fields = [
            ("Name", f"Your {self.mode} Heat Pump Name"),
            ("Availability Schedule Name Heating", ""),
            ("Availability Schedule Name Cooling", ""),
            ("Operating Mode Control Method", "Load"),
            ("Operating Mode Control Option for Multiple Unit", "SingleMode"),
            ("Operating Mode Control Schedule Name", ""),
            ("Minimum Part Load Ratio", 0.0),
            ("Rated Inlet Air Temperature in Heating Mode", self.rated_air_temperature if is_heating else ""),
            ("Rated Air Flow Rate in Heating Mode", self.rated_air_flow if is_heating else ""),
            ("Rated Leaving Water Temperature in Heating Mode", self.rated_water_temperature if is_heating else ""),
            ("Rated Water Flow Rate in Heating Mode", self.rated_water_flow if is_heating else ""),
            ("Minimum Outdoor Air Temperature in Heating Mode", ""),
            ("Maximum Outdoor Air Temperature in Heating Mode", ""),
            ("Minimum Leaving Water Temperature Curve Name in Heating Mode", ""),
            ("Maximum Leaving Water Temperature Curve Name in Heating Mode", ""),
            ("Sizing Factor for Heating", 1.0),
            ("Rated Inlet Air Temperature in Cooling Mode", self.rated_air_temperature if not is_heating else ""),
            ("Rated Air Flow Rate in Cooling Mode", self.rated_air_flow if not is_heating else ""),
            ("Rated Leaving Water Temperature in Cooling Mode", self.rated_water_temperature if not is_heating else ""),
            ("Rated Water Flow Rate in Cooling Mode", self.rated_water_flow if not is_heating else ""),
            ("Minimum Outdoor Air Temperature in Cooling Mode", ""),
            ("Maximum Outdoor Air Temperature in Cooling Mode", ""),
            ("Minimum Leaving Water Temperature Curve Name in Cooling Mode", ""),
            ("Maximum Leaving Water Temperature Curve Name in Cooling Mode", ""),
            ("Sizing Factor for Cooling", 1.0),
            ("Air Inlet Node Name", "Your Heat Pump Air Inlet Node"),
            ("Air Outlet Node Name", "Your Heat Pump Air Outlet Node"),
            ("Hot Water Inlet Node Name", "Your Heat Pump Hot Water Inlet Node" if is_heating else ""),
            ("Hot Water Outlet Node Name", "Your Heat Pump Hot Water Outlet Node" if is_heating else ""),
            ("Chilled Water Inlet Node Name", "" if is_heating else "Your Heat Pump Chilled Water Inlet Node"),
            ("Chilled Water Outlet Node Name", "" if is_heating else "Your Heat Pump Chilled Water Outlet Node"),
            ("Maximum Outdoor Dry Bulb Temperature For Defrost Operation", 10.0),
            ("Heat Pump Defrost Control", "None"),
            ("Heat Pump Defrost Time Period Fraction", 0.058333),
            ("Resistive Defrost Heater Capacity", 0.0),
            ("Defrost Energy Input Ratio Function of Temperature Curve Name", ""),
            ("Heat Pump Multiplier", 1),
            ("Control Type", "FixedSpeed"),
            ("Crankcase Heater Capacity", 0.0),
            ("Crankcase Heater Capacity Function of Temperature Curve Name", ""),
            ("Maximum Ambient Temperature for Crankcase Heater Operation", 10.0),
            ("Number of Speeds for Heating", 1 if is_heating else 0),
        ]
        for speed in range(1, 6):
            selected = is_heating and speed == 1
            fields.extend(
                [
                    (f"Rated Heating Capacity at Speed {speed}", self.rated_capacity if selected else ""),
                    (
                        f"Rated COP for Heating at Speed {speed}",
                        self.rated_capacity / self.rated_power if selected else "",
                    ),
                    (
                        f"Normalized Heating Capacity Function of Temperature Curve Name at Speed {speed}",
                        self.capacity_curve_name if selected else "",
                    ),
                    (
                        f"Heating Energy Input Ratio Function of Temperature Curve Name at Speed {speed}",
                        self.eir_curve_name if selected else "",
                    ),
                    (
                        f"Heating Energy Input Ratio Function of PLR Curve Name at Speed {speed}",
                        self.eir_plr_curve_name if selected else "",
                    ),
                ]
            )
        fields.extend(
            [
                ("Booster Mode On Heating", "No"),
                ("Rated Heating Capacity in Booster Mode", ""),
                ("Rated Heating COP in Booster Mode", ""),
                ("Normalized Heating Capacity Function of Temperature Curve Name in Booster Mode", ""),
                ("Heating Energy Input Ratio Function of Temperature Curve Name in Booster Mode", ""),
                ("Heating Energy Input Ratio Function of PLR Curve Name in Booster Mode", ""),
                ("Number of Speeds for Cooling", 0 if is_heating else 1),
            ]
        )
        fields.extend(
            [
                ("Rated Cooling Capacity at Speed 1", self.rated_capacity if not is_heating else ""),
                ("Rated COP for Cooling at Speed 1", self.rated_capacity / self.rated_power if not is_heating else ""),
                (
                    "Normalized Cooling Capacity Function of Temperature Curve Name at Speed 1",
                    self.capacity_curve_name if not is_heating else "",
                ),
                (
                    "Cooling Energy Input Ratio Function of Temperature Curve Name at Speed 1",
                    self.eir_curve_name if not is_heating else "",
                ),
                (
                    "Cooling Energy Input Ratio Function of PLR Curve Name at Speed 1",
                    self.eir_plr_curve_name if not is_heating else "",
                ),
            ]
        )
        return fields

    def to_eplus_idf_object(self) -> str:
        curves = [
            self._curve_idf_object(self.capacity_curve_name, self.capacity_curve_params, True),
            self._curve_idf_object(self.eir_curve_name, self.eir_curve_params, True),
            self._curve_idf_object(self.eir_plr_curve_name, [1.0, 0.0, 0.0], False),
        ]
        return "\n".join(
            [
                self.current_eplus_version_object_idf(self.energyplus_version),
                self.fill_eplus_object_format("HeatPump:AirToWater", self._idf_heat_pump_fields()),
                *curves,
            ]
        )

    @staticmethod
    def _epjson_biquadratic(params: List[float]) -> Dict:
        return {
            "coefficient1_constant": params[0],
            "coefficient2_x": params[1],
            "coefficient3_x_x": params[2],
            "coefficient4_y": params[3],
            "coefficient5_y_y": params[4],
            "coefficient6_x_y": params[5],
            "minimum_value_of_x": -100,
            "maximum_value_of_x": 100,
            "minimum_value_of_y": -100,
            "maximum_value_of_y": 100,
            "minimum_curve_output": 0,
            "maximum_curve_output": 10,
        }

    def to_eplus_epjson_object(self) -> str:
        is_heating = self.mode == "Heating"
        heat_pump = {
            "availability_schedule_name_heating": "",
            "availability_schedule_name_cooling": "",
            "operating_mode_control_method": "Load",
            "operating_mode_control_option_for_multiple_unit": "SingleMode",
            "minimum_part_load_ratio": 0.0,
            "air_inlet_node_name": "Your Heat Pump Air Inlet Node",
            "air_outlet_node_name": "Your Heat Pump Air Outlet Node",
            "control_type": "FixedSpeed",
            "number_of_speeds_for_heating": 1 if is_heating else 0,
            "number_of_speeds_for_cooling": 0 if is_heating else 1,
        }
        if is_heating:
            heat_pump.update(
                {
                    "rated_inlet_air_temperature_in_heating_mode": self.rated_air_temperature,
                    "rated_air_flow_rate_in_heating_mode": self.rated_air_flow,
                    "rated_leaving_water_temperature_in_heating_mode": self.rated_water_temperature,
                    "rated_water_flow_rate_in_heating_mode": self.rated_water_flow,
                    "hot_water_inlet_node_name": "Your Heat Pump Hot Water Inlet Node",
                    "hot_water_outlet_node_name": "Your Heat Pump Hot Water Outlet Node",
                    "rated_heating_capacity_at_speed_1": self.rated_capacity,
                    "rated_cop_for_heating_at_speed_1": self.rated_capacity / self.rated_power,
                    "normalized_heating_capacity_function_of_temperature_curve_name_at_speed_1":
                        self.capacity_curve_name,
                    "heating_energy_input_ratio_function_of_temperature_curve_name_at_speed_1":
                        self.eir_curve_name,
                    "heating_energy_input_ratio_function_of_plr_curve_name_at_speed_1":
                        self.eir_plr_curve_name,
                }
            )
        else:
            heat_pump.update(
                {
                    "rated_inlet_air_temperature_in_cooling_mode": self.rated_air_temperature,
                    "rated_air_flow_rate_in_cooling_mode": self.rated_air_flow,
                    "rated_leaving_water_temperature_in_cooling_mode": self.rated_water_temperature,
                    "rated_water_flow_rate_in_cooling_mode": self.rated_water_flow,
                    "chilled_water_inlet_node_name": "Your Heat Pump Chilled Water Inlet Node",
                    "chilled_water_outlet_node_name": "Your Heat Pump Chilled Water Outlet Node",
                    "rated_cooling_capacity_at_speed_1": self.rated_capacity,
                    "rated_cop_for_cooling_at_speed_1": self.rated_capacity / self.rated_power,
                    "normalized_cooling_capacity_function_of_temperature_curve_name_at_speed_1":
                        self.capacity_curve_name,
                    "cooling_energy_input_ratio_function_of_temperature_curve_name_at_speed_1":
                        self.eir_curve_name,
                    "cooling_energy_input_ratio_function_of_plr_curve_name_at_speed_1":
                        self.eir_plr_curve_name,
                }
            )
        epjson = {
            **self.current_eplus_version_object_epjson(self.energyplus_version),
            "HeatPump:AirToWater": {f"Your {self.mode} Heat Pump Name": heat_pump},
            "Curve:Biquadratic": {
                self.capacity_curve_name: self._epjson_biquadratic(self.capacity_curve_params),
                self.eir_curve_name: self._epjson_biquadratic(self.eir_curve_params),
            },
            "Curve:Quadratic": {
                self.eir_plr_curve_name: {
                    "coefficient1_constant": 1.0,
                    "coefficient2_x": 0.0,
                    "coefficient3_x_x": 0.0,
                    "minimum_value_of_x": 0,
                    "maximum_value_of_x": 1,
                    "minimum_curve_output": 0,
                    "maximum_curve_output": 10,
                }
            },
        }
        return dumps(epjson, indent=2)

    def to_parameter_summary(self) -> str:
        output = f"""{self.name()}
**Begin Nomenclature**
CAP: {self.mode} Capacity
EIR: Energy Input Ratio
OAT: Outdoor Entering Dry-bulb Temperature
LWT: Leaving Water Temperature
**End Nomenclature**

**Begin Governing Equations**
CAP/CAP_R = CAP_T(OAT, LWT)
EIR/EIR_R = EIR_T(OAT, LWT)
**End Governing Equations**

**Begin Reporting Parameters**
Rated {self.capacity_label}: {self.rated_capacity}
Rated {self.power_label}: {self.rated_power}
Rated Air Flow Rate: {self.rated_air_flow}
Rated Water Flow Rate: {self.rated_water_flow}
Rated Outdoor Air Dry-bulb Temperature: {self.rated_air_temperature}
Rated Leaving Water Temperature: {self.rated_water_temperature}
"""
        for curve_name, params in (
            ("Capacity Temperature", self.capacity_curve_params),
            ("EIR Temperature", self.eir_curve_params),
        ):
            output += f"{curve_name} Curve Coefficients: "
            output += ", ".join(str(round(value, 6)) for value in params) + "\n"
        return output + "**End Reporting Parameters**"


class AirToWaterHeatPumpHeatingCurveFit(AirToWaterHeatPumpCurveFit):
    mode = "Heating"
    equipment_type = EquipType.AWHP_Heating_CurveFit
    capacity_label = "Heating Capacity"
    power_label = "Heating Power"
    rated_air_temperature_default = 8.0
    rated_water_temperature_default = 40.0
    capacity_curve_name = "HeatingCapacityTemperatureCurve"
    eir_curve_name = "HeatingEIRTemperatureCurve"
    eir_plr_curve_name = "HeatingEIRPLRCurve"


class AirToWaterHeatPumpCoolingCurveFit(AirToWaterHeatPumpCurveFit):
    mode = "Cooling"
    equipment_type = EquipType.AWHP_Cooling_CurveFit
    capacity_label = "Cooling Capacity"
    power_label = "Cooling Power"
    rated_air_temperature_default = 30.0
    rated_water_temperature_default = 8.0
    capacity_curve_name = "CoolingCapacityTemperatureCurve"
    eir_curve_name = "CoolingEIRTemperatureCurve"
    eir_plr_curve_name = "CoolingEIRPLRCurve"
