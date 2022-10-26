Adding a New Unit Type
===========================

If you are interested in adding a new unit type (dimension) or a new unit for a given dimension, follow these steps:

#. For a new unit type, create a new entry in the ``UnitType`` enum in ``units.py``
#. For a new unit type, create a new derived class that inherits ``BaseValueWithUnit``, mimicking patterns as needed
#. For just a new unit within a given type, just add a new ID to the unit type class, and update the unit string/id/convert functions accordingly
