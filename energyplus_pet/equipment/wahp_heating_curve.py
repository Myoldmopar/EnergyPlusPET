from typing import List
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.equip_types import EquipType


class WaterToAirHeatPumpHeatingCurveFit(BaseEquipment):

    def __init__(self):
        super().__init__()
        # self.RatedLoadVolFlowRate = 0.0
        # self.RatedSourceVolFlowRate = 0.0
        # self.RatedTotalCapacity = 0.0
        # self.RatedCompressorPower = 0.0
        #
        # self.SourceSideInletTemp = []
        # self.SourceSideVolFlowRate = []
        # self.LoadSideInletTemp = []
        # self.LoadSideVolFlowRate = []
        # self.TotalHeatingCapacity = []
        # self.CompressorPower = []
        # self.HeatAbsorption = []
        # self.PredictedTotHtgCapacity = []
        # self.PredictedSourceHtgRate = []
        # self.PredictedPowerInput = []

    def this_type(self) -> EquipType:
        return EquipType.WAHP_Heating_CurveFit

    def header_units(self) -> List[str]:
        pass

    def header_strings(self) -> List[str]:
        pass

    def to_eplus_idf_object(self) -> str:
        pass
#         fields = [
#             'Your Coil Name',
#             'Your Coil Source Side Inlet Node',
#             'Your Coil Source Side Outlet Node',
#             'Your Coil Load Side Inlet Node',
#             'Your Coil Load Side Outlet Node',
#             self.RatedLoadVolFlowRate,
#             self.RatedSourceVolFlowRate,
#             self.RatedTotalCapacity,
#             self.RatedTotalCapacity / self.Rated
#         ]
#         return f"""
# HeatPump:WaterToWater:EquationFit:Heating,
# {0},{1}!-Name
# {2},{3}!-Source Side Inlet Node Name
# {4},{5}!-Source Side Outlet Node Name
# {6},{7}!-Load Side Inlet Node Name
# {8},{9}!-Load Side Outlet Node Name
# {10},{11}!-Rated Load Side Flow Rate
# {12},{13}!-Rated Source Side Flow Rate
# {14},{15}!-Rated Heating Capacity
# {16},{17}!-Rated Heating COP
# {18},{19}!-Heating Capacity Coefficient 1
# {20},{21}!-Heating Capacity Coefficient 2
# {22},{23}!-Heating Capacity Coefficient 3
# {24},{25}!-Heating Capacity Coefficient 4
# {26},{27}!-Heating Capacity Coefficient 5
# {28},{29}!-Heating Compressor Power Coefficient 1
# {30},{31}!-Heating Compressor Power Coefficient 2
# {32},{33}!-Heating Compressor Power Coefficient 3
# {34},{35}!-Heating Compressor Power Coefficient 4
# {36},{37}!-Heating Compressor Power Coefficient 5
# {38};{39}!-Cycle Time
#         """


    def to_parameter_summary(self) -> str:
        pass

    def to_eplus_epjson_object(self) -> str:
        pass

    def generate_parameters(self):
        pass

    def generate_absolute_plot(self):
        pass

    def generate_error_plot(self):
        pass
