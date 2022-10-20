from tkinter import Toplevel, Frame, LabelFrame  # containers
from tkinter import Button, Label, OptionMenu, Entry  # widgets
from tkinter import TOP, X, RIDGE, BOTH  # appearance stuff
from tkinter import StringVar, DoubleVar  # dynamic variables
from typing import Callable

from energyplus_pet.units import BaseUnit
from energyplus_pet.equipment.base import BaseEquipment


class ConstantParameterEntryWidget(Frame):
    def __init__(self, value: BaseUnit, parent_frame: LabelFrame, units_changed_handler: Callable):
        super().__init__(parent_frame, borderwidth=1, relief=RIDGE)
        self.value = value
        self.units_changed_handler = units_changed_handler
        p = 4
        self.unit_strings = self.value.get_unit_strings()
        self.target_unit = self.unit_strings[self.value.units]
        Label(self, text=self.value.name).grid(row=0, column=0, padx=p, pady=p)
        Label(self, text=self.value.description).grid(row=1, column=0, padx=p, pady=p)
        self.var_value = DoubleVar(value=self.value.value)
        Entry(self, textvariable=self.var_value).grid(row=0, column=1, padx=p, pady=p)
        self.var_selected_unit = StringVar(value=self.target_unit)
        OptionMenu(self, self.var_selected_unit, *self.unit_strings).grid(row=1, column=1, padx=p, pady=p)
        self.var_selected_unit.trace('w', self.units_change)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.units_conformed = True

    def units_change(self, *_):
        self.value.units = self.unit_strings.index(self.var_selected_unit.get())
        self.units_conformed = self.var_selected_unit.get() == self.target_unit
        self.units_changed_handler()

    def conform_units(self):
        self.value.convert_to_calculation_unit()
        self.var_value.set(self.value.value)
        self.var_selected_unit.set(self.target_unit)


class ConstantParameterEntryForm(Toplevel):

    def __init__(self, parent_window, equipment: BaseEquipment):
        super().__init__(parent_window)
        self.title(f"{parent_window.title()}: Rated/Constant Parameter Entry")
        self.form_cancelled = True
        self.equipment = equipment
        entries_form = LabelFrame(self, text="Required Parameters")
        self.parameter_value_map = {}
        self.known_parameters = []
        for rp in equipment.required_constant_parameters():
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
        # finalize UI operations
        self.grab_set()
        self.transient(parent_window)

    def check_all_units(self):
        self.need_to_conform_units = False
        for rp in self.known_parameters:
            if not rp.units_conformed:
                self.var_conform_done.set("Conform units")
                self.need_to_conform_units = True
                return
        self.var_conform_done.set("Done, process data now")

    def conform_done(self):
        if self.need_to_conform_units:
            for rp in self.known_parameters:
                rp.conform_units()
            self.check_all_units()
        else:
            self.form_cancelled = False
            for rp in self.known_parameters:
                self.parameter_value_map[rp.value.name] = rp.var_value.get()
            self.close_me()

    def close_me(self):
        self.grab_release()
        self.destroy()

# Private Sub DataValidation(ByVal Sender As Object, ByVal e As System.ComponentModel.CancelEventArgs)
    #     Dim txt As TextBox = TryCast(Sender, TextBox)
    #     If txt Is Nothing Then Exit Sub
    #     If txt.Text = Nothing Then Exit Sub
    #     Dim ValidDataSignal As PublicData.DataValidationReturnType = PublicData.DataValidationTest(txt.Text)
    #     If ValidDataSignal <> DataValidationReturnType.Valid Then
    #         e.Cancel = True
    #         txt.SelectAll()
    #         ERROR
    #     End If
    # End Sub
    #
    # Private Sub DataValidated(ByVal Sender As Object, ByVal e As System.EventArgs)
    #     Dim txt As TextBox = TryCast(Sender, TextBox)
    #     If txt Is Nothing Then Exit Sub
    #     ErrorSignal.SetError(txt, "")
    # End Sub

#
# if __name__ == "__main__":
#     from tkinter import Tk
#     from energyplus_pet.equipment.wwhp_heating_curve import WaterToWaterHeatPumpHeatingCurveFit
#     tk = Tk()
#     e = WaterToWaterHeatPumpHeatingCurveFit()
#     f = ConstantParameterEntryForm(tk, e)
#     tk.mainloop()
