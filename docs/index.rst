Welcome to EnergyPlus PET's documentation!
==========================================

PET as in Parameter Estimation Tool, not a friendly supporter that hangs around ready to help...or maybe both?

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   forms/index
   equipment/index
   new_component_type
   new_unit_type
   support_classes

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

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

Installation
------------

This program should be installed from PyPi using ``pip install energyplus_pet``.
Once installed, a new command will be available from that Python environment called ``energyplus_pet_gui``, with a
``.exe`` appended on Windows.  Run this one time right from the command line where ``pip`` was executed to launch the
program.  For easier access, there is an additional executable right next to the main gui executable.  The name
is ``energyplus_pet_configure``.  Simply execute this binary entry point and it will create a desktop shortcut on
Windows, or install a .desktop launcher on Linux, or create an .app bundle on MacOS.  After that, the user should be
able to launch the program from this icon, or from the system shell/spotlight/searcher/start menu.

To get updates to the program, you simply need to install the latest version using the same ``pip`` version, but let
``pip`` know that it can upgrade existing package installations: ``pip install --upgrade energyplus_pet``

Developing
----------

If you are curious about the latest code, or want to open an issue or submit a contribution, check out the repo at
https://github.com/myoldmoopar/EnergyPlusPET.  This will likely soon move to a new location.
