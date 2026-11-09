Air-to-Water Heat Pump Curve Fits
=================================

The air-to-water heat pump curve fits model single-speed heating and cooling
performance using the EnergyPlus ``HeatPump:AirToWater`` object. Capacity and
energy input ratio (EIR) are represented by biquadratic curves of outdoor
entering dry-bulb temperature and leaving water temperature.

Catalog data
------------

- Outdoor entering dry-bulb temperature [UnitType.Temperature]
- Leaving water temperature [UnitType.Temperature]
- Heating or cooling capacity [UnitType.Power]
- Heating or cooling power [UnitType.Power]

Required rated parameters are capacity, power, air flow, water flow, outdoor
air temperature, and leaving water temperature. Rated conditions default to
8 C outdoor air and 40 C leaving water for heating, and 30 C outdoor air and
8 C leaving water for cooling. The generated AWHP IDF and EpJSON include an
EnergyPlus 25.2 version declaration because ``HeatPump:AirToWater`` was not
available in earlier EnergyPlus schemas. Existing equipment types continue to
use the project's EnergyPlus 22.2 output version.

.. automodule:: energyplus_pet.equipment.awhp_curve
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:
