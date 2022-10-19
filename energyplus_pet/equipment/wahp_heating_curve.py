from json import dumps
from typing import Callable, List, Tuple

from scipy.optimize import curve_fit

from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.column_header import ColumnHeaderArray, ColumnHeader
from energyplus_pet.units import UnitType, BaseUnit, FlowUnits, PowerUnits


class WaterToAirHeatPumpHeatingCurveFit(BaseEquipment):

    def __init__(self):
        # need some rated parameters that we get from the user for scaling, reporting, etc.
        self.rated_load_volume_flow_rate = FlowUnits(  # TODO: Get these from a form!
            0.0006887, "Rated Load Side Flow Rate",
            "This is a nominal flow rate value for the load-side of the heat pump"
        )
        self.rated_source_volume_flow_rate = FlowUnits(
            0.0001892, "Rated Source Side Flow Rate",
            "This is a nominal flow rate value for the source-side of the heat pump"
        )
        self.rated_total_capacity = PowerUnits(
            3.513, "Rated Total Heating Capacity",
            "This is a nominal value of the load-side heating capacity of the heat pump"
        )
        self.rated_compressor_power = PowerUnits(
            0.900, "Rated Compressor Power Use",
            "This is a nominal value of the compressor power for this heat pump"
        )
        # store some individual arrays for each of the input columns
        self.catalog_source_side_inlet_temp = []
        self.catalog_source_side_volume_flow_rate = []
        self.catalog_load_side_inlet_temp = []
        self.catalog_load_side_volume_flow_rate = []
        self.catalog_load_side_heating_capacity = []
        self.catalog_compressor_power = []
        self.catalog_source_side_heat_absorption = []
        # these are matrices in the original code, here just store the final vector
        self.heating_capacity_params = []
        self.compressor_power_params = []
        # store the predicted outputs that are calculated from the generated parameters
        self.predicted_load_side_heating_capacity = []
        self.predicted_compressor_power = []
        self.predicted_source_side_heat_absorption = []
        self.percent_error_load_side_heating_capacity = []
        self.percent_error_compressor_power = []
        self.percent_error_source_side_heat_absorption = []

    def this_type(self) -> EquipType:
        return EquipType.WAHP_Heating_CurveFit

    def name(self) -> str:
        return "Water to Air Heat Pump, Heating Mode, Curve Fit Formulation"

    def short_name(self) -> str:
        return "WAHP-Heating-CurveFit"

    def required_constant_parameters(self) -> List[BaseUnit]:
        # TODO: CDM should hold a dict of strings and values or something, and the equipment can decode it here
        return [
            self.rated_load_volume_flow_rate,
            self.rated_source_volume_flow_rate,
            self.rated_total_capacity,
            self.rated_compressor_power
        ]

    def set_required_constant_parameter(self, parameter_name: str, new_value: float) -> None:
        my_param_names = self.required_constant_parameters()
        if parameter_name == my_param_names[0].name:
            self.rated_load_volume_flow_rate.value = new_value
        elif parameter_name == my_param_names[1].name:
            self.rated_source_volume_flow_rate.value = new_value
        elif parameter_name == my_param_names[2].name:
            self.rated_total_capacity.value = new_value
        elif parameter_name == my_param_names[3].name:
            self.rated_compressor_power.value = new_value
        else:
            pass  # ERROR

    def headers(self) -> ColumnHeaderArray:
        return ColumnHeaderArray(
            [
                ColumnHeader("Source Side Entering Temp", UnitType.Temperature),
                ColumnHeader("Source Side Flow Rate", UnitType.Flow),
                ColumnHeader("Load Side Entering Temp", UnitType.Temperature),
                ColumnHeader("Load Side Flow Rate", UnitType.Flow),
                ColumnHeader("Load Side Heating Capacity", UnitType.Power),
                ColumnHeader("Compressor Power Input", UnitType.Power),
                ColumnHeader("Source Side Heat Absorption", UnitType.Power),
            ]
        )

    def to_eplus_idf_object(self) -> str:
        fields = [
            'Your Coil Name',
            'Your Coil Source Side Inlet Node',
            'Your Coil Source Side Outlet Node',
            'Your Coil Load Side Inlet Node',
            'Your Coil Load Side Outlet Node',
            self.rated_load_volume_flow_rate.value,
            self.rated_source_volume_flow_rate.value,
            self.rated_total_capacity.value,
            round(self.rated_total_capacity.value / self.rated_compressor_power.value, 4),
        ]
        fields.extend(self.heating_capacity_params)
        fields.extend(self.compressor_power_params)
        fields.append('Your Heat Pump Cycle Time')
        form = """HeatPump:WaterToAir:EquationFit:Heating,
{0},{1}!-Name
{2},{3}!-Source Side Inlet Node Name
{4},{5}!-Source Side Outlet Node Name
{6},{7}!-Load Side Inlet Node Name
{8},{9}!-Load Side Outlet Node Name
{10},{11}!-Rated Load Side Flow Rate
{12},{13}!-Rated Source Side Flow Rate
{14},{15}!-Rated Heating Capacity
{16},{17}!-Rated Heating COP
{18},{19}!-Heating Capacity Coefficient 1
{20},{21}!-Heating Capacity Coefficient 2
{22},{23}!-Heating Capacity Coefficient 3
{24},{25}!-Heating Capacity Coefficient 4
{26},{27}!-Heating Capacity Coefficient 5
{28},{29}!-Heating Compressor Power Coefficient 1
{30},{31}!-Heating Compressor Power Coefficient 2
{32},{33}!-Heating Compressor Power Coefficient 3
{34},{35}!-Heating Compressor Power Coefficient 4
{36},{37}!-Heating Compressor Power Coefficient 5
{38};{39}!-Cycle Time
                """
        return self.fill_eplus_object_format(fields, form)

    def to_parameter_summary(self) -> str:
        output = f"""{self.name()}
**Begin Nomenclature**
HC: Heating Capacity
HP: Heating Power Consumption
TLI: Entering Load-side Temperature
TSI: Entering Source-side Temperature
VLI: Entering Load-side Flow Rate
VSI: Entering Source-side Flow Rate
Subscript _R: Rated Value
Subscript _#: Coefficient #
**End Nomenclature**

**Begin Governing Equations**
(HC/HC_R) = HC_1 + HC_2*(TLI/TLI_R) + HC_3*(TSI/TSI_R) + HC_4*(VLI/VLI_R) + HC_5*(VSI/VSI_R)
(HP/HP_R) = HP_1 + HP_2*(TLI/TLI_R) + HP_3*(TSI/TSI_R) + HP_4*(VLI/VLI_R) + HP_5*(VSI/VSI_R)
**End Governing Equations**

**Begin Reporting Parameters**
Rated Load-side Heating Capacity: {self.rated_total_capacity}
Rated Heating Power Consumption: {self.rated_compressor_power}
Rated Load-side Volumetric Flow Rate: {self.rated_load_volume_flow_rate}
Rated Source-side Volumetric Flow Rate: {self.rated_source_volume_flow_rate}
        """
        for i, c in enumerate(self.heating_capacity_params):
            output += f"Heating Capacity Coefficient HC_{i + 1}: {round(c, 4)}\n"
        for i, c in enumerate(self.compressor_power_params):
            output += f"Heating Power Consumption Coefficient HC_{i + 1}: {round(c, 4)}\n"
        output += "**End Reporting Parameters**"
        return output

    def to_eplus_epjson_object(self) -> str:
        base_values_dict = {
            'source_inlet_node': 'Your Coil Source Side Inlet Node',
            'source_outlet_node': 'Your Coil Source Side Outlet Node',
            'load_inlet_node': 'Your Coil Load Side Inlet Node',
            'load_outlet_node': 'Your Coil Load Side Outlet Node',
            'rated_capacity': self.rated_total_capacity.value,
            'rated_power_consumption': self.rated_compressor_power.value,
            'rated_load_side_volume_flow': self.rated_load_volume_flow_rate.value,
            'rated_source_side_volume_flow': self.rated_source_volume_flow_rate.value,
            'cycle_time': -999
        }
        capacity_coefficient_dict = {f"heating_capacity_coefficient_{i + 1}": round(c, 4) for i, c in
                                     enumerate(self.heating_capacity_params)}
        power_coefficient_dict = {
            f"compressor_power_coefficient_{i + 1}": round(c, 4) for i, c in enumerate(self.compressor_power_params)
        }
        epjson_object = {
            'WAHP:Heating:CurveFit': {
                'Your Coil Name': {
                    **base_values_dict, **capacity_coefficient_dict, **power_coefficient_dict
                }
            }
        }
        return dumps(epjson_object, indent=2)

    def generate_parameters(
            self, data_manager: CatalogDataManager, cb_progress_initialize: Callable,
            cb_progress_increment: Callable, cb_progress_done: Callable
    ):
        cb_progress_initialize(4)  # read data, hc curve fit, power curve fit, calc predicted data

        # step 1, read the data into arrays (will be used for both scaling calculations and plotting later)
        # these should already be set to zero, but not sure if the main form will reinitialize the equip-instance or not
        self.catalog_source_side_inlet_temp = []
        self.catalog_source_side_volume_flow_rate = []
        self.catalog_load_side_inlet_temp = []
        self.catalog_load_side_volume_flow_rate = []
        self.catalog_load_side_heating_capacity = []
        self.catalog_compressor_power = []
        self.catalog_source_side_heat_absorption = []
        scaled_source_side_inlet_temp = []
        scaled_source_side_flow_rate = []
        scaled_load_side_inlet_temp = []
        scaled_load_side_flow_rate = []
        scaled_heating_capacity = []
        scaled_compressor_power = []
        ones = []
        for data_row in data_manager.final_data_matrix:
            self.catalog_source_side_inlet_temp.append(data_row[0])
            self.catalog_source_side_volume_flow_rate.append(data_row[1])
            self.catalog_load_side_inlet_temp.append(data_row[2])
            self.catalog_load_side_volume_flow_rate.append(data_row[3])
            self.catalog_load_side_heating_capacity.append(data_row[4])
            self.catalog_compressor_power.append(data_row[5])
            self.catalog_source_side_heat_absorption.append(data_row[6])
            scaled_source_side_inlet_temp.append((data_row[0] + 273.15) / (10.0 + 273.15))  # T_ref defined by HP model
            scaled_source_side_flow_rate.append(data_row[1] / self.rated_source_volume_flow_rate.value)
            scaled_load_side_inlet_temp.append((data_row[2] + 273.15) / (10.0 + 273.15))
            scaled_load_side_flow_rate.append(data_row[3] / self.rated_load_volume_flow_rate.value)
            scaled_heating_capacity.append(data_row[4] / self.rated_total_capacity.value)
            scaled_compressor_power.append(data_row[5] / self.rated_compressor_power.value)
            ones.append(1.0)
        cb_progress_increment()

        def evaluate_expression(x, a, b, c, d, e):
            """
            Evaluates:  Y / Y_rated = A*(1.0) + B*(TLI/TLI_R) + C*(TSI/TSI_R) + D*(VLI/VLI_R) + E*(VSI/VSI_R)
            Where Y would represent any of the desired dependent variables, such as Q or Power

            :param x: tuple of independent variables, (1.0, TLI/TLI_R, TSI/TSI_R, VLI/VLI_R, VSI/VSI_R)
            :param a: coefficient A in the above equation
            :param b: coefficient B in the above equation
            :param c: coefficient C in the above equation
            :param d: coefficient D in the above equation
            :param e: coefficient E in the above equation
            :return: Scaled dependent variable, such as Q/Q_rated
            """
            return a * x[0] + b * x[1] + c * x[2] + d * x[3] + e * x[4]

        heating_capacity_params = curve_fit(
            evaluate_expression,
            (
                ones,
                scaled_load_side_inlet_temp,
                scaled_source_side_inlet_temp,
                scaled_load_side_flow_rate,
                scaled_source_side_flow_rate
            ),
            scaled_heating_capacity
        )[0]
        self.heating_capacity_params = list(heating_capacity_params)
        cb_progress_increment()
        compressor_power_params = curve_fit(
            evaluate_expression,
            (
                ones,
                scaled_load_side_inlet_temp,
                scaled_source_side_inlet_temp,
                scaled_load_side_flow_rate,
                scaled_source_side_flow_rate
            ),
            scaled_compressor_power
        )[0]
        self.compressor_power_params = list(compressor_power_params)
        cb_progress_increment()

        # should be empty, but just reset to be sure
        self.predicted_load_side_heating_capacity = []
        self.predicted_compressor_power = []
        self.predicted_source_side_heat_absorption = []
        self.percent_error_load_side_heating_capacity = []
        self.percent_error_compressor_power = []
        self.percent_error_source_side_heat_absorption = []
        for i in range(len(data_manager.final_data_matrix)):
            self.predicted_load_side_heating_capacity.append(self.rated_total_capacity.value * evaluate_expression(
                (
                    ones[i],
                    scaled_load_side_inlet_temp[i],
                    scaled_source_side_inlet_temp[i],
                    scaled_load_side_flow_rate[i],
                    scaled_source_side_flow_rate[i]
                ),
                heating_capacity_params[0],
                heating_capacity_params[1],
                heating_capacity_params[2],
                heating_capacity_params[3],
                heating_capacity_params[4]
            ))
            self.predicted_compressor_power.append(self.rated_compressor_power.value * evaluate_expression(
                (
                    ones[i],
                    scaled_load_side_inlet_temp[i],
                    scaled_source_side_inlet_temp[i],
                    scaled_load_side_flow_rate[i],
                    scaled_source_side_flow_rate[i]
                ),
                compressor_power_params[0],
                compressor_power_params[1],
                compressor_power_params[2],
                compressor_power_params[3],
                compressor_power_params[4]
            ))
            self.predicted_source_side_heat_absorption.append(
                self.predicted_load_side_heating_capacity[i] - self.predicted_compressor_power[i]
            )
            self.percent_error_load_side_heating_capacity.append(
                100.0 * (self.predicted_load_side_heating_capacity[i] - self.catalog_load_side_heating_capacity[i]) /
                self.catalog_load_side_heating_capacity[i]
            )
            self.percent_error_compressor_power.append(
                100.0 * (self.predicted_compressor_power[i] - self.catalog_compressor_power[i]) /
                self.catalog_compressor_power[i]
            )
            self.percent_error_source_side_heat_absorption.append(
                100.0 * (self.predicted_source_side_heat_absorption[i] - self.catalog_source_side_heat_absorption[i]) /
                self.catalog_source_side_heat_absorption[i]
            )
        cb_progress_increment()
        cb_progress_done(True)

    def get_absolute_plot_data(self) -> Tuple:
        return (
            ('Total Heat Transfer Model Output', 'line', 'red', self.predicted_load_side_heating_capacity),
            ('Total Heat Transfer Catalog Input', 'point', 'red', self.catalog_load_side_heating_capacity),
            ('Compressor Power Model Output', 'line', 'green', self.predicted_compressor_power),
            ('Compressor Power Catalog Input', 'point', 'green', self.catalog_compressor_power),
        )

    def get_error_plot_data(self) -> Tuple:
        return (
            ('Total Heat Transfer % Error', 'line', 'red', self.percent_error_load_side_heating_capacity),
            ('Compressor Power % Error', 'line', 'green', self.percent_error_compressor_power),
        )
