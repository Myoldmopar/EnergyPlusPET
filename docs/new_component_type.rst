Adding a New Component Type
===========================

New component types can be added by following a well-defined series of steps, search for these strings in the code:

#. Add component string here, the index should match with the SenderType enumeration below
#. Add component index here, should match with the names defined in EquipNames1 above
#. Add unit type array and header string array here
#. Return proper column header strings, they are defined below
#. Return proper column unit array, they are defined below
#. Return proper dry bulb column index, they are defined below
#. Return proper wet bulb column index, they are defined below
#. Add more nodes to the treeview based on the type added
#. Create an instance of this interface, along with a component data structure
#. Add data structure instances here
#. Pass array of data to each component class structure here
#. Generate a new detailed data form here
#. Retrieve detailed data values here
#. Instantiate proper threaded class and information
#. Add more components here, passing in their data structures and setting the Me.Component object

