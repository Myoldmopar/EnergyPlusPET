from json import dumps
from time import sleep
from typing import Callable, List

from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.column_header import ColumnHeaderArray, ColumnHeader
from energyplus_pet.units import UnitType, BaseUnit, FlowUnits, PowerUnits


class WaterToWaterHeatPumpHeatingCurveFit(BaseEquipment):

    def __init__(self):
        # need some rated parameters that we get from the user for scaling, reporting, etc.
        self.rated_load_volume_flow_rate = FlowUnits(
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
        self.c1 = [0.0] * 5
        self.c2 = [0.0] * 5
        # store the predicted outputs that are calculated from the generated parameters
        self.predicted_load_side_heating_capacity = []
        self.predicted_compressor_power = []
        self.predicted_source_side_heat_absorption = []

    def this_type(self) -> EquipType:
        return EquipType.WWHP_Heating_CurveFit

    def name(self) -> str:
        return "Water to Water Heat Pump, Heating Mode, Curve Fit Formulation"

    def required_constant_parameters(self) -> List[BaseUnit]:
        return [
            self.rated_load_volume_flow_rate,
            self.rated_source_volume_flow_rate,
            self.rated_total_capacity,
            self.rated_compressor_power
        ]

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
        fields.extend(self.c1)
        fields.extend(self.c1)
        fields.append('Your Heat Pump Cycle Time')
        form = """
HeatPump:WaterToWater:EquationFit:Heating,
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
        output = f"""{self.name}
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
        for i, c in enumerate(self.c1):
            output += f"Heating Capacity Coefficient HC_{i + 1}: {round(c, 4)}\n"
        for i, c in enumerate(self.c2):
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
        capacity_coefficient_dict = {f"heating_capacity_coefficient_{i+1}": round(c, 4) for i, c in enumerate(self.c1)}
        power_coefficient_dict = {f"compressor_power_coefficient_{i+1}": round(c, 4) for i, c in enumerate(self.c2)}
        epjson_object = {
            'WWHP:Heating:CurveFit': {
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
        cb_progress_initialize(3)
        for i in range(3):
            sleep(1)
            cb_progress_increment()
        cb_progress_done('DONE')
        # set some constants
        # initialize_progress based on the total count of increments
        # load data into local arrays from full catalog dataset
        # for each matrix equation to solve
        #     create F matrix to size of num data points x num coefficients
        #     create Y vector to size of num data points
        #     increment_progress
        #     (x is data point index)
        #     fill F[x, ...] = [1, ScaledRatedTemp[x], ScaledRatedTemp[x], ScaledRatedFlow[x], ScaledRatedFlow[x]]
        #     increment_progress
        #     fill Y[x] = [ScaledHeatCapacity[x]] or [ScaledCompressorPower[x]] or whatever equation we are solving
        #     increment_progress
        #     solve the equation: C1 (or C2) = SolveEqSet(F, Y)
        #     catch matrix error
        #     increment_progress
        #     fill in local predicted output arrays:
        #       predicted_heating_capacity[x] = rated + C1[0]*F[x, 0] + C1[1]*F[x,1] etc.
        #       similar for predicted_compressor_power[x]
        #       then predicted_source_heat_absorption[x] = predicted_heating_capacity[x] - predicted_compressor_power[x]
        #     increment_progress

    def generate_absolute_plot(self):
        pass

    def generate_error_plot(self):
        pass

#
# if __name__ == "__main__":
#     w = WaterToWaterHeatPumpHeatingCurveFit()
#     w.rated_compressor_power.value = 100.0
#     print(w.to_eplus_idf_object())
#     print(w.to_parameter_summary())
