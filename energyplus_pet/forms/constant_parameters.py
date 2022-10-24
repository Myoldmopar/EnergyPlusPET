from tkinter import Toplevel, Frame, LabelFrame  # containers
from tkinter import Button, Label, OptionMenu, Entry  # widgets
from tkinter import TOP, X, RIDGE, BOTH, ALL, END  # appearance stuff
from tkinter import StringVar, DoubleVar  # dynamic variables
from tkinter import TclError
from typing import Callable

from energyplus_pet.forms.basic_message_form import PetMessageForm
from energyplus_pet.units import unit_class_factory, unit_instance_factory
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.exceptions import EnergyPlusPetException


class ConstantParameterEntryWidget(Frame):
    """
    This form is where the user enters any fixed/rated parameter values for this equipment type
    """
    def __init__(
            self, rp: BaseEquipment.RequiredConstantParameter, parent_frame: LabelFrame, units_ch_handler: Callable
    ):
        """
        Constructor for this widget.  Creates a small grid for users to enter a single parameter.
        Four member variables are public:

        * rp_id (str) which is the unique id for this parameter for this equipment type
        * units_conformed (bool) which is a flag for whether the units are ready to go here
        * var_value (Tk.DoubleVar) which holds the value of the parameter, usually accessed after conforming
        * var_units_string (Tk.StringVar) which holds the units of the parameter, usually accessed after conforming

        :param rp: A required constant/rated parameter, defined on each equipment type
        :param parent_frame: A frame to hold this widget
        :param units_ch_handler: A function to be called back to alert the parent of units changes
        """
        super().__init__(parent_frame, borderwidth=1, relief=RIDGE)
        self.rp_id = rp.id
        self._units_changed_handler = units_ch_handler
        p = 4
        self._unit_type = rp.unit_type
        self._unit_type_class = unit_class_factory(self._unit_type)
        self._unit_id_to_string_mapping = self._unit_type_class.get_unit_string_map()
        unit_strings = list(self._unit_id_to_string_mapping.values())
        preferred_unit_id = self._unit_type_class.calculation_unit_id()
        self._preferred_unit_string = self._unit_id_to_string_mapping[preferred_unit_id]
        Label(self, text=rp.title).grid(row=0, column=0, padx=p, pady=p)
        Label(self, text=rp.description).grid(row=1, column=0, padx=p, pady=p)
        # create a tk variable to hold the value in the entry, don't assign it a value yet
        self._tk_var_value = DoubleVar()
        # create the entry pointing it back to the tk variable
        self.entry = Entry(self, textvariable=self._tk_var_value)
        self.entry.grid(row=0, column=1, padx=p, pady=p)
        self.entry.bind('<FocusIn>', lambda x: self.entry.selection_range(0, END))
        # set up a trace to the value to track any changes and assign it in order to initialize self.valid_number flag
        self._tk_var_value.trace('w', self._validate_number)
        self._tk_var_value.set(rp.default_value)
        self.var_units_string = StringVar(value=self._preferred_unit_string)
        o = OptionMenu(self, self.var_units_string, *unit_strings, command=self._units_changed)
        o.config(takefocus=1)
        o.grid(row=1, column=1, padx=p, pady=p)
        self.grid_columnconfigure(ALL, weight=1)
        self.grid_rowconfigure(ALL, weight=1)
        self.units_conformed = True

    def _units_changed(self, proposed_units):
        """Handler for user changing units, just sets a flag for the parent form"""
        self.units_conformed = proposed_units == self._preferred_unit_string
        self._units_changed_handler()

    def _validate_number(self, *_):
        try:
            float(self._tk_var_value.get())
            self.valid_number = True
            self.entry['background'] = 'white'
        except TclError:
            self.valid_number = False
            self.entry['background'] = 'pink'

    def current_value(self):
        """Returns the private value of the numeric entry"""
        return self._tk_var_value.get()

    def conform_units(self):
        """
        Conforms the value to the preferred units for this unit type

        :return: Nothing
        """
        current_units_string = self.var_units_string.get()
        try:
            current_unit_id = self._unit_type_class.get_id_from_unit_string(current_units_string)
        except EnergyPlusPetException:
            pmf = PetMessageForm(self, "Unit ID Problem", "Could not match unit ID; this is a developer issue.")
            self.wait_window(pmf)
            self.units_conformed = False
            return
        current_value = self._tk_var_value.get()
        unit_value = unit_instance_factory(current_value, self._unit_type)
        unit_value.units = current_unit_id
        unit_value.convert_to_calculation_unit()
        self._tk_var_value.set(unit_value.value)
        self.var_units_string.set(self._preferred_unit_string)
        self.units_conformed = True

    def set_focus_to_entry(self):
        """Sets the focus to the entry box, used for initializing the form"""
        self.entry.focus()


class ConstantParameterEntryForm(Toplevel):

    def __init__(self, parent_window, equipment: BaseEquipment):
        super().__init__(parent_window)
        self.title(f"{parent_window.title()}: Rated/Constant Parameter Entry")
        self.form_cancelled = True
        self.equipment = equipment
        entries_form = LabelFrame(self, text="Required Parameters")
        self.parameter_value_map = {}
        self.known_parameters = []
        for rp in equipment.get_required_constant_parameters():
            c = ConstantParameterEntryWidget(rp, entries_form, self.check_all_units)
            c.pack(side=TOP, fill=X, expand=True, padx=4, pady=4)
            self.known_parameters.append(c)
        entries_form.pack(side=TOP, expand=True, fill=BOTH, padx=4, pady=4)
        self.need_to_conform_units = False  # initially it assumes the calculation unit
        button_frame = Frame(self)
        self.var_conform_done = StringVar(value="Done, process data now")
        Button(button_frame, textvariable=self.var_conform_done, command=self.conform_done).grid(
            row=0, column=0, padx=3, pady=3
        )
        Button(button_frame, text="Cancel Wizard", command=self.close_me).grid(row=0, column=1, padx=3, pady=3)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        self.check_all_units()
        self.known_parameters[0].set_focus_to_entry()
        # finalize UI operations
        self.grab_set()
        self.transient(parent_window)

    def check_all_units(self):
        self.need_to_conform_units = False
        for parameter_widget in self.known_parameters:
            if not parameter_widget.units_conformed:
                self.var_conform_done.set("Conform units")
                self.need_to_conform_units = True
                return
        self.var_conform_done.set("Done, process data now")

    def conform_done(self):
        if self.need_to_conform_units:
            for parameter_widget in self.known_parameters:
                parameter_widget.conform_units()
            self.check_all_units()
        else:
            if any([not x.valid_number for x in self.known_parameters]):
                pmf = PetMessageForm(self, "Numeric Issue", "At least one entry has an invalid value, fix and retry.")
                self.wait_window(pmf)
                return
            for parameter_widget in self.known_parameters:
                self.parameter_value_map[parameter_widget.rp_id] = parameter_widget.current_value()
            self.form_cancelled = False
            self.close_me()

    def close_me(self):
        self.grab_release()
        self.destroy()


if __name__ == "__main__":
    from tkinter import Tk
    from energyplus_pet.equipment.wahp_heating_curve import WaterToAirHeatPumpHeatingCurveFit
    tk = Tk()
    e = WaterToAirHeatPumpHeatingCurveFit()
    f = ConstantParameterEntryForm(tk, e)
    tk.mainloop()
