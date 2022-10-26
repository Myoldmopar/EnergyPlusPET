from json import dumps
from typing import Callable, List, Tuple

from energyplus_pet.equipment.common_curves import CommonCurves
from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.column_header import ColumnHeaderArray, ColumnHeader
from energyplus_pet.exceptions import EnergyPlusPetException
from energyplus_pet.units import UnitType


class WaterToAirHeatPumpCoolingCurveFit(BaseEquipment):

    def __init__(self):
        # need some rated parameters that we get from the user for scaling, reporting, etc.
        self.rated_air_volume_flow_key = 'vl'
        self.rated_air_volume_flow = 0.0
        self.rated_water_volume_flow_key = 'vs'
        self.rated_water_volume_flow = 0.0
        self.rated_total_capacity_key = 'qc'
        self.rated_total_capacity = 0.0
        self.rated_sensible_capacity_key = 'qs'
        self.rated_sensible_capacity = 0.0
        self.rated_cooling_power_key = 'cp'
        self.rated_cooling_power = 0.0
        # store some individual arrays for each of the dependent variable input columns
        self.catalog_total_capacity = []
        self.catalog_sensible_capacity = []
        self.catalog_cooling_power = []
        # these are matrices in the original code, here just store the final vector
        self.total_capacity_params = []
        self.sensible_capacity_params = []
        self.cooling_power_params = []
        # these represent a metric for the quality of the regression
        self.total_capacity_avg_err = 0.0
        self.sensible_capacity_avg_err = 0.0
        self.cooling_power_avg_err = 0.0
        # store the predicted outputs that are calculated from the generated parameters
        self.predicted_total_capacity = []
        self.predicted_sensible_capacity = []
        self.predicted_cooling_power = []
        self.percent_error_total_capacity = []
        self.percent_error_sensible_capacity = []
        self.percent_error_cooling_power = []
        # store the headers as an instance variable, so we don't recreate on each call to headers()
        self._headers = ColumnHeaderArray(
            [
                ColumnHeader("Water-side Entering Temp", UnitType.Temperature),
                ColumnHeader("Water-side Volume Flow", UnitType.Flow),
                ColumnHeader("Air-side Entering Dry-bulb Temp", UnitType.Temperature, db=True),
                ColumnHeader("Air-side Entering Wet-bulb Temp", UnitType.Temperature, wb=True),
                ColumnHeader("Air-side Volume Flow", UnitType.Flow),
                ColumnHeader("Total Cooling Capacity", UnitType.Power),
                ColumnHeader("Sensible Cooling Capacity", UnitType.Power),
                ColumnHeader("Cooling Power", UnitType.Power),
            ]
        )

    def this_type(self) -> EquipType:
        return EquipType.WAHP_Cooling_CurveFit

    def name(self) -> str:
        return "Water to Air Heat Pump, Cooling Coil, Curve Fit Formulation"

    def short_name(self) -> str:
        return "WAHP-Cooling-CurveFit"

    def get_required_constant_parameters(self) -> List[BaseEquipment.RequiredConstantParameter]:
        return [
            # need some rated parameters that we get from the user for scaling, reporting, etc.
            BaseEquipment.RequiredConstantParameter(
                self.rated_air_volume_flow_key,
                "Rated Air Flow Rate",
                "This is a nominal flow rate value for the air-side of the coil",
                UnitType.Flow,
                0.0006887,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_water_volume_flow_key,
                "Rated Water Flow Rate",
                "This is a nominal flow rate value for the water-side of the coil",
                UnitType.Flow,
                0.0001892,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_total_capacity_key,
                "Rated Total Cooling Capacity",
                "This is a nominal value of the total cooling capacity of the coil",
                UnitType.Power,
                3.513,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_sensible_capacity_key,
                "Rated Sensible Cooling Capacity",
                "This is a nominal value of the sensible cooling capacity of the coil",
                UnitType.Power,
                3.1,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_cooling_power_key,
                "Rated Cooling Power",
                "This is a nominal value of the cooling power for this coil",
                UnitType.Power,
                0.900,
            )
        ]

    def set_required_constant_parameter(self, parameter_id: str, new_value: float) -> None:
        if parameter_id == self.rated_air_volume_flow_key:
            self.rated_air_volume_flow = new_value
        elif parameter_id == self.rated_water_volume_flow_key:
            self.rated_water_volume_flow = new_value
        elif parameter_id == self.rated_total_capacity_key:
            self.rated_total_capacity = new_value
        elif parameter_id == self.rated_sensible_capacity_key:
            self.rated_sensible_capacity = new_value
        elif parameter_id == self.rated_cooling_power_key:
            self.rated_cooling_power = new_value
        else:
            raise EnergyPlusPetException("Bad parameter ID in set_required_constant_parameter")

    def headers(self) -> ColumnHeaderArray:
        return self._headers

    def to_eplus_idf_object(self) -> str:
        object_name = "Coil:Cooling:WaterToAirHeatPump:EquationFit"
        fields = [
            ("Name", 'Your Coil Name'),
            ("Water Inlet Node Name", 'Your Coil Source Side Inlet Node'),
            ("Water Outlet Node Name", 'Your Coil Source Side Outlet Node'),
            ("Air Inlet Node Name", 'Your Coil Load Side Inlet Node'),
            ("Air Outlet Node Name", 'Your Coil Load Side Outlet Node'),
            ("Rated Air Flow Rate", self.rated_air_volume_flow),
            ("Rated Water Flow Rate", self.rated_water_volume_flow),
            ("Rated Total Cooling Capacity", self.rated_total_capacity),
            ("Rated Sensible Cooling Capacity", self.rated_sensible_capacity),
            ("Rated Cooling COP", round(self.rated_total_capacity / self.rated_cooling_power, 4)),
            ("Rated Entering Water Temperature", ''),
            ("Rated Entering Air Dry-Bulb Temp", ''),
            ("Rated Entering Air Wet-Bulb Temp", ''),
            ("Total Cooling Capacity Curve Name", 'TotalCapacityCurve'),
            ("Sensible Cooling Capacity Curve Name", 'SensibleCapacityCurve'),
            ("Cooling Power Consumption Curve Name", 'CoolingPowerCurve'),
            ("Nominal Time for Condensate Removal to Begin", ''),
            ("Ratio of Initial Moisture Evaporation Rate and Steady State Latent Capacity", '')
        ]
        coil_object_string = self.fill_eplus_object_format(object_name, fields)

        quad_reused_limits = [
            ("Minimum Value of w", -100), ("Maximum Value of w", 100),
            ("Minimum Value of x", -100), ("Maximum Value of x", 100),
            ("Minimum Value of y", -100), ("Maximum Value of y", 100),
            ("Minimum Value of z", -100), ("Maximum Value of z", 100),
        ]
        quint_reused_limits = [
            ("Minimum Value of v", -100), ("Maximum Value of v", 100),
            ("Minimum Value of w", -100), ("Maximum Value of w", 100),
            ("Minimum Value of x", -100), ("Maximum Value of x", 100),
            ("Minimum Value of y", -100), ("Maximum Value of y", 100),
            ("Minimum Value of z", -100), ("Maximum Value of z", 100),
        ]

        object_name = "Curve:QuadLinear"
        fields = [
            ("Name", "TotalCapacityCurve"),
            *[(f"Coefficient{i}", self.total_capacity_params[i]) for i in range(5)],
            *quad_reused_limits
        ]
        total_curve_output = self.fill_eplus_object_format(object_name, fields)

        object_name = "Curve:QuintLinear"
        fields = [
            ("Name", "SensibleCapacityCurve"),
            *[(f"Coefficient{i}", self.sensible_capacity_params[i]) for i in range(6)],
            *quint_reused_limits
        ]
        sensible_curve_output = self.fill_eplus_object_format(object_name, fields)

        object_name = "Curve:QuadLinear"
        fields = [
            ("Name", "CoolingPowerCurve"),
            *[(f"Coefficient{i}", self.cooling_power_params[i]) for i in range(5)],
            *quad_reused_limits
        ]
        power_curve_output = self.fill_eplus_object_format(object_name, fields)

        return '\n'.join([
            BaseEquipment.current_eplus_version_object_idf(),
            coil_object_string,
            total_curve_output, sensible_curve_output, power_curve_output
        ])

    def to_parameter_summary(self) -> str:
        output = f"""{self.name()}
**Begin Nomenclature**
TC: Total Cooling Capacity
SC: Sensible Capacity
CP: Cooling Power Consumption
Tdb: Entering Dry-bulb Load-side Temperature
Twb: Entering Wet-bulb Load-side Temperature
TSI: Entering Source-side Temperature
VLI: Entering Load-side Flow Rate
VSI: Entering Source-side Flow Rate
Subscript _R: Rated Value
Subscript _#: Coefficient #
**End Nomenclature**

**Begin Governing Equations**
(TC/TC_R) = TC_1 + TC_2*(Twb/Twb_R) + TC_3*(TSI/TSI_R) + TC_4*(VLI/VLI_R) + TC_5*(VSI/VSI_R)
(SC/SC_R) = SC_1 + SC_2*(Tdb/Tdb_R) + SC_3*(Twb/Twb_R) + SC_4*(TSI/TSI_R) + SC_5*(VLI/VLI_R) + SC_6*(VSI/VSI_R)
(CP/CP_R) = CP_1 + CP_2*(Twb/Twb_R) + CP_3*(TSI/TSI_R) + CP_4*(VLI/VLI_R) + CP_5*(VSI/VSI_R)
**End Governing Equations**

**Begin Reporting Parameters**
Rated Load-side Total Cooling Capacity: {self.rated_total_capacity}
Rated Load-side Sensible Cooling Capacity: {self.rated_sensible_capacity}
Rated Cooling Power Consumption: {self.rated_cooling_power}
Rated Load-side Volumetric Flow Rate: {self.rated_air_volume_flow}
Rated Source-side Volumetric Flow Rate: {self.rated_water_volume_flow}
"""
        for i, c in enumerate(self.total_capacity_params):
            output += f"Cooling Total Capacity Coefficient TC_{i + 1}: {round(c, 4)}\n"
        for i, c in enumerate(self.sensible_capacity_params):
            output += f"Cooling Sensible Capacity Coefficient SC_{i + 1}: {round(c, 4)}\n"
        for i, c in enumerate(self.cooling_power_params):
            output += f"Cooling Power Consumption Coefficient CP_{i + 1}: {round(c, 4)}\n"
        output += "**End Reporting Parameters**"
        return output

    def to_eplus_epjson_object(self) -> str:
        coil_object = {'Your Coil Name': {
            'water_inlet_node_name': 'Your Coil Source Side Inlet Node',
            'water_outlet_node_name': 'Your Coil Source Side Outlet Node',
            'air_inlet_node_name': 'Your Coil Load Side Inlet Node',
            'air_outlet_node_name': 'Your Coil Load Side Outlet Node',
            'gross_rated_total_cooling_capacity': self.rated_total_capacity,
            'gross_rated_sensible_cooling_capacity': self.rated_sensible_capacity,
            'gross_rated_cooling_cop': self.rated_total_capacity / self.rated_cooling_power,
            'rated_air_flow_rate': self.rated_air_volume_flow,
            'rated_water_flow_rate': self.rated_water_volume_flow,
            'rated_entering_water_temperature': '',
            'rated_entering_air_dry_bulb_temperature': '',
            'rated_entering_air_wet_bulb_temperature': '',
            'total_cooling_capacity_curve_name': 'TotalCapacityCurve',
            'sensible_cooling_capacity_curve_name': 'SensibleCapacityCurve',
            'cooling_power_consumption_curve_name': 'CoolingPowerCurve',
            'nominal_time_for_condensate_removal_to_begin': '',
            'ratio_of_initial_moisture_evaporation_rate_and_steady_state_latent_capacity': ''
        }}
        reused_limits_four = {
            "minimum_value_of_w": -100, "maximum_value_of_w": 100,
            "minimum_value_of_x": -100, "maximum_value_of_x": 100,
            "minimum_value_of_y": -100, "maximum_value_of_y": 100,
            "minimum_value_of_z": -100, "maximum_value_of_z": 100,
        }
        reused_limits_five = {
            "minimum_value_of_v": -100, "maximum_value_of_v": 100,
            "minimum_value_of_w": -100, "maximum_value_of_w": 100,
            "minimum_value_of_x": -100, "maximum_value_of_x": 100,
            "minimum_value_of_y": -100, "maximum_value_of_y": 100,
            "minimum_value_of_z": -100, "maximum_value_of_z": 100,
        }
        quad_curves = {'TotalCapacityCurve': {
            "coefficient1_constant": self.total_capacity_params[0],
            "coefficient2_w": self.total_capacity_params[1],
            "coefficient3_x": self.total_capacity_params[2],
            "coefficient4_y": self.total_capacity_params[3],
            "coefficient5_z": self.total_capacity_params[4],
            **reused_limits_four
        }, 'CoolingPowerCurve': {
            "coefficient1_constant": self.cooling_power_params[0],
            "coefficient2_w": self.cooling_power_params[1],
            "coefficient3_x": self.cooling_power_params[2],
            "coefficient4_y": self.cooling_power_params[3],
            "coefficient5_z": self.cooling_power_params[4],
            **reused_limits_four
        }}
        quint_curves = {'SensibleCapacityCurve': {
            "coefficient1_constant": self.sensible_capacity_params[0],
            "coefficient2_v": self.sensible_capacity_params[1],
            "coefficient3_w": self.sensible_capacity_params[2],
            "coefficient4_x": self.sensible_capacity_params[3],
            "coefficient5_y": self.sensible_capacity_params[4],
            "coefficient5_z": self.sensible_capacity_params[5],
            **reused_limits_five
        }}

        epjson_object = {
            **BaseEquipment.current_eplus_version_object_epjson(),
            'Coil:Cooling:WaterToAirHeatPump:EquationFit': coil_object,
            'Curve:QuadLinear': quad_curves,
            'Curve:QuintLinear': quint_curves
        }
        return dumps(epjson_object, indent=2)

    def get_number_of_progress_steps(self) -> int:
        return 4  # read data, tc curve fit, sc curve fit, power curve fit

    def minimum_data_points_for_generation(self) -> int:
        return 6

    def generate_parameters(
            self, data_manager: CatalogDataManager, cb_progress_increment: Callable, cb_progress_done: Callable
    ):
        # step 1, read the data into arrays (will be used for both scaling calculations and plotting later)
        # these should already be set to zero, but not sure if the main form will reinitialize the equip-instance or not
        self.catalog_total_capacity = [x[5] for x in data_manager.final_data_matrix]
        self.catalog_sensible_capacity = [x[6] for x in data_manager.final_data_matrix]
        self.catalog_cooling_power = [x[7] for x in data_manager.final_data_matrix]
        scaled_water_inlet_temp = []
        scaled_water_flow_rate = []
        scaled_air_inlet_db_temp = []
        scaled_air_inlet_wb_temp = []
        scaled_air_flow_rate = []
        scaled_cooling_capacity = []
        scaled_sensible_capacity = []
        scaled_cooling_power = []
        for data_row in data_manager.final_data_matrix:
            scaled_water_inlet_temp.append((data_row[0] + 273.15) / (10.0 + 273.15))  # T_ref defined by HP model
            scaled_water_flow_rate.append(data_row[1] / self.rated_water_volume_flow)
            scaled_air_inlet_db_temp.append((data_row[2] + 273.15) / (10.0 + 273.15))
            scaled_air_inlet_wb_temp.append((data_row[3] + 273.15) / (10.0 + 273.15))
            scaled_air_flow_rate.append(data_row[4] / self.rated_air_volume_flow)
            scaled_cooling_capacity.append(data_row[5] / self.rated_total_capacity)
            scaled_sensible_capacity.append(data_row[6] / self.rated_sensible_capacity)
            scaled_cooling_power.append(data_row[7] / self.rated_cooling_power)
        cb_progress_increment()

        four_independent_var_arrays = (
            scaled_air_inlet_wb_temp,
            scaled_water_inlet_temp,
            scaled_air_flow_rate,
            scaled_water_flow_rate
        )
        five_independent_var_arrays = (
            scaled_air_inlet_db_temp,
            scaled_air_inlet_wb_temp,
            scaled_water_inlet_temp,
            scaled_air_flow_rate,
            scaled_water_flow_rate
        )

        self.total_capacity_params, self.total_capacity_avg_err = self.do_one_curve_fit(
            CommonCurves.heat_pump_5_coefficient_curve,
            four_independent_var_arrays,
            scaled_cooling_capacity
        )
        cb_progress_increment()

        self.sensible_capacity_params, self.sensible_capacity_avg_err = self.do_one_curve_fit(
            CommonCurves.heat_pump_6_coefficient_curve,
            five_independent_var_arrays,
            scaled_sensible_capacity
        )
        cb_progress_increment()

        self.cooling_power_params, self.cooling_power_avg_err = self.do_one_curve_fit(
            CommonCurves.heat_pump_5_coefficient_curve,
            four_independent_var_arrays,
            scaled_cooling_power
        )
        cb_progress_increment()

        # now just recalculate the values at each catalog data point
        self.predicted_total_capacity, self.percent_error_total_capacity = self.eval_curve_at_points(
            lambda *x: CommonCurves.heat_pump_5_coefficient_curve_raw_value(*x, self.rated_total_capacity),
            four_independent_var_arrays,
            self.total_capacity_params,
            self.catalog_total_capacity
        )
        self.predicted_sensible_capacity, self.percent_error_sensible_capacity = self.eval_curve_at_points(
            lambda *x: CommonCurves.heat_pump_6_coefficient_curve_raw_value(*x, self.rated_sensible_capacity),
            five_independent_var_arrays,
            self.sensible_capacity_params,
            self.catalog_sensible_capacity
        )
        self.predicted_cooling_power, self.percent_error_cooling_power = self.eval_curve_at_points(
            lambda *x: CommonCurves.heat_pump_5_coefficient_curve_raw_value(*x, self.rated_cooling_power),
            four_independent_var_arrays,
            self.cooling_power_params,
            self.catalog_cooling_power
        )
        cb_progress_done(True)

    def get_absolute_plot_data(self) -> Tuple:
        return (
            ('Total Heat Transfer Model', 'line', 'red', self.predicted_total_capacity),
            ('Total Heat Transfer Catalog', 'point', 'red', self.catalog_total_capacity),
            ('Sensible Heat Transfer Model', 'line', 'blue', self.predicted_sensible_capacity),
            ('Sensible Heat Transfer Catalog', 'point', 'blue', self.catalog_sensible_capacity),
            ('Cooling Power Model', 'line', 'green', self.predicted_cooling_power),
            ('Cooling Power Catalog', 'point', 'green', self.catalog_cooling_power),
        )

    def get_error_plot_data(self) -> Tuple:
        return (
            ('Total Heat Transfer % Error', 'line', 'red', self.percent_error_total_capacity),
            ('Sensible Heat Transfer % Error', 'line', 'blue', self.percent_error_sensible_capacity),
            ('Cooling Power % Error', 'line', 'green', self.percent_error_cooling_power),
        )

    def get_extra_regression_metrics(self) -> Tuple:
        return (
            (
                "Total Heat Transfer Average curve-fit error (1 standard deviation)",
                self.total_capacity_avg_err
            ),
            (
                "Sensible Heat Transfer Average curve-fit error (1 standard deviation)",
                self.sensible_capacity_avg_err
            ),
            (
                "Cooling Power Average curve-fit error (1 standard deviation)",
                self.cooling_power_avg_err
            )
        )
