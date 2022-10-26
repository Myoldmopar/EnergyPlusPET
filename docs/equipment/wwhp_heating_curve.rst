Water-to-Water Heat Pump Heating Mode Curve Fit
===============================================

The water-to-water heat pump, heating mode, curve-fit formulation provides inputs using the
quad-linear formulation for both load side heating capacity and power input.

Required Columnar Data
----------------------
- Source-side Entering Temp [UnitType.Temperature]
- Source-side Volume Flow [UnitType.Flow]
- Load-side Entering Temp [UnitType.Temperature]
- Load-side Volume Flow [UnitType.Flow]
- Total Heating Capacity [UnitType.Power]
- Heating Power [UnitType.Power]

Required Fixed Parameters
-------------------------

- Rated Load-side Flow Rate [UnitType.Flow]
- Rated Source-side Flow Rate [UnitType.Flow]
- Rated Total Heating Capacity [UnitType.Power]
- Rated Heating Power [UnitType.Power]

.. automodule:: energyplus_pet.equipment.wwhp_heating_curve
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:
