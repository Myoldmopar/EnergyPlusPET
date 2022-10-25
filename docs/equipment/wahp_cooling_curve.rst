Water-to-Air Heat Pump Cooling Mode Curve Fit
=============================================

The water-to-air heat pump, cooling mode, curve-fit formulation provides inputs using the
quad-linear formulation for both load side cooling capacity and power input, and a
quint-linear formulation for sensible cooling capacity.

Required Columnar Data
----------------------

- Water-side Entering Temp [UnitType.Temperature]
- Water-side Volume Flow [UnitType.Flow]
- Air-side Entering Dry-bulb Temp [UnitType.Temperature]
- Air-side Volume Flow [UnitType.Flow]
- Heating Capacity [UnitType.Power]
- Heating Power [UnitType.Power]

Required Fixed Parameters
-------------------------

- Rated Air Flow Rate [UnitType.Flow]
- Rated Water Flow Rate [UnitType.Flow]
- Rated Total Heating Capacity [UnitType.Power]
- Rated Heating Power [UnitType.Power]

.. automodule:: energyplus_pet.equipment.wahp_cooling_curve
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:
