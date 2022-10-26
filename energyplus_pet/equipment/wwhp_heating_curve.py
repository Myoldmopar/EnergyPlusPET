from json import dumps
from typing import Callable, List, Tuple

from energyplus_pet.equipment.common_curves import CommonCurves
from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.column_header import ColumnHeaderArray, ColumnHeader
from energyplus_pet.exceptions import EnergyPlusPetException
from energyplus_pet.units import UnitType


class WaterToWaterHeatPumpHeatingCurveFit(BaseEquipment):

    def __init__(self):
        # need some rated parameters that we get from the user for scaling, reporting, etc.
        self.rated_load_volume_flow_key = 'vl'
        self.rated_load_volume_flow = 0.0
        self.rated_source_volume_flow_key = 'vs'
        self.rated_source_volume_flow = 0.0
        self.rated_total_capacity_key = 'qc'
        self.rated_total_capacity = 0.0
        self.rated_heating_power_key = 'cp'
        self.rated_heating_power = 0.0
        # store some individual arrays for each of the dependent variable input columns
        self.catalog_total_capacity = []
        self.catalog_heating_power = []
        # these are matrices in the original code, here just store the final vector
        self.total_capacity_params = []
        self.heating_power_params = []
        # these represent a metric for the quality of the regression
        self.total_capacity_avg_err = 0.0
        self.heating_power_avg_err = 0.0
        # store the predicted outputs that are calculated from the generated parameters
        self.predicted_total_capacity = []
        self.predicted_heating_power = []
        self.percent_error_total_capacity = []
        self.percent_error_heating_power = []
        # store the headers as an instance variable, so we don't recreate on each call to headers()
        self._headers = ColumnHeaderArray(
            [
                ColumnHeader("Source-side Entering Temp", UnitType.Temperature),
                ColumnHeader("Source-side Volume Flow", UnitType.Flow),
                ColumnHeader("Load-side Entering Temp", UnitType.Temperature),
                ColumnHeader("Load-side Volume Flow", UnitType.Flow),
                ColumnHeader("Total Heating Capacity", UnitType.Power),
                ColumnHeader("Heating Power", UnitType.Power),
            ]
        )

    def this_type(self) -> EquipType:
        return EquipType.WWHP_Heating_CurveFit

    def name(self) -> str:
        return "Water to Water Heat Pump, Heating Coil, Curve Fit Formulation"

    def short_name(self) -> str:
        return "WWHP-Heating-CurveFit"

    def get_required_constant_parameters(self) -> List[BaseEquipment.RequiredConstantParameter]:
        return [
            # need some rated parameters that we get from the user for scaling, reporting, etc.
            BaseEquipment.RequiredConstantParameter(
                self.rated_load_volume_flow_key,
                "Rated Load-side Flow Rate",
                "This is a nominal flow rate value for the load-side of the coil",
                UnitType.Flow,
                0.0006887,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_source_volume_flow_key,
                "Rated Source-side Flow Rate",
                "This is a nominal flow rate value for the source-side of the coil",
                UnitType.Flow,
                0.0001892,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_total_capacity_key,
                "Rated Total Heating Capacity",
                "This is a nominal value of the total heating capacity of the coil",
                UnitType.Power,
                3.513,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_heating_power_key,
                "Rated Heating Power",
                "This is a nominal value of the heating power for this coil",
                UnitType.Power,
                0.900,
            )
        ]

    def set_required_constant_parameter(self, parameter_id: str, new_value: float) -> None:
        if parameter_id == self.rated_load_volume_flow_key:
            self.rated_load_volume_flow = new_value
        elif parameter_id == self.rated_source_volume_flow_key:
            self.rated_source_volume_flow = new_value
        elif parameter_id == self.rated_total_capacity_key:
            self.rated_total_capacity = new_value
        elif parameter_id == self.rated_heating_power_key:
            self.rated_heating_power = new_value
        else:
            raise EnergyPlusPetException("Bad parameter ID in set_required_constant_parameter")

    def headers(self) -> ColumnHeaderArray:
        return self._headers

    def to_eplus_idf_object(self) -> str:
        object_name = "HeatPump:WaterToWater:EquationFit:Heating"
        fields = [
            ("Name", 'Your Heating Coil Name'),
            ("Source Side Inlet Node Name", 'Your Coil Source Side Inlet Node'),
            ("Source Side Outlet Node Name", 'Your Coil Source Side Outlet Node'),
            ("Load Side Inlet Node Name", 'Your Coil Load Side Inlet Node'),
            ("Load Side Outlet Node Name", 'Your Coil Load Side Outlet Node'),
            ("Reference Load Side Flow Rate", self.rated_load_volume_flow),
            ("Reference Source Side Flow Rate", self.rated_source_volume_flow),
            ("Reference Heating Capacity", self.rated_total_capacity),
            ("Reference Heating Power Consumption", self.rated_heating_power),
            ("Heating Capacity Curve Name", 'TotalCapacityCurve'),
            ("Heating Compressor Power Consumption Curve Name", 'HeatingPowerCurve'),
            ("Reference Coefficient of Performance", round(self.rated_total_capacity / self.rated_heating_power, 8)),
            ("Sizing Factor", ''),
            ("Companion Cooling Heat Pump Name", 'Your Cooling Coil Name')
        ]
        coil_object_string = self.fill_eplus_object_format(object_name, fields)

        reused_limits = [
            ("Minimum Value of w", -100), ("Maximum Value of w", 100),
            ("Minimum Value of x", -100), ("Maximum Value of x", 100),
            ("Minimum Value of y", -100), ("Maximum Value of y", 100),
            ("Minimum Value of z", -100), ("Maximum Value of z", 100),
        ]

        object_name = "Curve:QuadLinear"
        fields = [
            ("Name", "TotalCapacityCurve"),
            *[(f"Coefficient{i}", self.total_capacity_params[i]) for i in range(5)],
            *reused_limits
        ]
        total_curve_output = self.fill_eplus_object_format(object_name, fields)

        object_name = "Curve:QuadLinear"
        fields = [
            ("Name", "HeatingPowerCurve"),
            *[(f"Coefficient{i}", self.heating_power_params[i]) for i in range(5)],
            *reused_limits
        ]
        power_curve_output = self.fill_eplus_object_format(object_name, fields)

        return '\n'.join([
            BaseEquipment.current_eplus_version_object_idf(),
            coil_object_string,
            total_curve_output, power_curve_output
        ])

    def to_parameter_summary(self) -> str:
        output = f"""{self.name()}
**Begin Nomenclature**
TC: Total Heating Capacity
CP: Heating Power Consumption
TLI: Entering Load-side Temperature
TSI: Entering Source-side Temperature
VLI: Entering Load-side Flow Rate
VSI: Entering Source-side Flow Rate
Subscript _R: Rated Value
Subscript _#: Coefficient #
**End Nomenclature**

**Begin Governing Equations**
(TC/TC_R) = TC_1 + TC_2*(TLI/TLI_R) + TC_3*(TSI/TSI_R) + TC_4*(VLI/VLI_R) + TC_5*(VSI/VSI_R)
(CP/CP_R) = CP_1 + CP_2*(TLI/TLI_R) + CP_3*(TSI/TSI_R) + CP_4*(VLI/VLI_R) + CP_5*(VSI/VSI_R)
**End Governing Equations**

**Begin Reporting Parameters**
Rated Load-side Total Heating Capacity: {self.rated_total_capacity}
Rated Heating Power Consumption: {self.rated_heating_power}
Rated Load-side Volumetric Flow Rate: {self.rated_load_volume_flow}
Rated Source-side Volumetric Flow Rate: {self.rated_source_volume_flow}
"""
        for i, c in enumerate(self.total_capacity_params):
            output += f"Heating Total Capacity Coefficient TC_{i + 1}: {round(c, 4)}\n"
        for i, c in enumerate(self.heating_power_params):
            output += f"Heating Power Consumption Coefficient CP_{i + 1}: {round(c, 4)}\n"
        output += "**End Reporting Parameters**"
        return output

    def to_eplus_epjson_object(self) -> str:
        coil_object = {'Your Heating Coil Name': {
            'source_side_inlet_node_name': 'Your Coil Source Side Inlet Node',
            'source_side_outlet_node_name': 'Your Coil Source Side Outlet Node',
            'load_side_inlet_node_name': 'Your Coil Load Side Inlet Node',
            'load_side_outlet_node_name': 'Your Coil Load Side Outlet Node',
            'reference_load_side_flow_rate': self.rated_load_volume_flow,
            'reference_source_side_flow_rate': self.rated_source_volume_flow,
            'reference_heating_capacity': self.rated_total_capacity,
            'reference_heating_power_consumption': self.rated_heating_power,
            'heating_capacity_curve_name': 'TotalCapacityCurve',
            'heating_compressor_power_curve_name': 'HeatingPowerCurve',
            'reference_coefficient_of_performance': self.rated_total_capacity / self.rated_heating_power,
            'sizing_factor': '',
            'companion_heating_heat_pump_name': 'Your Heating Coil Name',
        }}
        reused_limits = {
            "minimum_value_of_w": -100, "maximum_value_of_w": 100,
            "minimum_value_of_x": -100, "maximum_value_of_x": 100,
            "minimum_value_of_y": -100, "maximum_value_of_y": 100,
            "minimum_value_of_z": -100, "maximum_value_of_z": 100,
        }
        curves = {'TotalCapacityCurve': {
            "coefficient1_constant": self.total_capacity_params[0],
            "coefficient2_w": self.total_capacity_params[1],
            "coefficient3_x": self.total_capacity_params[2],
            "coefficient4_y": self.total_capacity_params[3],
            "coefficient5_z": self.total_capacity_params[4],
            **reused_limits
        }, 'HeatingPowerCurve': {
            "coefficient1_constant": self.heating_power_params[0],
            "coefficient2_w": self.heating_power_params[1],
            "coefficient3_x": self.heating_power_params[2],
            "coefficient4_y": self.heating_power_params[3],
            "coefficient5_z": self.heating_power_params[4],
            **reused_limits
        }}

        epjson_object = {
            **BaseEquipment.current_eplus_version_object_epjson(),
            'HeatPump:WaterToWater:EquationFit:Cooling': coil_object,
            'Curve:QuadLinear': curves
        }
        return dumps(epjson_object, indent=2)

    def get_number_of_progress_steps(self) -> int:
        return 3  # read data, tc curve fit, power curve fit

    def minimum_data_points_for_generation(self) -> int:
        return 5

    def generate_parameters(
            self, data_manager: CatalogDataManager, cb_progress_increment: Callable, cb_progress_done: Callable
    ):
        # step 1, read the data into arrays (will be used for both scaling calculations and plotting later)
        # these should already be set to zero, but not sure if the main form will reinitialize the equip-instance or not
        self.catalog_total_capacity = [x[4] for x in data_manager.final_data_matrix]
        self.catalog_heating_power = [x[5] for x in data_manager.final_data_matrix]
        scaled_source_side_inlet_temp = []
        scaled_source_side_flow_rate = []
        scaled_load_side_inlet_temp = []
        scaled_load_side_flow_rate = []
        scaled_heating_capacity = []
        scaled_heating_power = []
        for data_row in data_manager.final_data_matrix:
            scaled_source_side_inlet_temp.append((data_row[0] + 273.15) / (10.0 + 273.15))  # T_ref defined by HP model
            scaled_source_side_flow_rate.append(data_row[1] / self.rated_source_volume_flow)
            scaled_load_side_inlet_temp.append((data_row[2] + 273.15) / (10.0 + 273.15))
            scaled_load_side_flow_rate.append(data_row[3] / self.rated_load_volume_flow)
            scaled_heating_capacity.append(data_row[4] / self.rated_total_capacity)
            scaled_heating_power.append(data_row[5] / self.rated_heating_power)
        cb_progress_increment()

        independent_var_arrays = (
            scaled_load_side_inlet_temp,
            scaled_source_side_inlet_temp,
            scaled_load_side_flow_rate,
            scaled_source_side_flow_rate
        )

        self.total_capacity_params, self.total_capacity_avg_err = self.do_one_curve_fit(
            CommonCurves.heat_pump_5_coefficient_curve,
            independent_var_arrays,
            scaled_heating_capacity
        )
        cb_progress_increment()

        self.heating_power_params, self.heating_power_avg_err = self.do_one_curve_fit(
            CommonCurves.heat_pump_5_coefficient_curve,
            independent_var_arrays,
            scaled_heating_power
        )
        cb_progress_increment()

        # now just recalculate the values at each catalog data point
        self.predicted_total_capacity, self.percent_error_total_capacity = self.eval_curve_at_points(
            lambda *x: CommonCurves.heat_pump_5_coefficient_curve_raw_value(*x, self.rated_total_capacity),
            independent_var_arrays,
            self.total_capacity_params,
            self.catalog_total_capacity
        )
        self.predicted_heating_power, self.percent_error_heating_power = self.eval_curve_at_points(
            lambda *x: CommonCurves.heat_pump_5_coefficient_curve_raw_value(*x, self.rated_heating_power),
            independent_var_arrays,
            self.heating_power_params,
            self.catalog_heating_power
        )
        cb_progress_done(True)

    def get_absolute_plot_data(self) -> Tuple:
        return (
            ('Total Heat Transfer Model', 'line', 'red', self.predicted_total_capacity),
            ('Total Heat Transfer Catalog', 'point', 'red', self.catalog_total_capacity),
            ('Heating Power Model', 'line', 'green', self.predicted_heating_power),
            ('Heating Power Catalog', 'point', 'green', self.catalog_heating_power),
        )

    def get_error_plot_data(self) -> Tuple:
        return (
            ('Total Heat Transfer % Error', 'line', 'red', self.percent_error_total_capacity),
            ('Heating Power % Error', 'line', 'green', self.percent_error_heating_power),
        )

    def get_extra_regression_metrics(self) -> Tuple:
        return (
            (
                "Total Heat Transfer Average curve-fit error (1 standard deviation)",
                self.total_capacity_avg_err
            ),
            (
                "Heating Power Average curve-fit error (1 standard deviation)",
                self.heating_power_avg_err
            )
        )
