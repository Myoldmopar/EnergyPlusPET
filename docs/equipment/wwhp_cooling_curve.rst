Water-to-Water Heat Pump Cooling Mode Curve Fit
===============================================

The water-to-water heat pump, cooling mode, curve-fit formulation provides inputs using the
quad-linear formulation for both load side cooling capacity and power input.

Required Columnar Data
----------------------
- Source-side Entering Temp [UnitType.Temperature]
- Source-side Volume Flow [UnitType.Flow]
- Load-side Entering Temp [UnitType.Temperature]
- Load-side Volume Flow [UnitType.Flow]
- Total Cooling Capacity [UnitType.Power]
- Cooling Power [UnitType.Power]

Required Fixed Parameters
-------------------------

- Rated Load-side Flow Rate [UnitType.Flow]
- Rated Source-side Flow Rate [UnitType.Flow]
- Rated Total Cooling Capacity [UnitType.Power]
- Rated Cooling Power [UnitType.Power]

.. automodule:: energyplus_pet.equipment.wwhp_cooling_curve
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:
