from json import dumps
from typing import Callable, List, Tuple

from scipy.optimize import least_squares

from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.column_header import ColumnHeader, ColumnHeaderArray
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.exceptions import EnergyPlusPetException
from energyplus_pet.units import UnitType


class AirSourceHeatPumpCurveFit(BaseEquipment):
    """Fits EnergyPlus single-speed DX heat-pump temperature and airflow curves."""

    mode = ""
    equipment_type = EquipType.InvalidType
    coil_object_type = ""
    capacity_label = ""
    power_label = ""
    indoor_temperature_label = ""
    indoor_temperature_default = 0.0
    outdoor_temperature_default = 0.0
    capacity_temperature_curve_name = ""
    capacity_flow_curve_name = ""
    eir_temperature_curve_name = ""
    eir_flow_curve_name = ""

    def __init__(self):
        self.rated_capacity_key = "capacity"
        self.rated_capacity = 10000.0
        self.rated_power_key = "power"
        self.rated_power = 2500.0
        self.rated_air_flow_key = "air_flow"
        self.rated_air_flow = 0.5
        self.rated_indoor_temperature_key = "indoor_temperature"
        self.rated_indoor_temperature = self.indoor_temperature_default
        self.rated_outdoor_temperature_key = "outdoor_temperature"
        self.rated_outdoor_temperature = self.outdoor_temperature_default
        self.minimum_outdoor_temperature_key = "minimum_outdoor_temperature"
        self.minimum_outdoor_temperature = -25.0
        self.rated_shr_key = "shr"
        self.rated_shr = 0.75
        self.catalog_capacity = []
        self.catalog_power = []
        self.capacity_temperature_params = [0.0] * 6
        self.capacity_flow_params = [1.0, 0.0, 0.0]
        self.eir_temperature_params = [0.0] * 6
        self.eir_flow_params = [1.0, 0.0, 0.0]
        self.predicted_capacity = []
        self.predicted_power = []
        self.percent_error_capacity = []
        self.percent_error_power = []
        self.capacity_avg_err = 0.0
        self.eir_avg_err = 0.0
        indoor_temp_is_wet_bulb = self.mode == "Cooling"
        self._headers = ColumnHeaderArray(
            [
                ColumnHeader("Outdoor Entering Dry-bulb Temp", UnitType.Temperature),
                ColumnHeader(
                    self.indoor_temperature_label,
                    UnitType.Temperature,
                    db=not indoor_temp_is_wet_bulb,
                    wb=indoor_temp_is_wet_bulb,
                ),
                ColumnHeader("Air-side Volume Flow", UnitType.Flow),
                ColumnHeader(self.capacity_label, UnitType.Power),
                ColumnHeader(self.power_label, UnitType.Power),
            ]
        )

    def this_type(self) -> EquipType:
        return self.equipment_type

    def name(self) -> str:
        return f"Air Source Heat Pump, {self.mode} Mode, Single-Speed Curve Fit"

    def short_name(self) -> str:
        return f"ASHP-{self.mode}-CurveFit"

    def get_required_constant_parameters(self) -> List[BaseEquipment.RequiredConstantParameter]:
        parameters = [
            BaseEquipment.RequiredConstantParameter(
                self.rated_capacity_key,
                f"Rated {self.capacity_label}",
                f"Rated {self.capacity_label.lower()} for the coil",
                UnitType.Power,
                10000.0,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_power_key,
                f"Rated {self.power_label}",
                f"Rated {self.power_label.lower()} for the coil",
                UnitType.Power,
                2500.0,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_air_flow_key,
                "Rated Air Flow Rate",
                "Rated indoor air volume flow through the coil",
                UnitType.Flow,
                0.5,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_indoor_temperature_key,
                f"Rated Indoor {self.indoor_temperature_label}",
                "Indoor entering-air temperature used to normalize the temperature curves",
                UnitType.Temperature,
                self.indoor_temperature_default,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_outdoor_temperature_key,
                "Rated Outdoor Dry-bulb Temperature",
                "Outdoor entering-air temperature used to normalize the temperature curves",
                UnitType.Temperature,
                self.outdoor_temperature_default,
            ),
        ]
        if self.mode == "Heating":
            parameters.append(
                BaseEquipment.RequiredConstantParameter(
                    self.minimum_outdoor_temperature_key,
                    "Minimum Outdoor Dry-bulb Temperature for Compressor Operation",
                    "The lowest outdoor temperature at which the compressor can operate",
                    UnitType.Temperature,
                    self.minimum_outdoor_temperature,
                )
            )
        if self.mode == "Cooling":
            parameters.append(
                BaseEquipment.RequiredConstantParameter(
                    self.rated_shr_key,
                    "Rated Sensible Heat Ratio",
                    "Rated sensible cooling capacity divided by rated total cooling capacity",
                    UnitType.Dimensionless,
                    self.rated_shr,
                )
            )
        return parameters

    def set_required_constant_parameter(self, parameter_id: str, new_value: float) -> None:
        if parameter_id == self.rated_capacity_key:
            self.rated_capacity = new_value
        elif parameter_id == self.rated_power_key:
            self.rated_power = new_value
        elif parameter_id == self.rated_air_flow_key:
            self.rated_air_flow = new_value
        elif parameter_id == self.rated_indoor_temperature_key:
            self.rated_indoor_temperature = new_value
        elif parameter_id == self.rated_outdoor_temperature_key:
            self.rated_outdoor_temperature = new_value
        elif parameter_id == self.minimum_outdoor_temperature_key and self.mode == "Heating":
            self.minimum_outdoor_temperature = new_value
        elif parameter_id == self.rated_shr_key and self.mode == "Cooling":
            self.rated_shr = new_value
        else:
            raise EnergyPlusPetException("Bad parameter ID in set_required_constant_parameter")

    def headers(self) -> ColumnHeaderArray:
        return self._headers

    def get_number_of_progress_steps(self) -> int:
        return 3

    def minimum_data_points_for_generation(self) -> int:
        return 7

    @staticmethod
    def _temperature_curve_value(params, indoor_temp, outdoor_temp):
        return (
            params[0]
            + params[1] * indoor_temp
            + params[2] * indoor_temp ** 2
            + params[3] * outdoor_temp
            + params[4] * outdoor_temp ** 2
            + params[5] * indoor_temp * outdoor_temp
        )

    @staticmethod
    def _flow_curve_value(params, flow_fraction):
        return params[0] + params[1] * flow_fraction + params[2] * flow_fraction ** 2

    @staticmethod
    def _fit_curves(indoor_temps, outdoor_temps, flow_fractions, outputs, rated_indoor, rated_outdoor):
        """Fit normalized biquadratic temperature and quadratic flow curves."""
        indoor_delta = [value - rated_indoor for value in indoor_temps]
        outdoor_delta = [value - rated_outdoor for value in outdoor_temps]
        flow_delta = [value - 1.0 for value in flow_fractions]

        def evaluate(parameters, index):
            a, b, c, d, e, f, g = parameters
            temp_modifier = (
                1.0
                + a * indoor_delta[index]
                + b * indoor_delta[index] ** 2
                + c * outdoor_delta[index]
                + d * outdoor_delta[index] ** 2
                + e * indoor_delta[index] * outdoor_delta[index]
            )
            flow_modifier = 1.0 + f * flow_delta[index] + g * flow_delta[index] ** 2
            return temp_modifier * flow_modifier

        solution = least_squares(
            lambda parameters: [
                evaluate(parameters, i) - output for i, output in enumerate(outputs)
            ],
            [0.0] * 7,
            x_scale="jac",
        )
        if not solution.success:
            raise EnergyPlusPetException(f"Unable to fit air-source heat-pump curves: {solution.message}")

        a, b, c, d, e, f, g = solution.x
        temperature_params = [
            1.0 - a * rated_indoor + b * rated_indoor ** 2
            - c * rated_outdoor + d * rated_outdoor ** 2
            + e * rated_indoor * rated_outdoor,
            a - 2.0 * b * rated_indoor - e * rated_outdoor,
            b,
            c - 2.0 * d * rated_outdoor - e * rated_indoor,
            d,
            e,
        ]
        flow_params = [1.0 - f + g, f - 2.0 * g, g]
        predictions = [evaluate(solution.x, i) for i in range(len(outputs))]
        rms_error = (
            sum((predicted - actual) ** 2 for predicted, actual in zip(predictions, outputs))
            / len(outputs)
        ) ** 0.5
        return temperature_params, flow_params, predictions, rms_error

    def generate_parameters(
        self,
        data_manager: CatalogDataManager,
        cb_progress_increment: Callable,
        cb_progress_done: Callable,
    ):
        if self.rated_capacity <= 0 or self.rated_power <= 0 or self.rated_air_flow <= 0:
            raise EnergyPlusPetException("Rated capacity, power, and air flow must be greater than zero")
        if len(data_manager.final_data_matrix) < self.minimum_data_points_for_generation():
            raise EnergyPlusPetException(
                f"At least {self.minimum_data_points_for_generation()} catalog data points are required"
            )
        if self.mode == "Cooling" and not 0.5 <= self.rated_shr <= 1.0:
            raise EnergyPlusPetException("Rated sensible heat ratio must be between 0.5 and 1.0")
        for row in data_manager.final_data_matrix:
            if row[2] <= 0 or row[3] <= 0 or row[4] <= 0:
                raise EnergyPlusPetException("Catalog flow, capacity, and power values must be greater than zero")

        self.catalog_capacity = [row[3] for row in data_manager.final_data_matrix]
        self.catalog_power = [row[4] for row in data_manager.final_data_matrix]
        outdoor_temps = [row[0] for row in data_manager.final_data_matrix]
        indoor_temps = [row[1] for row in data_manager.final_data_matrix]
        flow_fractions = [row[2] / self.rated_air_flow for row in data_manager.final_data_matrix]
        capacity_fractions = [value / self.rated_capacity for value in self.catalog_capacity]
        eir_fractions = [
            (power / capacity) * (self.rated_capacity / self.rated_power)
            for power, capacity in zip(self.catalog_power, self.catalog_capacity)
        ]
        cb_progress_increment()

        (
            self.capacity_temperature_params,
            self.capacity_flow_params,
            predicted_capacity_fractions,
            self.capacity_avg_err,
        ) = self._fit_curves(
            indoor_temps,
            outdoor_temps,
            flow_fractions,
            capacity_fractions,
            self.rated_indoor_temperature,
            self.rated_outdoor_temperature,
        )
        cb_progress_increment()

        (
            self.eir_temperature_params,
            self.eir_flow_params,
            predicted_eir_fractions,
            self.eir_avg_err,
        ) = self._fit_curves(
            indoor_temps,
            outdoor_temps,
            flow_fractions,
            eir_fractions,
            self.rated_indoor_temperature,
            self.rated_outdoor_temperature,
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

    def _curve_idf_objects(self):
        temperature_limits = [
            ("Minimum Value of x", -100),
            ("Maximum Value of x", 100),
            ("Minimum Value of y", -100),
            ("Maximum Value of y", 100),
            ("Minimum Curve Output", 0),
            ("Maximum Curve Output", 10),
        ]
        flow_limits = [
            ("Minimum Value of x", 0),
            ("Maximum Value of x", 2),
            ("Minimum Curve Output", 0),
            ("Maximum Curve Output", 10),
        ]
        curves = (
            (
                "Curve:Biquadratic",
                self.capacity_temperature_curve_name,
                self.capacity_temperature_params,
                temperature_limits,
            ),
            (
                "Curve:Quadratic",
                self.capacity_flow_curve_name,
                self.capacity_flow_params,
                flow_limits,
            ),
            (
                "Curve:Biquadratic",
                self.eir_temperature_curve_name,
                self.eir_temperature_params,
                temperature_limits,
            ),
            ("Curve:Quadratic", self.eir_flow_curve_name, self.eir_flow_params, flow_limits),
            ("Curve:Quadratic", "PartLoadFractionCurve", [1.0, 0.0, 0.0], flow_limits),
        )
        output = []
        for object_type, name, coefficients, limits in curves:
            fields = [("Name", name)]
            fields.extend((f"Coefficient{i + 1}", value) for i, value in enumerate(coefficients))
            fields.extend(limits)
            output.append(self.fill_eplus_object_format(object_type, fields))
        return output

    def _coil_idf_object(self):
        fields = [
            ("Name", f"Your {self.mode} Coil Name"),
            ("Availability Schedule Name", ""),
        ]
        if self.mode == "Heating":
            fields.extend(
                [
                    ("Gross Rated Heating Capacity", self.rated_capacity),
                    ("Gross Rated Heating COP", self.rated_capacity / self.rated_power),
                    ("Rated Air Flow Rate", self.rated_air_flow),
                    ("2017 Rated Supply Fan Power Per Volume Flow Rate", ""),
                    ("2023 Rated Supply Fan Power Per Volume Flow Rate", ""),
                    ("Air Inlet Node Name", "Your Coil Air Inlet Node"),
                    ("Air Outlet Node Name", "Your Coil Air Outlet Node"),
                    (
                        "Heating Capacity Function of Temperature Curve Name",
                        self.capacity_temperature_curve_name,
                    ),
                    (
                        "Heating Capacity Function of Flow Fraction Curve Name",
                        self.capacity_flow_curve_name,
                    ),
                    ("Energy Input Ratio Function of Temperature Curve Name", self.eir_temperature_curve_name),
                    ("Energy Input Ratio Function of Flow Fraction Curve Name", self.eir_flow_curve_name),
                    ("Part Load Fraction Correlation Curve Name", "PartLoadFractionCurve"),
                    ("Defrost Energy Input Ratio Function of Temperature Curve Name", ""),
                    (
                        "Minimum Outdoor Dry-Bulb Temperature for Compressor Operation",
                        self.minimum_outdoor_temperature,
                    ),
                    ("Outdoor Dry-Bulb Temperature to Turn On Compressor", ""),
                    ("Maximum Outdoor Dry-Bulb Temperature for Defrost Operation", ""),
                    ("Crankcase Heater Capacity", 0.0),
                    ("Maximum Outdoor Dry-Bulb Temperature for Crankcase Heater Operation", 10.0),
                    ("Defrost Strategy", "Resistive"),
                    ("Defrost Control", "Timed"),
                    ("Defrost Time Period Fraction", 0.058333),
                    ("Resistive Defrost Heater Capacity", 0.0),
                    ("Region number for calculating HSPF", 4),
                    ("Evaporator Air Inlet Node Name", ""),
                    ("Zone Name for Evaporator Placement", ""),
                    ("Secondary Coil Air Flow Rate", ""),
                    ("Secondary Coil Fan Flow Scaling Factor", ""),
                    ("Nominal Sensible Heat Ratio of Secondary Coil", ""),
                    ("Sensible Heat Ratio Modifier Function of Temperature Curve Name", ""),
                    ("Sensible Heat Ratio Modifier Function of Flow Fraction Curve Name", ""),
                ]
            )
        else:
            fields.extend(
                [
                    ("Gross Rated Total Cooling Capacity", self.rated_capacity),
                    ("Gross Rated Sensible Heat Ratio", self.rated_shr),
                    ("Gross Rated Cooling COP", self.rated_capacity / self.rated_power),
                    ("Rated Air Flow Rate", self.rated_air_flow),
                    ("2017 Rated Evaporator Fan Power Per Volume Flow Rate", ""),
                    ("2023 Rated Evaporator Fan Power Per Volume Flow Rate", ""),
                    ("Air Inlet Node Name", "Your Coil Air Inlet Node"),
                    ("Air Outlet Node Name", "Your Coil Air Outlet Node"),
                    (
                        "Total Cooling Capacity Function of Temperature Curve Name",
                        self.capacity_temperature_curve_name,
                    ),
                    (
                        "Total Cooling Capacity Function of Flow Fraction Curve Name",
                        self.capacity_flow_curve_name,
                    ),
                    ("Energy Input Ratio Function of Temperature Curve Name", self.eir_temperature_curve_name),
                    ("Energy Input Ratio Function of Flow Fraction Curve Name", self.eir_flow_curve_name),
                    ("Part Load Fraction Correlation Curve Name", "PartLoadFractionCurve"),
                ]
            )
        return self.fill_eplus_object_format(self.coil_object_type, fields)

    def to_eplus_idf_object(self) -> str:
        return "\n".join(
            [
                self.current_eplus_version_object_idf(),
                self._coil_idf_object(),
                *self._curve_idf_objects(),
            ]
        )

    @staticmethod
    def _epjson_biquadratic(params):
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

    @staticmethod
    def _epjson_quadratic(params):
        return {
            "coefficient1_constant": params[0],
            "coefficient2_x": params[1],
            "coefficient3_x_x": params[2],
            "minimum_value_of_x": 0,
            "maximum_value_of_x": 2,
            "minimum_curve_output": 0,
            "maximum_curve_output": 10,
        }

    def to_eplus_epjson_object(self) -> str:
        coil = {
            "availability_schedule_name": "",
            "air_inlet_node_name": "Your Coil Air Inlet Node",
            "air_outlet_node_name": "Your Coil Air Outlet Node",
            "rated_air_flow_rate": self.rated_air_flow,
            "energy_input_ratio_function_of_temperature_curve_name": self.eir_temperature_curve_name,
            "energy_input_ratio_function_of_flow_fraction_curve_name": self.eir_flow_curve_name,
            "part_load_fraction_correlation_curve_name": "PartLoadFractionCurve",
        }
        if self.mode == "Heating":
            coil.update(
                {
                    "gross_rated_heating_capacity": self.rated_capacity,
                    "gross_rated_heating_cop": self.rated_capacity / self.rated_power,
                    "heating_capacity_function_of_temperature_curve_name": self.capacity_temperature_curve_name,
                    "heating_capacity_function_of_flow_fraction_curve_name": self.capacity_flow_curve_name,
                    "minimum_outdoor_dry_bulb_temperature_for_compressor_operation":
                        self.minimum_outdoor_temperature,
                    "defrost_strategy": "Resistive",
                }
            )
        else:
            coil.update(
                {
                    "gross_rated_total_cooling_capacity": self.rated_capacity,
                    "gross_rated_sensible_heat_ratio": self.rated_shr,
                    "gross_rated_cooling_cop": self.rated_capacity / self.rated_power,
                    "total_cooling_capacity_function_of_temperature_curve_name": self.capacity_temperature_curve_name,
                    "total_cooling_capacity_function_of_flow_fraction_curve_name": self.capacity_flow_curve_name,
                }
            )
        epjson = {
            **self.current_eplus_version_object_epjson(),
            self.coil_object_type: {f"Your {self.mode} Coil Name": coil},
            "Curve:Biquadratic": {
                self.capacity_temperature_curve_name: self._epjson_biquadratic(
                    self.capacity_temperature_params
                ),
                self.eir_temperature_curve_name: self._epjson_biquadratic(self.eir_temperature_params),
            },
            "Curve:Quadratic": {
                self.capacity_flow_curve_name: self._epjson_quadratic(self.capacity_flow_params),
                self.eir_flow_curve_name: self._epjson_quadratic(self.eir_flow_params),
                "PartLoadFractionCurve": self._epjson_quadratic([1.0, 0.0, 0.0]),
            },
        }
        return dumps(epjson, indent=2)

    def to_parameter_summary(self) -> str:
        output = f"""{self.name()}
**Begin Nomenclature**
CAP: {self.mode} Capacity
EIR: Energy Input Ratio
IAT: Indoor Entering Temperature
OAT: Outdoor Entering Dry-bulb Temperature
FF: Indoor Air Flow Fraction
**End Nomenclature**

**Begin Governing Equations**
CAP/CAP_R = CAP_T(IAT, OAT) * CAP_F(FF)
EIR/EIR_R = EIR_T(IAT, OAT) * EIR_F(FF)
**End Governing Equations**

**Begin Reporting Parameters**
Rated {self.capacity_label}: {self.rated_capacity}
Rated {self.power_label}: {self.rated_power}
Rated Air Flow Rate: {self.rated_air_flow}
Rated Indoor {self.indoor_temperature_label}: {self.rated_indoor_temperature}
Rated Outdoor Dry-bulb Temperature: {self.rated_outdoor_temperature}
"""
        if self.mode == "Heating":
            output += (
                "Minimum Outdoor Dry-bulb Temperature for Compressor Operation: "
                f"{self.minimum_outdoor_temperature}\n"
            )
        if self.mode == "Cooling":
            output += f"Rated Sensible Heat Ratio: {self.rated_shr}\n"
        for curve_name, params in (
            ("Capacity Temperature", self.capacity_temperature_params),
            ("Capacity Flow", self.capacity_flow_params),
            ("EIR Temperature", self.eir_temperature_params),
            ("EIR Flow", self.eir_flow_params),
        ):
            output += f"{curve_name} Curve Coefficients: "
            output += ", ".join(str(round(value, 6)) for value in params) + "\n"
        return output + "**End Reporting Parameters**"


class AirSourceHeatPumpHeatingCurveFit(AirSourceHeatPumpCurveFit):
    mode = "Heating"
    equipment_type = EquipType.ASHP_Heating_CurveFit
    coil_object_type = "Coil:Heating:DX:SingleSpeed"
    capacity_label = "Heating Capacity"
    power_label = "Heating Power"
    indoor_temperature_label = "Indoor Entering Dry-bulb Temp"
    indoor_temperature_default = 21.11
    outdoor_temperature_default = 8.33
    capacity_temperature_curve_name = "HeatingCapacityTemperatureCurve"
    capacity_flow_curve_name = "HeatingCapacityFlowCurve"
    eir_temperature_curve_name = "HeatingEIRTemperatureCurve"
    eir_flow_curve_name = "HeatingEIRFlowCurve"


class AirSourceHeatPumpCoolingCurveFit(AirSourceHeatPumpCurveFit):
    mode = "Cooling"
    equipment_type = EquipType.ASHP_Cooling_CurveFit
    coil_object_type = "Coil:Cooling:DX:SingleSpeed"
    capacity_label = "Total Cooling Capacity"
    power_label = "Cooling Power"
    indoor_temperature_label = "Indoor Entering Wet-bulb Temp"
    indoor_temperature_default = 19.44
    outdoor_temperature_default = 35.0
    capacity_temperature_curve_name = "CoolingCapacityTemperatureCurve"
    capacity_flow_curve_name = "CoolingCapacityFlowCurve"
    eir_temperature_curve_name = "CoolingEIRTemperatureCurve"
    eir_flow_curve_name = "CoolingEIRFlowCurve"
