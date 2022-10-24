from enum import Enum, auto
from tkinter import Toplevel, Frame  # containers
from tkinter import Button, Label, OptionMenu  # widgets
from tkinter import HORIZONTAL, TOP, X, W, EW, BOTH  # appearance attributes
from tkinter import StringVar  # dynamic variables
from tkinter.ttk import Separator

from tksheet import Sheet

from energyplus_pet.correction_factor import CorrectionFactor, CorrectionFactorType
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.forms.basic_message_form import PetMessageForm
from energyplus_pet.exceptions import EnergyPlusPetException
from energyplus_pet.units import unit_class_factory, unit_instance_factory, TemperatureValue, UnitType


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
        self.exit_code = DetailedCorrectionFactorForm.DetailedCorrectionExitCode.Cancel
        self.need_to_conform_units = False
        # create all the objects
        self.title(f"{parent_window.title()}: Enter Correction Factor Data {cf_num}/{num_cfs}")
        base_column_name = eq.headers().name_array()[_cf.base_column_index]
        dep_column_names = ""
        for mod_column in _cf.columns_to_modify:
            dep_column_names += f"  -- {eq.headers().name_array()[mod_column]}\n"

        #
        Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
        #
        if _cf.correction_type == CorrectionFactorType.CombinedDbWb:
            Label(self, text=f"""Entering correction data for ~~ {_cf.name} ~~

This correction factor requires {_cf.num_corrections} replacement values for both dry and wet bulb temps.

The correction factor requires multiplier values for the following {len(_cf.columns_to_modify)} column(s):
{dep_column_names}""").pack(side=TOP, fill=X, anchor=W, expand=False, padx=p, pady=p)
            temp_string_options = list(TemperatureValue.get_unit_string_map().values())
            self.preferred_db_wb_unit_id = TemperatureValue.calculation_unit_id()
            self.preferred_db_wb_unit_string = TemperatureValue.get_unit_string_map()[self.preferred_db_wb_unit_id]
            self._tk_var_db_units_string = StringVar(value=self.preferred_db_wb_unit_string)
            self._tk_var_wb_units_string = StringVar(value=self.preferred_db_wb_unit_string)
            self._tk_var_db_units_string.trace('w', self._units_changed)
            self._tk_var_wb_units_string.trace('w', self._units_changed)
            db_wb_frame = Frame(self)
            db_unit_string = f"Units for DB Column: \"{eq.headers().name_array()[eq.headers().get_db_column()]}\""
            Label(db_wb_frame, text=db_unit_string).grid(row=0, column=0, padx=p, pady=p)
            OptionMenu(db_wb_frame, self._tk_var_db_units_string, *temp_string_options).grid(
                row=0, column=1, padx=p, pady=p
            )
            wb_unit_string = f"Units for WB Column: \"{eq.headers().name_array()[eq.headers().get_wb_column()]}\""
            Label(db_wb_frame, text=wb_unit_string).grid(row=1, column=0, padx=p, pady=p)
            OptionMenu(db_wb_frame, self._tk_var_wb_units_string, *temp_string_options).grid(
                row=1, column=1, padx=p, pady=p
            )
            db_wb_frame.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
            Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=p, pady=p)

        elif _cf.correction_type == CorrectionFactorType.Replacement:
            Label(self, text=f"""Entering correction data for ~~ {_cf.name} ~~

This correction factor requires {_cf.num_corrections} replacement values for both dry and wet bulb temps.

The correction factor requires multiplier values for the following {len(_cf.columns_to_modify)} column(s):
{dep_column_names}""").pack(side=TOP, fill=X, anchor=W, expand=False, padx=p, pady=p)
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
            self._tk_var_replacement_units_string = StringVar(value=self.preferred_replacement_unit_string)
            self._tk_var_replacement_units_string.trace('w', self._units_changed)
            replacement_option = OptionMenu(
                replacement_frame, self._tk_var_replacement_units_string, *replacement_unit_strings
            )
            replacement_label.grid(row=0, column=0, padx=p, pady=p)
            replacement_option.grid(row=0, column=1, sticky=EW, padx=p, pady=p)
            replacement_frame.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
            Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=p, pady=p)

        else:  # regular multiplier
            Label(self, text=f"""Entering correction data for ~~ {_cf.name} ~~

This correction factor requires {_cf.num_corrections} multiplier values for {base_column_name}.

The correction factor requires multiplier values for the following {len(_cf.columns_to_modify)} column(s):
{dep_column_names}""").pack(side=TOP, fill=X, anchor=W, expand=False, padx=p, pady=p)

        self.tabular_frame = Frame(self)
        column_titles = list()
        # build out the independent variables first
        if self.completed_factor.correction_type != CorrectionFactorType.CombinedDbWb:
            # just add the one selected base column
            column_titles.append(eq.headers().name_array()[_cf.base_column_index])
        else:
            # this is a db/wb entry, need to add db to column 1 and wb to column 2
            column_titles.append(eq.headers().name_array()[eq.headers().get_db_column()])
            column_titles.append(eq.headers().name_array()[eq.headers().get_wb_column()])
        # then add the dependent variables
        for mod_column in _cf.columns_to_modify:
            column_titles.append(eq.headers().name_array()[mod_column])
        num_columns_in_table = len(column_titles)
        num_rows_in_table = self.completed_factor.num_corrections  # no need to add a header or anything here
        pretend_data = []
        for row in range(num_rows_in_table):
            this_row = []
            for col in range(num_columns_in_table):
                this_row.append(0.0)
            pretend_data.append(this_row)
        self._num_bad_cells = 0
        self.table = Sheet(self.tabular_frame)
        self.table.set_sheet_data(pretend_data)
        self.table.headers(column_titles)
        self.table.enable_bindings()
        self.table.set_options(expand_sheet_if_paste_too_big=False)
        self.table.hide(canvas="row_index")
        self.table.hide(canvas="top_left")
        self.table.set_all_cell_sizes_to_text(redraw=True)
        # https://github.com/ragardner/tksheet/blob/master/DOCUMENTATION.md#25-example-custom-right-click-and-text-editor-functionality
        self.table.extra_bindings("end_edit_cell", func=self._cell_edited)
        self.table.extra_bindings("end_paste", func=self._cells_pasted)
        self.table.pack(side=TOP, expand=True, fill=BOTH, padx=p, pady=p)
        self.table.select_cell(row=0, column=0)
        self.table.focus()
        self.tabular_frame.pack(side=TOP, fill=BOTH, expand=True, padx=p, pady=p)
        # we block resizing the table when pasting, and we are hiding the row titles to block inserting rows via title,
        # but we can't seem to block tksheet from allowing a column insert, so we will just have to check later
        # https://github.com/ragardner/tksheet/blob/0ed6ee8611a7062eedfe43333e7760e1f22088af/tksheet/_tksheet_main_table.py#L3172
        # store the expected number of columns and if it doesn't match later just make the user fix it
        self.expected_num_columns: int = self.table.total_columns()
        #
        Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
        #
        button_frame = Frame(self)
        self._tk_var_done_conform_text = StringVar(value="This one is done, continue")
        btn_done_conform = Button(
            button_frame, textvariable=self._tk_var_done_conform_text, command=self._done_or_conform
        )
        btn_cancel = Button(button_frame, text="Cancel Wizard", command=self.cancel)
        btn_done_conform.grid(row=4, column=0, padx=p, pady=p)
        btn_cancel.grid(row=4, column=1, padx=p, pady=p)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)

        # draw factors, in case there already are any
        # self.draw_factors()

        # set up keybinding and flags
        self.bind('<Key>', self._handle_button_pressed)

        # finalize UI operations
        self.grab_set()
        self.transient(parent_window)

    def _handle_button_pressed(self, event):
        # relevant_modifiers
        # mod_shift = 0x1
        mod_control = 0x4
        # mod_alt = 0x20000
        if event.keysym == 'd' and mod_control & event.state:
            for row in range(self.completed_factor.num_corrections):
                for col in range(len(self.completed_factor.columns_to_modify) + 1):
                    self.table.set_cell_data(row, col, (row + 1.0) * (col + 1.0))
            self._cells_pasted()

    def _cell_edited(self, event):
        row = event.row
        column = event.column
        # first check the current value to see if it was already bad -- it will be the old value in the cell
        current_value = self.table.get_cell_data(row, column)
        try:
            float(current_value)
            was_good = True
        except ValueError:
            was_good = False
        try:
            float(event.text)
            self.table.highlight_cells(row, column, bg='white')
            # if it was good already, and good now, we are done
            # if it was bad, and now good, decrement the counter
            if not was_good:
                self._num_bad_cells -= 1
        except ValueError:
            self.table.highlight_cells(row, column, bg='pink')
            # if it was bad already, and bad now, we are done
            # if it was good, and now bad, increment the counter
            if was_good:
                self._num_bad_cells += 1

    def _cells_pasted(self, _=None):
        self._num_bad_cells = 0
        for row in range(self.table.total_rows()):
            for column in range(self.table.total_columns()):
                try:
                    float(self.table.get_cell_data(row, column))
                    self.table.highlight_cells(row, column, bg='white')
                except ValueError:
                    self._num_bad_cells += 1
                    self.table.highlight_cells(row, column, bg='pink')

    def _table_data_all_good(self) -> bool:
        return self._num_bad_cells == 0

    def any_blank_cells(self):
        for row in range(self.table.total_rows()):
            for col in range(self.table.total_columns()):
                if self.table.get_cell_data(row, col) == '':
                    return True
        return False

    def _units_changed(self, *_):
        """This function is called back by the unit traces, just check all of them"""
        self.need_to_conform_units = False
        if self.completed_factor.correction_type == CorrectionFactorType.Multiplier:
            pass  # nothing to be done, there are no units to conform
        elif self.completed_factor.correction_type == CorrectionFactorType.Replacement:
            if self._tk_var_replacement_units_string.get() != self.preferred_replacement_unit_string:
                self.need_to_conform_units = True
        elif self.completed_factor.correction_type == CorrectionFactorType.CombinedDbWb:
            if self._tk_var_db_units_string.get() != self.preferred_db_wb_unit_string:
                self.need_to_conform_units = True
            if self._tk_var_wb_units_string.get() != self.preferred_db_wb_unit_string:
                self.need_to_conform_units = True
        self._refresh_done_conform_button_text()

    def _refresh_done_conform_button_text(self):
        if self.need_to_conform_units:
            self._tk_var_done_conform_text.set("Conform units")
        else:
            self._tk_var_done_conform_text.set("This one is done, continue")
        self.table.redraw()

    def _done_or_conform(self):
        # don't try to conorm or exit if there are any bad values
        if not self._table_data_all_good():
            message_window = PetMessageForm(
                self, "Value Issue", f"{self._num_bad_cells} cell(s) appear to have bad values; fix them and retry"
            )
            self.wait_window(message_window)
            return
        if self.need_to_conform_units:
            self.conform_units()
        else:
            if self.expected_num_columns != self.table.total_columns():
                message_window = PetMessageForm(
                    self, "Problem with Table Size", "Table column size does not match expected size, cancel and retry"
                )
                self.wait_window(message_window)
                return
            if self.any_blank_cells():
                message_window = PetMessageForm(
                    self,
                    "Problem with Table Entries",
                    "Blank entries detected in the table, fix and retry"
                )
                self.wait_window(message_window)
                return
            for r in range(self.table.total_rows()):
                for c in range(self.table.total_columns()):
                    value = self.table.get_cell_data(r, c)
                    if value == '':
                        message_window = PetMessageForm(
                            self,
                            "Problem with Correction Factor Data",
                            "Encountered at least one blank cell in the data, populate the full table and retry"
                        )
                        self.wait_window(message_window)
                        return
            # OK, so if we are done, units must be ready, so we just need to update the data in the correction factor
            # for regular correction factors, read the first column of data into the base correction of the CF
            if self.completed_factor.correction_type != CorrectionFactorType.CombinedDbWb:
                self.completed_factor.base_correction = [
                    float(self.table.get_cell_data(row, 0)) for row in range(self.completed_factor.num_corrections)
                ]
                last_column_read = 0
            else:  # for db/wb, read the first column into the db array and the second column into the wb array
                self.completed_factor.base_correction_db = [
                    float(self.table.get_cell_data(row, 0)) for row in range(self.completed_factor.num_corrections)
                ]
                self.completed_factor.base_correction_wb = [
                    float(self.table.get_cell_data(row, 1)) for row in range(self.completed_factor.num_corrections)
                ]
                last_column_read = 1
            # then iterate over the mod column ids of the CF and read the data into lists and then into the CF map
            for equipment_column_index in self.completed_factor.columns_to_modify:
                last_column_read += 1
                this_column = []
                for row in range(self.table.total_rows()):
                    this_column.append(float(self.table.get_cell_data(row, last_column_read)))
                self.completed_factor.mod_correction_data_column_map[equipment_column_index] = this_column
            output_message = ""
            db = self.equipment_instance.headers().get_db_column()
            wb = self.equipment_instance.headers().get_wb_column()
            if not self.completed_factor.check_ok(db, wb):
                output_message += f"Errors for {self.completed_factor.name}:\n"
                for e in self.completed_factor.check_ok_messages:
                    output_message += f" - {e}\n"
            if output_message:
                message_window = PetMessageForm(
                    self, "Problem with Correction Factor", output_message, justify_message_left=True
                )
                self.wait_window(message_window)
                return
            self.exit_code = DetailedCorrectionFactorForm.DetailedCorrectionExitCode.Done
            self.grab_release()
            self.destroy()

    def conform_units(self):
        if self.completed_factor.correction_type == CorrectionFactorType.Multiplier:
            pass  # shouldn't have been able to get here, just carry on, nothing to do
        elif self.completed_factor.correction_type == CorrectionFactorType.Replacement:
            db_units_string = self._tk_var_replacement_units_string.get()
            try:
                current_db_unit_id = self.unit_type_class.get_id_from_unit_string(db_units_string)
            except EnergyPlusPetException:
                pmf = PetMessageForm(self, "Unit ID Problem", "Could not match unit ID; this is a developer issue.")
                self.wait_window(pmf)
                self.cancel()
                return
            for r in range(self.table.total_rows()):
                cell_value = float(self.table.get_cell_data(r, 0))
                unit_value = unit_instance_factory(cell_value, self.replacement_column_unit_type)
                unit_value.units = current_db_unit_id
                unit_value.convert_to_calculation_unit()
                self.table.set_cell_data(r, 0, unit_value.value)
            self._tk_var_replacement_units_string.set(self.preferred_replacement_unit_string)
        elif self.completed_factor.correction_type == CorrectionFactorType.CombinedDbWb:
            db_units_string = self._tk_var_db_units_string.get()
            try:
                current_db_unit_id = TemperatureValue.get_id_from_unit_string(db_units_string)
            except EnergyPlusPetException:
                pmf = PetMessageForm(self, "Unit ID Problem", "Could not match DB unit ID; this is a developer issue.")
                self.wait_window(pmf)
                self.cancel()
                return
            for r in range(self.table.total_rows()):
                cell_value = float(self.table.get_cell_data(r, 0))
                unit_value = unit_instance_factory(cell_value, UnitType.Temperature)
                unit_value.units = current_db_unit_id
                unit_value.convert_to_calculation_unit()
                self.table.set_cell_data(r, 0, unit_value.value)
            self._tk_var_db_units_string.set(self.preferred_db_wb_unit_string)
            wb_units_string = self._tk_var_wb_units_string.get()
            try:
                current_wb_unit_id = TemperatureValue.get_id_from_unit_string(wb_units_string)
            except EnergyPlusPetException:
                pmf = PetMessageForm(self, "Unit ID Problem", "Could not match WB unit ID; this is a developer issue.")
                self.wait_window(pmf)
                self.cancel()
                return
            for r in range(self.table.total_rows()):
                cell_value = float(self.table.get_cell_data(r, 1))
                unit_value = unit_instance_factory(cell_value, UnitType.Temperature)
                unit_value.units = current_wb_unit_id
                unit_value.convert_to_calculation_unit()
                self.table.set_cell_data(r, 1, unit_value.value)
            self._tk_var_wb_units_string.set(self.preferred_db_wb_unit_string)
        self.need_to_conform_units = False
        self._refresh_done_conform_button_text()

    def cancel(self):
        self.exit_code = DetailedCorrectionFactorForm.DetailedCorrectionExitCode.Cancel
        self.grab_release()
        self.destroy()


if __name__ == "__main__":
    from tkinter import Tk
    from energyplus_pet.equipment.wahp_cooling_curve import WaterToAirHeatPumpCoolingCurveFit

    root = Tk()
    cf = CorrectionFactor('Load Side DB/WB Temperature Correction')
    cf.num_corrections = 2
    cf.base_column_index = 0
    cf.columns_to_modify = [4, 5, 6]
    cf.correction_type = CorrectionFactorType.Multiplier
    _eq = WaterToAirHeatPumpCoolingCurveFit()
    DetailedCorrectionFactorForm(root, cf, _eq, 1, 1)
    root.mainloop()
