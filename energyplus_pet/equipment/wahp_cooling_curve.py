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
        self.rated_load_volume_flow_rate_key = 'vl'
        self.rated_load_volume_flow_rate = 0.0
        self.rated_source_volume_flow_rate_key = 'vs'
        self.rated_source_volume_flow_rate = 0.0
        self.rated_total_capacity_key = 'qc'
        self.rated_total_capacity = 0.0
        self.rated_sensible_capacity_key = 'qs'
        self.rated_sensible_capacity = 0.0
        self.rated_compressor_power_key = 'cp'
        self.rated_compressor_power = 0.0
        # store some individual arrays for each of the input columns
        self.catalog_source_side_inlet_temp = []
        self.catalog_source_side_volume_flow_rate = []
        self.catalog_load_side_inlet_temp = []
        self.catalog_load_side_volume_flow_rate = []
        self.catalog_load_side_cooling_capacity = []
        self.catalog_load_side_sensible_capacity = []
        self.catalog_compressor_power = []
        # these represent a metric for the quality of the regression
        self.cooling_capacity_average_err_one_sigma = 0.0
        self.sensible_capacity_average_err_one_sigma = 0.0
        self.compressor_power_average_err_one_sigma = 0.0
        # these are matrices in the original code, here just store the final vector
        self.total_capacity_params = [0.0] * 5
        self.sensible_capacity_params = [0.0] * 5
        self.compressor_power_params = [0.0] * 5
        # store the predicted outputs that are calculated from the generated parameters
        self.predicted_load_side_cooling_capacity = []
        self.predicted_load_side_sensible_capacity = []
        self.predicted_compressor_power = []
        self.predicted_source_side_heat_absorption = []
        self.error_load_side_cooling_capacity = []
        self.error_load_side_sensible_capacity = []
        self.error_compressor_power = []
        self.percent_error_source_side_heat_absorption = []

    def this_type(self) -> EquipType:
        return EquipType.WAHP_Cooling_CurveFit

    def name(self) -> str:
        return "Water to Air Heat Pump, Cooling Mode, Curve Fit Formulation"

    def short_name(self) -> str:
        return "WAHP-Cooling-CurveFit"

    def get_required_constant_parameters(self) -> List[BaseEquipment.RequiredConstantParameter]:
        return [
            # need some rated parameters that we get from the user for scaling, reporting, etc.
            BaseEquipment.RequiredConstantParameter(
                self.rated_load_volume_flow_rate_key,
                "Rated Load Side Flow Rate",
                "This is a nominal flow rate value for the load-side of the heat pump",
                UnitType.Flow,
                0.0006887,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_source_volume_flow_rate_key,
                "Rated Source Side Flow Rate",
                "This is a nominal flow rate value for the source-side of the heat pump",
                UnitType.Flow,
                0.0001892,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_total_capacity_key,
                "Rated Total Cooling Capacity",
                "This is a nominal value of the load-side cooling capacity of the heat pump",
                UnitType.Power,
                3.513,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_sensible_capacity_key,
                "Rated Sensible Cooling Capacity",
                "This is a nominal value of the load-side sensible capacity of the heat pump",
                UnitType.Power,
                3.1,
            ),
            BaseEquipment.RequiredConstantParameter(
                self.rated_compressor_power_key,
                "Rated Compressor Power Use",
                "This is a nominal value of the compressor power for this heat pump",
                UnitType.Power,
                0.900,
            )
        ]

    def set_required_constant_parameter(self, parameter_id: str, new_value: float) -> None:
        if parameter_id == self.rated_load_volume_flow_rate_key:
            self.rated_load_volume_flow_rate = new_value
        elif parameter_id == self.rated_source_volume_flow_rate_key:
            self.rated_source_volume_flow_rate = new_value
        elif parameter_id == self.rated_total_capacity_key:
            self.rated_total_capacity = new_value
        elif parameter_id == self.rated_sensible_capacity_key:
            self.rated_sensible_capacity = new_value
        elif parameter_id == self.rated_compressor_power_key:
            self.rated_compressor_power = new_value
        else:
            raise EnergyPlusPetException("Bad parameter ID in set_required_constant_parameter")

    def headers(self) -> ColumnHeaderArray:
        return ColumnHeaderArray(
            [
                ColumnHeader("Source Side Entering Temp", UnitType.Temperature),
                ColumnHeader("Source Side Flow Rate", UnitType.Flow),
                ColumnHeader("Load Side Entering Temp", UnitType.Temperature),
                ColumnHeader("Load Side Flow Rate", UnitType.Flow),
                ColumnHeader("Load Side Total Capacity", UnitType.Power),
                ColumnHeader("Load Side Sensible Capacity", UnitType.Power),
                ColumnHeader("Compressor Power Input", UnitType.Power),
            ]
        )

    def to_eplus_idf_object(self) -> str:
        fields = [
            'Your Coil Name',
            'Your Coil Source Side Inlet Node',
            'Your Coil Source Side Outlet Node',
            'Your Coil Load Side Inlet Node',
            'Your Coil Load Side Outlet Node',
            self.rated_load_volume_flow_rate,
            self.rated_source_volume_flow_rate,
            self.rated_total_capacity,
            self.rated_sensible_capacity,
            round(self.rated_total_capacity / self.rated_compressor_power, 4),
        ]
        fields.extend(self.total_capacity_params)
        fields.extend(self.sensible_capacity_params)
        fields.extend(self.compressor_power_params)
        fields.append('Your Heat Pump Cycle Time')
        form = """HeatPump:WaterToAir:EquationFit:Cooling,
{0},{1}!-Name
{2},{3}!-Source Side Inlet Node Name
{4},{5}!-Source Side Outlet Node Name
{6},{7}!-Load Side Inlet Node Name
{8},{9}!-Load Side Outlet Node Name
{10},{11}!-Rated Load Side Flow Rate
{12},{13}!-Rated Source Side Flow Rate
{14},{15}!-Rated Total Cooling Capacity
{14},{15}!-Rated Sensible Cooling Capacity
{16},{17}!-Rated Cooling COP
{18},{19}!-Total Cooling Capacity Coefficient 1
{20},{21}!-Total Cooling Capacity Coefficient 2
{22},{23}!-Total Cooling Capacity Coefficient 3
{24},{25}!-Total Cooling Capacity Coefficient 4
{26},{27}!-Total Cooling Capacity Coefficient 5
{18},{19}!-Sensible Cooling Capacity Coefficient 1
{20},{21}!-Sensible Cooling Capacity Coefficient 2
{22},{23}!-Sensible Cooling Capacity Coefficient 3
{24},{25}!-Sensible Cooling Capacity Coefficient 4
{26},{27}!-Sensible Cooling Capacity Coefficient 5
{28},{29}!-Cooling Compressor Power Coefficient 1
{30},{31}!-Cooling Compressor Power Coefficient 2
{32},{33}!-Cooling Compressor Power Coefficient 3
{34},{35}!-Cooling Compressor Power Coefficient 4
{36},{37}!-Cooling Compressor Power Coefficient 5
{38};{39}!-Cycle Time
        """
        return self.fill_eplus_object_format(fields, form)

    def to_parameter_summary(self) -> str:
        output = f"""{self.name}
**Begin Nomenclature**
TC: Total Cooling Capacity
SC: Sensible Capacity
CP: Cooling Power Consumption
TLI: Entering Load-side Temperature
TSI: Entering Source-side Temperature
VLI: Entering Load-side Flow Rate
VSI: Entering Source-side Flow Rate
Subscript _R: Rated Value
Subscript _#: Coefficient #
**End Nomenclature**

**Begin Governing Equations**
(TC/TC_R) = TC_1 + TC_2*(TLI/TLI_R) + TC_3*(TSI/TSI_R) + TC_4*(VLI/VLI_R) + TC_5*(VSI/VSI_R)
(SC/SC_R) = SC_1 + SC_2*(TLI/TLI_R) + SC_3*(TSI/TSI_R) + SC_4*(VLI/VLI_R) + SC_5*(VSI/VSI_R)
(CP/CP_R) = CP_1 + CP_2*(TLI/TLI_R) + CP_3*(TSI/TSI_R) + CP_4*(VLI/VLI_R) + CP_5*(VSI/VSI_R)
**End Governing Equations**

**Begin Reporting Parameters**
Rated Load-side Total Cooling Capacity: {self.rated_total_capacity}
Rated Load-side Sensible Cooling Capacity: {self.rated_sensible_capacity}
Rated Cooling Power Consumption: {self.rated_compressor_power}
Rated Load-side Volumetric Flow Rate: {self.rated_load_volume_flow_rate}
Rated Source-side Volumetric Flow Rate: {self.rated_source_volume_flow_rate}
"""
        for i, c in enumerate(self.total_capacity_params):
            output += f"Cooling Total Capacity Coefficient TC_{i + 1}: {round(c, 4)}\n"
        for i, c in enumerate(self.sensible_capacity_params):
            output += f"Cooling Sensible Capacity Coefficient SC_{i + 1}: {round(c, 4)}\n"
        for i, c in enumerate(self.compressor_power_params):
            output += f"Cooling Power Consumption Coefficient CP_{i + 1}: {round(c, 4)}\n"
        output += "**End Reporting Parameters**"
        return output

    def to_eplus_epjson_object(self) -> str:
        base_values_dict = {
            'source_inlet_node': 'Your Coil Source Side Inlet Node',
            'source_outlet_node': 'Your Coil Source Side Outlet Node',
            'load_inlet_node': 'Your Coil Load Side Inlet Node',
            'load_outlet_node': 'Your Coil Load Side Outlet Node',
            'rated_capacity': self.rated_total_capacity,
            'rated_sensible_capacity': self.rated_sensible_capacity,
            'rated_power_consumption': self.rated_compressor_power,
            'rated_load_side_volume_flow': self.rated_load_volume_flow_rate,
            'rated_source_side_volume_flow': self.rated_source_volume_flow_rate,
            'cycle_time': -999
        }
        capacity_coefficient_dict = {
            f"cooling_capacity_coefficient_{i+1}": round(c, 4) for i, c in enumerate(self.total_capacity_params)
        }
        sensible_coefficient_dict = {
            f"sensible_capacity_coefficient_{i+1}": round(c, 4) for i, c in enumerate(self.sensible_capacity_params)
        }
        power_coefficient_dict = {
            f"compressor_power_coefficient_{i+1}": round(c, 4) for i, c in enumerate(self.compressor_power_params)
        }
        epjson_object = {
            'HeatPump:WaterToAir:EquationFit:Cooling': {
                'Your Coil Name': {
                    **base_values_dict,
                    **capacity_coefficient_dict,
                    **sensible_coefficient_dict,
                    **power_coefficient_dict
                }
            }
        }
        return dumps(epjson_object, indent=2)

    def get_number_of_progress_steps(self) -> int:
        return 4  # read data, tc curve fit, sc curve fit, power curve fit

    def minimum_data_points_for_generation(self) -> int:
        return 5

    def generate_parameters(
            self, data_manager: CatalogDataManager,  cb_progress_increment: Callable, cb_progress_done: Callable
    ):
        # step 1, read the data into arrays (will be used for both scaling calculations and plotting later)
        # these should already be set to zero, but not sure if the main form will reinitialize the equip-instance or not
        self.catalog_source_side_inlet_temp = []
        self.catalog_source_side_volume_flow_rate = []
        self.catalog_load_side_inlet_temp = []
        self.catalog_load_side_volume_flow_rate = []
        self.catalog_load_side_cooling_capacity = []
        self.catalog_load_side_sensible_capacity = []
        self.catalog_compressor_power = []
        scaled_source_side_inlet_temp = []
        scaled_source_side_flow_rate = []
        scaled_load_side_inlet_temp = []
        scaled_load_side_flow_rate = []
        scaled_cooling_capacity = []
        scaled_sensible_capacity = []
        scaled_compressor_power = []
        ones = []
        for data_row in data_manager.final_data_matrix:
            self.catalog_source_side_inlet_temp.append(data_row[0])
            self.catalog_source_side_volume_flow_rate.append(data_row[1])
            self.catalog_load_side_inlet_temp.append(data_row[2])
            self.catalog_load_side_volume_flow_rate.append(data_row[3])
            self.catalog_load_side_cooling_capacity.append(data_row[4])
            self.catalog_load_side_sensible_capacity.append(data_row[5])
            self.catalog_compressor_power.append(data_row[6])
            scaled_source_side_inlet_temp.append((data_row[0] + 273.15) / (10.0 + 273.15))  # T_ref defined by HP model
            scaled_source_side_flow_rate.append(data_row[1] / self.rated_source_volume_flow_rate)
            scaled_load_side_inlet_temp.append((data_row[2] + 273.15) / (10.0 + 273.15))
            scaled_load_side_flow_rate.append(data_row[3] / self.rated_load_volume_flow_rate)
            scaled_cooling_capacity.append(data_row[4] / self.rated_total_capacity)
            scaled_sensible_capacity.append(data_row[5] / self.rated_sensible_capacity)
            scaled_compressor_power.append(data_row[6] / self.rated_compressor_power)
            ones.append(1.0)
        cb_progress_increment()

        independent_var_arrays = (
            ones,
            scaled_load_side_inlet_temp,
            scaled_source_side_inlet_temp,
            scaled_load_side_flow_rate,
            scaled_source_side_flow_rate
        )

        self.total_capacity_params, self.cooling_capacity_average_err_one_sigma = self.do_one_curve_fit(
            CommonCurves.heat_pump_5_coefficient_curve,
            independent_var_arrays,
            scaled_cooling_capacity
        )
        cb_progress_increment()

        self.sensible_capacity_params, self.sensible_capacity_average_err_one_sigma = self.do_one_curve_fit(
            CommonCurves.heat_pump_5_coefficient_curve,
            independent_var_arrays,
            scaled_sensible_capacity
        )
        cb_progress_increment()

        self.compressor_power_params, self.compressor_power_average_err_one_sigma = self.do_one_curve_fit(
            CommonCurves.heat_pump_5_coefficient_curve,
            independent_var_arrays,
            scaled_compressor_power
        )
        cb_progress_increment()

        # now just recalculate the values at each catalog data point
        self.predicted_load_side_cooling_capacity, self.error_load_side_cooling_capacity = self.eval_curve_at_points(
            lambda *x: CommonCurves.heat_pump_5_coefficient_curve_raw_value(*x, self.rated_total_capacity),
            independent_var_arrays,
            self.total_capacity_params,
            self.catalog_load_side_cooling_capacity
        )
        self.predicted_load_side_sensible_capacity, self.error_load_side_sensible_capacity = self.eval_curve_at_points(
            lambda *x: CommonCurves.heat_pump_5_coefficient_curve_raw_value(*x, self.rated_sensible_capacity),
            independent_var_arrays,
            self.sensible_capacity_params,
            self.catalog_load_side_sensible_capacity
        )
        self.predicted_compressor_power, self.error_compressor_power = self.eval_curve_at_points(
            lambda *x: CommonCurves.heat_pump_5_coefficient_curve_raw_value(*x, self.rated_compressor_power),
            independent_var_arrays,
            self.compressor_power_params,
            self.catalog_compressor_power
        )
        cb_progress_done(True)

    def get_absolute_plot_data(self) -> Tuple:
        return (
            ('Total Heat Transfer Model Output', 'line', 'red', self.predicted_load_side_cooling_capacity),
            ('Total Heat Transfer Catalog Input', 'point', 'red', self.catalog_load_side_cooling_capacity),
            ('Sensible Heat Transfer Model Output', 'line', 'red', self.predicted_load_side_sensible_capacity),
            ('Sensible Heat Transfer Catalog Input', 'point', 'red', self.catalog_load_side_sensible_capacity),
            ('Compressor Power Model Output', 'line', 'green', self.predicted_compressor_power),
            ('Compressor Power Catalog Input', 'point', 'green', self.catalog_compressor_power),
        )

    def get_error_plot_data(self) -> Tuple:
        return (
            ('Total Heat Transfer % Error', 'line', 'red', self.error_load_side_cooling_capacity),
            ('Sensible Heat Transfer % Error', 'line', 'red', self.error_load_side_sensible_capacity),
            ('Compressor Power % Error', 'line', 'green', self.error_compressor_power),
        )

    def get_extra_regression_metrics(self) -> Tuple:
        return (
            (
                "Total Heat Transfer Average curve-fit error (1 standard deviation)",
                self.cooling_capacity_average_err_one_sigma
            ),
            (
                "Sensible Heat Transfer Average curve-fit error (1 standard deviation)",
                self.sensible_capacity_average_err_one_sigma
            ),
            (
                "Compressor Power Average curve-fit error (1 standard deviation)",
                self.compressor_power_average_err_one_sigma
            )
        )
