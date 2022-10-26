from json import dumps
from typing import Callable, List, Tuple

from energyplus_pet.equipment.common_curves import CommonCurves
from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.column_header import ColumnHeaderArray, ColumnHeader
from energyplus_pet.exceptions import EnergyPlusPetException
from energyplus_pet.units import UnitType


class WaterToAirHeatPumpHeatingCurveFit(BaseEquipment):
    """
    This class represents a water-to-air heat pump, heating mode, using the model formulation:
    Q = Q_rated * (A + B * Tl + C * Ts + D * Vl + E * Vs)
    P = P_rated * (F + G * Tl + H * Ts + I * Vl + J * Vs)
    where:
    Q is the load side heat transfer rate
    P is the heating power
    _rated indicates the nominal operating value
    A-J are curve fit coefficients
    Tl and Ts are scaled load and source side inlet temps (T/283.15) where original T is in Kelvin
    Vl and Vs are scaled load and source side volume flow rates (V/V_rated)
    """

    def __init__(self):
        # need some rated parameters that we get from the user for scaling, reporting, etc.
        self.rated_air_volume_flow_key = 'vl'
        self.rated_air_volume_flow = 0.0
        self.rated_water_volume_flow_key = 'vs'
        self.rated_water_volume_flow = 0.0
        self.rated_heating_capacity_key = 'qh'
        self.rated_heating_capacity = 0.0
        self.rated_heating_power_key = 'cp'
        self.rated_heating_power = 0.0
        # store some individual arrays for each of the dependent variable input columns
        self.catalog_heating_capacity = []
        self.catalog_heating_power = []
        # these eventually become the actual parameter arrays
        self.heating_capacity_params = []
        self.heating_power_params = []
        # these represent a metric for the quality of the regression
        self.heating_capacity_avg_err = 0.0
        self.heating_power_avg_err = 0.0
        # store the predicted outputs that are calculated from the generated parameters
        self.predicted_heating_capacity = []
        self.predicted_heating_power = []
        self.percent_error_heating_capacity = []
        self.percent_error_heating_power = []
        # store the headers on the instance, so we don't reconstruct it every call to headers()
        self._headers = ColumnHeaderArray(
            [
                ColumnHeader("Water-side Entering Temp", UnitType.Temperature),
                ColumnHeader("Water-side Volume Flow", UnitType.Flow),
                ColumnHeader("Air-side Entering Dry-bulb Temp", UnitType.Temperature, db=True),
                ColumnHeader("Air-side Volume Flow", UnitType.Flow),
                ColumnHeader("Heating Capacity", UnitType.Power),
                ColumnHeader("Heating Power", UnitType.Power)
            ]
        )

    def this_type(self) -> EquipType:
        return EquipType.WAHP_Heating_CurveFit

    def name(self) -> str:
        return "Water to Air Heat Pump, Heating Coil, Curve Fit Formulation"

    def short_name(self) -> str:
        return "WAHP-Heating-CurveFit"

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
                self.rated_heating_capacity_key,
                "Rated Total Heating Capacity",
                "This is a nominal value of the load-side heating capacity of the coil",
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
        if parameter_id == self.rated_air_volume_flow_key:
            self.rated_air_volume_flow = new_value
        elif parameter_id == self.rated_water_volume_flow_key:
            self.rated_water_volume_flow = new_value
        elif parameter_id == self.rated_heating_capacity_key:
            self.rated_heating_capacity = new_value
        elif parameter_id == self.rated_heating_power_key:
            self.rated_heating_power = new_value
        else:
            raise EnergyPlusPetException("Bad parameter ID in set_required_constant_parameter")

    def headers(self) -> ColumnHeaderArray:
        return self._headers

    def to_eplus_idf_object(self) -> str:
        object_name = "Coil:Heating:WaterToAirHeatPump:EquationFit"
        fields = [
            ("Name", 'Your Coil Name'),
            ("Water Inlet Node Name", 'Your Coil Source Side Inlet Node'),
            ("Water Outlet Node Name", 'Your Coil Source Side Outlet Node'),
            ("Air Inlet Node Name", 'Your Coil Load Side Inlet Node'),
            ("Air Outlet Node Name", 'Your Coil Load Side Outlet Node'),
            ("Rated Air Flow Rate", self.rated_air_volume_flow),
            ("Rated Water Flow Rate", self.rated_water_volume_flow),
            ("Gross Rated Heating Capacity", self.rated_heating_capacity),
            ("Gross Rated Heating COP", round(self.rated_heating_capacity / self.rated_heating_power, 4)),
            ("Rated Entering Water Temperature", ''),
            ("Rated Entering Air Dry-Bulb Temp", ''),
            ("Ratio of Rated Heating Capacity to Rated Cooling Capacity", ''),
            ("Heating Capacity Curve Name", 'TotalCapacityCurve'),
            ("Heating Power Consumption Curve Name", 'HeatingPowerCurve'),
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
            *[(f"Coefficient{i}", self.heating_capacity_params[i]) for i in range(5)],
            *reused_limits
        ]
        total_curve_output = self.fill_eplus_object_format(object_name, fields)

        object_name = "Curve:QuadLinear"
        fields = [
            ("Name", "HeatingPowerCurve"),
            *[(f"Coefficient{i}", self.heating_power_params[i]) for i in range(5)],
            *reused_limits
        ]
        sensible_curve_output = self.fill_eplus_object_format(object_name, fields)

        return '\n'.join([
            BaseEquipment.current_eplus_version_object_idf(),
            coil_object_string,
            total_curve_output, sensible_curve_output
        ])

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
Rated Load-side Heating Capacity: {self.rated_heating_capacity}
Rated Heating Power Consumption: {self.rated_heating_power}
Rated Load-side Volumetric Flow Rate: {self.rated_air_volume_flow}
Rated Source-side Volumetric Flow Rate: {self.rated_water_volume_flow}
"""
        for i, c in enumerate(self.heating_capacity_params):
            output += f"Heating Capacity Coefficient HC_{i + 1}: {round(c, 4)}\n"
        for i, c in enumerate(self.heating_power_params):
            output += f"Heating Power Consumption Coefficient HC_{i + 1}: {round(c, 4)}\n"
        output += "**End Reporting Parameters**"
        return output

    def to_eplus_epjson_object(self) -> str:
        coil_object = {'Your Coil Name': {
            'water_inlet_node_name': 'Your Coil Source Side Inlet Node',
            'water_outlet_node_name': 'Your Coil Source Side Outlet Node',
            'air_inlet_node_name': 'Your Coil Load Side Inlet Node',
            'air_outlet_node_name': 'Your Coil Load Side Outlet Node',
            'rated_air_flow_rate': self.rated_air_volume_flow,
            'rated_water_flow_rate': self.rated_water_volume_flow,
            'gross_rated_heating_capacity': self.rated_heating_capacity,
            'gross_rated_heating_cop': self.rated_heating_capacity / self.rated_heating_power,
            'rated_entering_water_temperature': '',
            'rated_entering_air_dry_bulb_temperature': '',
            'ratio_of_rated_heating_capacity_to_rated_cooling_capacity': '',
            'heating_capacity_curve_name': 'TotalCapacityCurve',
            'heating_power_consumption_curve_name': 'HeatingPowerCurve',
        }}
        reused_limits = {
            "minimum_value_of_w": -100, "maximum_value_of_w": 100,
            "minimum_value_of_x": -100, "maximum_value_of_x": 100,
            "minimum_value_of_y": -100, "maximum_value_of_y": 100,
            "minimum_value_of_z": -100, "maximum_value_of_z": 100,
        }
        curves = {'TotalCapacityCurve': {
            "coefficient1_constant": self.heating_capacity_params[0],
            "coefficient2_w": self.heating_capacity_params[1],
            "coefficient3_x": self.heating_capacity_params[2],
            "coefficient4_y": self.heating_capacity_params[3],
            "coefficient5_z": self.heating_capacity_params[4],
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
            'Coil:Heating:WaterToAirHeatPump:EquationFit': coil_object,
            'Curve:QuadLinear': curves
        }
        return dumps(epjson_object, indent=2)

    def get_number_of_progress_steps(self) -> int:
        return 3  # read data, hc curve fit, power curve fit

    def minimum_data_points_for_generation(self) -> int:
        return 5

    def generate_parameters(
            self, data_manager: CatalogDataManager, cb_progress_increment: Callable, cb_progress_done: Callable
    ):
        # step 1, read the data into arrays (will be used for both scaling calculations and plotting later)
        # these should already be set to zero, but not sure if the main form will reinitialize the equip-instance or not
        self.catalog_heating_capacity = [x[4] for x in data_manager.final_data_matrix]
        self.catalog_heating_power = [x[5] for x in data_manager.final_data_matrix]
        scaled_water_inlet_temp = []
        scaled_water_flow_rate = []
        scaled_air_inlet_temp = []
        scaled_air_flow_rate = []
        scaled_heating_capacity = []
        scaled_heating_power = []
        for data_row in data_manager.final_data_matrix:
            scaled_water_inlet_temp.append((data_row[0] + 273.15) / (10.0 + 273.15))  # T_ref defined by HP model
            scaled_water_flow_rate.append(data_row[1] / self.rated_water_volume_flow)
            scaled_air_inlet_temp.append((data_row[2] + 273.15) / (10.0 + 273.15))
            scaled_air_flow_rate.append(data_row[3] / self.rated_air_volume_flow)
            scaled_heating_capacity.append(data_row[4] / self.rated_heating_capacity)
            scaled_heating_power.append(data_row[5] / self.rated_heating_power)
        cb_progress_increment()

        independent_var_arrays = (
            scaled_air_inlet_temp,
            scaled_water_inlet_temp,
            scaled_air_flow_rate,
            scaled_water_flow_rate
        )

        self.heating_capacity_params, self.heating_capacity_avg_err = self.do_one_curve_fit(
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
        self.predicted_heating_capacity, self.percent_error_heating_capacity = self.eval_curve_at_points(
            lambda *x: CommonCurves.heat_pump_5_coefficient_curve_raw_value(*x, self.rated_heating_capacity),
            independent_var_arrays,
            self.heating_capacity_params,
            self.catalog_heating_capacity
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
            ('Total Heat Transfer Model', 'line', 'red', self.predicted_heating_capacity),
            ('Total Heat Transfer Catalog', 'point', 'red', self.catalog_heating_capacity),
            ('Heating Power Model', 'line', 'green', self.predicted_heating_power),
            ('Heating Power Catalog', 'point', 'green', self.catalog_heating_power),
        )

    def get_error_plot_data(self) -> Tuple:
        return (
            ('Total Heat Transfer % Error', 'line', 'red', self.percent_error_heating_capacity),
            ('Heating Power % Error', 'line', 'green', self.percent_error_heating_power),
        )

    def get_extra_regression_metrics(self) -> Tuple:
        return (
            (
                "Total Heat Transfer Average curve-fit error (1 standard deviation)",
                self.heating_capacity_avg_err
            ),
            (
                "Heating Power Average curve-fit error (1 standard deviation)",
                self.heating_power_avg_err
            )
        )
