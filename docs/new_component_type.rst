Adding a New Component Type
===========================

If you are ready to dive in and implement a new model type in this tool, here are the steps you should take!

#. Identify the model to be implemented, along with identifying the independent and dependent variables
#. Create a new skeleton derived class from an existing component type inside the ``equipment`` folder
#. Generate example and test data, adding it to the ``examples/`` folder, mimicking the existing structures
#. Add entries to the classes and functions inside ``equipment/equip_types.py``
#. Add an entry to the factory method in ``equipment/manager.py``
#. Fully flesh out the equipment derived class, mimicking patterns and examples in other equipment
#. If there are model curve functions that can be reused by other classes, consider adding them to ``common_curves.py``
#. Add branches and nodes to the main form in the ``_build_treeview`` function in ``forms/main.py``

That's it!
