Equipment Documentation
=======================

This tool is capable of generating parameter summaries and EnergyPlus input parameters 
for a variety of components.  To date, the components are all heat pumps with very similar
mathematical formulations.  Ultimately it is expected that this tool will generate
parameters for a wider variety of building simulation related components.

This document will give a brief overview of the typical parameter generation process,
followed by some basic details of each implemented component type, followed finally by
a set of library documentation for different equipment utility modules.

The parameter estimation tool has, in general, three main goals: flexibly read input data,
process the input data into parameters and coefficients, and present those in a convenient
manner.  The process of generating the parameters and coefficients will primarily rely on
solving a system of equations using a least-squares fit algorithm.  Luckily the gory bits
of solving the system are tucked away inside SciPy and we can leverage that open source
library to do the work for us.  Thus, it is simply the equipment classes responsibility to
properly prepare the bulk input data for processing, and present the data once complete.

The equipment should define the worker function that represents the model formulation.  
For the heat pumps already implemented, the formulations are all very similar, using a
quad-linear equation with 5 coefficients.  Because of this, the function is placed in a 
common location to keep things DRY.  

A typical component will then:

#. Read the catalog data manager's final data set into individual arrays of independent and
dependent variable values.  This will often require scaling the raw variable values to 
make them proper inputs to the curve fit or parameter estimation process.
#. Utilize the base class curve fit functions to massage the data further and utilize
scipy to perform the equation solution.
#. Recalculate new dependent variable values using the original catalog data to determine
how well the coefficients match the catalog data.  These will be stored on the class instance.

Other than these steps, the process of creating a new component is primarily around building
the format for the output objects, and defining some basic parameters to describe the input data.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   base
   wahp_heating_curve
   wahp_cooling_curve
   wwhp_heating_curve
   wwhp_cooling_curve
   column_header
   equip_types
   manager
   common_curves