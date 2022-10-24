Welcome to EnergyPlus PET's documentation!
==========================================

EnergyPlus is a building simulation tool developed by the United States Department of Energy.
The simulation program is comprised of dozens of different component models which have been developed
over the course of decades.  In some cases there are similarities in the model formulation, but in many cases, due to
either different assumptions, physics, boundary conditions, etc., component models will have their own formulation.

One difficulty in using the various component models in EnergyPlus is how to consume actual manufacturer's data and
get it into a form usable for EnergyPlus.  That's where this tool is helpful.  The long term goal of this tool is to be
able to generate EnergyPlus inputs for a wide variety of the component models that exist inside the simulation program.
With the critical focus on heat pump deployment in our current time, the first models used in this tool are heat pumps.
Over time, other model types will be added.

So how does this tool work?  Well, it's only a few quick steps:

1. Take manufacturer's data and preferably copy and paste it into a spreadsheet to allow quick and easy data prep
2. With this tool, enter any correction factors for the catalog data
3. Then enter the base data set, with some columns potentially being constant, only to be corrected with factors later
4. Let the tool generate parameters!

This documentation will cover walking through the main form operations, as well as providing developer support for
those interested in extending the program or making changes.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   forms/index
   equipment/index
   new_component_type
   new_unit_type
   correction_factor
   data_manager
   exceptions
   runner
   units


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
