Water-to-Air Heat Pump Heating Mode Curve Fit
=============================================

The water-to-air heat pump, heating mode, curve-fit formulation provides inputs using the
quad-linear formulation for both load side heating capacity and power input.

Required Columnar Data
----------------------

- Water-side Entering Temp [UnitType.Temperature]
- Water-side Volume Flow [UnitType.Flow]
- Air-side Entering Dry-bulb Temp [UnitType.Temperature]
- Air-side Entering Wet-bulb Temp [UnitType.Temperature]
- Air-side Volume Flow [UnitType.Flow]
- Total Cooling Capacity [UnitType.Power]
- Sensible Cooling Capacity [UnitType.Power]
- Cooling Power [UnitType.Power]

Required Fixed Parameters
-------------------------

- Rated Air Flow Rate [UnitType.Flow]
- Rated Water Flow Rate [UnitType.Flow]
- Rated Total Cooling Capacity [UnitType.Power]
- Rated Sensible Cooling Capacity [UnitType.Power]
- Rated Cooling Power [UnitType.Power]

.. automodule:: energyplus_pet.equipment.wahp_heating_curve
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:
