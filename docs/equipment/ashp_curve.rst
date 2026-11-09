Air-Source Heat Pump Curve Fits
===============================

The air-source heat pump curve fits model single-speed direct-expansion heating
and cooling coils. Capacity and energy input ratio (EIR) are represented by a
biquadratic temperature curve multiplied by a quadratic airflow-fraction curve,
matching the EnergyPlus DX coil formulation.

Heating catalog data
--------------------

- Outdoor entering dry-bulb temperature [UnitType.Temperature]
- Indoor entering dry-bulb temperature [UnitType.Temperature]
- Air-side volume flow [UnitType.Flow]
- Heating capacity [UnitType.Power]
- Heating power [UnitType.Power]

Cooling catalog data
--------------------

- Outdoor entering dry-bulb temperature [UnitType.Temperature]
- Indoor entering wet-bulb temperature [UnitType.Temperature]
- Air-side volume flow [UnitType.Flow]
- Total cooling capacity [UnitType.Power]
- Cooling power [UnitType.Power]

Required rated parameters are capacity, power, air flow, indoor entering-air
temperature, and outdoor dry-bulb temperature. Cooling also requires the rated
sensible heat ratio. Heating defaults to the EnergyPlus rating temperatures of
21.11 C indoor and 8.33 C outdoor; cooling defaults to 19.44 C indoor wet-bulb
and 35 C outdoor. The heating coil's minimum outdoor compressor operating
temperature is configurable and defaults to -25 C for cold-climate applications.

.. automodule:: energyplus_pet.equipment.ashp_curve
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:
