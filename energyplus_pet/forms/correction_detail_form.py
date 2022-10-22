from enum import Enum, auto
from tkinter import Toplevel, Frame  # containers
from tkinter import Button, Label, Entry, OptionMenu  # widgets
from tkinter import HORIZONTAL, TOP, X, W, EW, BOTH  # appearance attributes
from tkinter import StringVar, DoubleVar  # dynamic variables
from tkinter.ttk import Separator

from tksheet import Sheet

from energyplus_pet.correction_factor import CorrectionFactor, CorrectionFactorType
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.units import unit_class_factory, unit_instance_factory, TemperatureValue


class DetailedCorrectionFactorForm(Toplevel):
    """
    This form is where the user will enter correction factor detailed tabular data
    """
    class DetailedCorrectionExitCode(Enum):
        Done = auto()
        Cancel = auto()

    def __init__(self, parent_window, _cf: CorrectionFactor, eq: BaseEquipment, cf_num: int, num_cfs: int):
        super().__init__(parent_window, height=200, width=200)
        p = 4
        self.completed_factor = _cf
        self.equipment_instance = eq
        self.exit_code = DetailedCorrectionFactorForm.DetailedCorrectionExitCode.Done
        self.need_to_conform_units = False
        # create all the objects
        self.title(f"{parent_window.title()}: Enter Correction Factor Data {cf_num}/{num_cfs}")
        m_or_r = 'multiplier' if _cf.correction_type == CorrectionFactorType.Multiplier else 'replacement'
        base_column_name = eq.headers().name_array()[_cf.base_column_index]
        dep_column_names = ""
        for mod_column in _cf.columns_to_modify:
            dep_column_names += f"  -- {eq.headers().name_array()[mod_column]}\n"
        Label(self, text=f"""Entering correction data for ~~ {_cf.name} ~~

This correction factor requires {_cf.num_corrections} {m_or_r} values for {base_column_name}.

The correction factor requires multiplier values for the following {len(_cf.columns_to_modify)} column(s):
{dep_column_names}""").pack(side=TOP, fill=X, anchor=W, expand=False, padx=p, pady=p)
        #
        Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
        #
        if _cf.correction_is_wb_db:
            db_frame = Frame(self)
            db_label = Label(db_frame, text="Dry Bulb Value/Units:")
            self.db_value = DoubleVar()
            db_value = Entry(db_frame, textvariable=self.db_value)
            options = list(TemperatureValue.get_unit_string_map().values())
            preferred_temp_unit_id = TemperatureValue.calculation_unit_id()
            preferred_temp_unit_string = TemperatureValue.get_unit_string_map()[preferred_temp_unit_id]
            # TODO: Need to add tracking and conforming just like the base column units conforming
            self.db_units_string = StringVar(value=preferred_temp_unit_string)
            db_units = OptionMenu(db_frame, self.db_units_string, *options)
            db_label.grid(row=0, column=0, padx=p, pady=p)
            db_value.grid(row=0, column=1, padx=p, pady=p)
            db_units.grid(row=0, column=2, padx=p, pady=p)
            db_frame.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
            Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=p, pady=p)

        if _cf.correction_type == CorrectionFactorType.Replacement:
            replacement_frame = Frame(self)
            replacement_label = Label(replacement_frame, text="Specify the units of the replacement data (column 1):")
            # all we need to do is look up the UnitType for the replacement column
            # from this type, we can get a Base unit class and get everything we need from it.
            # we don't need to create unit-value instances until we are conforming the final data
            # this returns a UnitType enum type of unit, such as UnitType.Temperature or UnitType.FlowRate
            self.replacement_column_unit_type = eq.headers().unit_array()[_cf.base_column_index]
            # this returns a class "type" not an instance, so like TemperatureUnits or PowerUnits
            self.unit_type_class = unit_class_factory(self.replacement_column_unit_type)
            # for this specific unit type, get a mapping of the underlying ids to user-consumable names {'some_id': 'W'}
            self.unit_id_to_string_mapping = self.unit_type_class.get_unit_string_map()
            # one thing we need is a list of all the user-facing unit names, such as ['W', 'kW']
            replacement_unit_strings = list(self.unit_id_to_string_mapping.values())
            # store the preferred replacement_unit id and string
            preferred_replacement_unit_id = self.unit_type_class.calculation_unit_id()
            self.preferred_replacement_unit_string = self.unit_id_to_string_mapping[preferred_replacement_unit_id]
            # create a Tk variable to store the currently shown user string for replacement units
            self.replacement_units_string = StringVar(value=self.preferred_replacement_unit_string)
            replacement_option = OptionMenu(
                replacement_frame, self.replacement_units_string,
                *replacement_unit_strings, command=self._units_changed
            )
            replacement_label.grid(row=0, column=0, padx=p, pady=p)
            replacement_option.grid(row=0, column=1, sticky=EW, padx=p, pady=p)
            replacement_frame.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
            Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=p, pady=p)

        self.tabular_frame = Frame(self)
        # TODO: The table shouldn't allow resizing, right?
        # TODO: Does db/wb get two independent value columns?
        column_titles = [eq.headers().name_array()[_cf.base_column_index]]
        for mod_column in _cf.columns_to_modify:
            column_titles.append(eq.headers().name_array()[mod_column])
        # TODO: should the following be +2 for db/wb replacement?
        self.table = Sheet(self.tabular_frame)
        pretend_data = []  # TODO: Make sure num_corrections is updated if table size changes
        for row in range(_cf.num_corrections):
            this_row = []
            for col in range(len(_cf.columns_to_modify) + 1):
                this_row.append(row * col)
            pretend_data.append(this_row)
        self.table.headers(column_titles)
        self.table.set_sheet_data(pretend_data)
        self.table.enable_bindings()
        self.table.set_options(expand_sheet_if_paste_too_big=False)
        self.table.hide(canvas="row_index")
        self.table.hide(canvas="top_left")
        self.table.set_all_cell_sizes_to_text(redraw=True)
        # https://github.com/ragardner/tksheet/blob/master/DOCUMENTATION.md#25-example-custom-right-click-and-text-editor-functionality
        # self.table.extra_bindings("end_edit_cell", func=self.cell_edited)
        # self.table.extra_bindings("end_paste", func=self.cells_pasted)
        self.table.pack(side=TOP, expand=True, fill=BOTH, padx=p, pady=p)
        self.tabular_frame.pack(side=TOP, fill=BOTH, expand=True, padx=p, pady=p)
        #
        Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
        #
        button_frame = Frame(self)
        self.done_conform_text = StringVar(value="This one is done, continue")
        btn_done_conform = Button(button_frame, textvariable=self.done_conform_text, command=self._done_or_conform)
        btn_cancel = Button(button_frame, text="Cancel Wizard", command=self.cancel)
        btn_done_conform.grid(row=4, column=0, padx=p, pady=p)
        btn_cancel.grid(row=4, column=1, padx=p, pady=p)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)

        # draw factors, in case there already are any
        # self.draw_factors()
        # set up connections/config calls as needed

        # finalize UI operations
        self.grab_set()
        self.transient(parent_window)

    def _units_changed(self, proposed_units):
        """This function is called back by the OptionMenu with the new value, so we don't need to check anything"""
        self.need_to_conform_units = False
        if proposed_units != self.preferred_replacement_unit_string:
            self.need_to_conform_units = True
        self._refresh_done_conform_button_text()

    def _refresh_done_conform_button_text(self):
        if self.need_to_conform_units:
            self.done_conform_text.set("Conform units")
        else:
            self.done_conform_text.set("This one is done, continue")
        self.table.redraw()

    def _done_or_conform(self):
        if self.need_to_conform_units:
            self.conform_units()
        else:
            # OK, so if we are done, units must be ready, so we just need to update the data in the correction factor
            self.exit_code = DetailedCorrectionFactorForm.DetailedCorrectionExitCode.Done
            # read the first column of data into the base correction of the CF
            self.completed_factor.base_correction = [
                float(self.table.get_cell_data(row, 0)) for row in range(self.table.total_rows())
            ]
            # then iterate over the mod column ids of the CF and read the data into lists and then into the CF map
            for col_num, equipment_column_index in enumerate(self.completed_factor.columns_to_modify):
                this_column = []
                for row in range(self.table.total_rows()):
                    this_column.append(float(self.table.get_cell_data(row, col_num)))
                self.completed_factor.mod_correction_data_column_map[equipment_column_index] = this_column
            self.grab_release()
            self.destroy()

    def conform_units(self):
        current_units_string = self.replacement_units_string.get()
        current_unit_id = self.unit_type_class.get_id_from_unit_string(current_units_string)
        for r in range(self.table.total_rows()):
            cell_value = float(self.table.get_cell_data(r, 0))
            unit_value = unit_instance_factory(cell_value, self.replacement_column_unit_type)
            unit_value.units = current_unit_id
            unit_value.convert_to_calculation_unit()
            self.table.set_cell_data(r, 0, unit_value.value)
        self.replacement_units_string.set(self.preferred_replacement_unit_string)
        self.need_to_conform_units = False
        self._refresh_done_conform_button_text()

    def cancel(self):
        self.exit_code = DetailedCorrectionFactorForm.DetailedCorrectionExitCode.Cancel
        self.grab_release()
        self.destroy()


if __name__ == "__main__":
    from tkinter import Tk
    from energyplus_pet.equipment.wahp_heating_curve import WaterToAirHeatPumpHeatingCurveFit

    root = Tk()
    def b(*_): print("hey")
    Button(root, text="Hey", command=b).pack()
    cf = CorrectionFactor('Load Side Temperature Correction')
    cf.num_corrections = 5
    cf.base_column_index = 0
    cf.columns_to_modify = [4, 5, 6]
    cf.correction_type = CorrectionFactorType.Replacement
    DetailedCorrectionFactorForm(root, cf, WaterToAirHeatPumpHeatingCurveFit(), 1, 2)
    root.mainloop()
