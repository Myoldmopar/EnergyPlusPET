from enum import Enum, auto
from tkinter import Toplevel, Frame, LabelFrame  # containers
from tkinter import Button, Label  # widgets
from tkinter import HORIZONTAL, TOP, X, BOTH, ALL  # appearance attributes
from tkinter import StringVar  # dynamic variables
from tkinter.ttk import Separator
from typing import List

from tksheet import Sheet

from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.exceptions import EnergyPlusPetException
from energyplus_pet.units import unit_class_factory, unit_instance_factory
from energyplus_pet.forms.basic_message_form import PetMessageForm


class MainDataForm(Toplevel):
    """
    This form is where the user will enter/paste the raw (typically pretty large) base data set, which will ultimately
    be processed with any correction factors to determine the final data set.
    """
    class MainDataExitCode(Enum):
        Done = auto()
        Cancel = auto()

    def __init__(self, parent_window, eq: BaseEquipment):
        super().__init__(parent_window, height=200, width=200)
        self.title(f"{parent_window.title()}: Main Catalog Data Input")
        p = 4
        self.equipment_instance = eq
        self.exit_code = MainDataForm.MainDataExitCode.Done
        self.need_to_conform_units = False
        self.final_base_data_rows: List[List[float]] = [[]]
        # create all the objects
        Label(
            self, text="""Now it's time to copy in the bulk of the catalog data.
To be brought in properly, the data should be divided into columns, delimited by tab characters.
This is the way most spreadsheets will store data in the clipboard, so the preferred approach is
to paste/cleanup the data in a spreadsheet, then copy the data and paste directly in the table here."""
        ).pack(
            side=TOP, fill=X, expand=False, padx=p, pady=p
        )
        #
        Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
        #
        tabular_frame = Frame(self)
        column_titles = eq.headers().name_array()
        column_units = eq.headers().unit_array()
        self.table = Sheet(tabular_frame)
        pretend_data = []
        # Would be nice to create a struct of extra data and tag each column with it rather than separate lists
        self.columnar_unit_types = []
        self.columnar_unit_type_classes = []
        self.columnar_unit_id_to_string_mapping = []  # keep this for convenience
        self.columnar_ip_unit_string = []
        self.columnar_preferred_unit_string = []
        self.columnar_units_are_preferred = []  # boolean check
        for row in range(eq.minimum_data_points_for_generation() + 1):
            this_row = []
            if row == 0:
                for col in range(len(column_units)):
                    this_column_unit_type = column_units[col]
                    this_column_unit_type_class = unit_class_factory(this_column_unit_type)
                    self.columnar_unit_type_classes.append(this_column_unit_type_class)
                    this_column_unit_id_to_string_mapping = this_column_unit_type_class.get_unit_string_map()
                    this_column_unit_strings = list(this_column_unit_id_to_string_mapping.values())
                    this_column_preferred_unit_id = this_column_unit_type_class.calculation_unit_id()
                    preferred_unit_string = this_column_unit_id_to_string_mapping[this_column_preferred_unit_id]
                    self.columnar_unit_types.append(this_column_unit_type)
                    self.columnar_unit_id_to_string_mapping.append(this_column_unit_id_to_string_mapping)
                    self.columnar_preferred_unit_string.append(preferred_unit_string)
                    self.columnar_ip_unit_string.append(
                        this_column_unit_id_to_string_mapping[this_column_unit_type_class.base_ip_unit_id()]
                    )
                    self.columnar_units_are_preferred.append(True)
                    this_row.append(f"{preferred_unit_string}")
                    self.table.create_dropdown(
                        r=row,
                        c=col,
                        values=this_column_unit_strings,
                        set_value=preferred_unit_string,
                        state="readonly",
                        redraw=False,
                        selection_function=self._units_changed,
                        modified_function=None
                    )
            else:
                for col in range(len(column_units)):
                    this_row.append(0.0)
            pretend_data.append(this_row)
        self._num_bad_cells = 0
        self.table.headers(column_titles)
        self.table.set_sheet_data(pretend_data)
        self.table.enable_bindings()
        self.table.set_options(expand_sheet_if_paste_too_big=True, paste_insert_column_limit=0)
        self.table.hide(canvas="row_index")
        self.table.hide(canvas="top_left")
        self.table.set_all_cell_sizes_to_text(redraw=True)
        self.table.extra_bindings("end_edit_cell", func=self._cell_edited)
        self.table.extra_bindings("end_paste", func=self._cells_pasted)
        # Undo events in the table could bypass our bindings, need to verify this
        self.table.select_cell(row=1, column=0)
        self.table.pack(side=TOP, expand=True, fill=BOTH, padx=p, pady=p)
        self.table.focus()
        self.expected_num_columns = self.table.total_columns()  # save this to verify later
        tabular_frame.pack(side=TOP, fill=BOTH, expand=True, padx=p, pady=p)
        Label(
            self,
            text="""Once the numeric data is in place, set the numeric units for each column, conform the data if
         necessary, and continue the wizard."""
        ).pack(
            side=TOP, fill=X, expand=False, padx=p, pady=p
        )

        #
        Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
        #
        bottom_button_frame = Frame(self)
        table_ops_label_frame = LabelFrame(bottom_button_frame, text="Table Operations")
        Button(
            table_ops_label_frame, text="Add Table Rows", command=self._add_more_table_rows
        ).grid(
            row=0, column=0, padx=p, pady=p
        )
        Button(
            table_ops_label_frame, text="Shrink Table to Data", command=self._shrink_table_to_data
        ).grid(
            row=0, column=1, padx=p, pady=p
        )
        table_ops_label_frame.grid(row=0, column=0, padx=p, pady=p)
        # Button(
        #     bottom_button_frame, text="Repair Data Column Order", state=DISABLED, command=self._repair
        # ).grid(
        #     row=0, column=1, padx=p, pady=p
        # )
        quick_convert_label_frame = LabelFrame(bottom_button_frame, text="Quick Convert Units")
        Button(
            quick_convert_label_frame, text="IP Units", command=self._quick_convert_ip
        ).grid(
            row=0, column=0, padx=p, pady=p
        )
        Button(
            quick_convert_label_frame, text="SI Units", command=self._quick_convert_si
        ).grid(
            row=0, column=1, padx=p, pady=p
        )
        quick_convert_label_frame.grid(row=0, column=1, padx=p, pady=p)
        workflow_control_label_frame = LabelFrame(bottom_button_frame, text="Primary Controls")
        self.done_conform_text = StringVar(value="Done, Continue")
        Button(
            workflow_control_label_frame, textvariable=self.done_conform_text, command=self._done_or_conform
        ).grid(
            row=0, column=3, padx=p, pady=p
        )
        Button(
            workflow_control_label_frame, text="Cancel Wizard", command=self.cancel
        ).grid(row=0, column=4, padx=p, pady=p)
        workflow_control_label_frame.grid(row=0, column=2, padx=p, pady=p)
        bottom_button_frame.grid_columnconfigure(ALL, weight=1)
        bottom_button_frame.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)

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
        if event.keysym == 'a' and mod_control & event.state:
            self._add_more_table_rows()
        elif event.keysym == 'd' and mod_control & event.state:
            for row in range(self.table.total_rows()):
                if row == 0:
                    continue
                for col in range(self.table.total_columns()):
                    self.table.set_cell_data(row, col, (row + 1.0) * (col + 1.0))
            self.table.redraw()
            self._cells_pasted()

    def _cell_edited(self, event):
        row = event.row
        if row == 0:
            return
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
        self.table.redraw()

    def _cells_pasted(self, _=None):
        self._num_bad_cells = 0
        for row in range(self.table.total_rows()):
            if row == 0:
                continue
            for column in range(self.table.total_columns()):
                try:
                    float(self.table.get_cell_data(row, column))
                    self.table.highlight_cells(row, column, bg='white')
                except ValueError:
                    self._num_bad_cells += 1
                    self.table.highlight_cells(row, column, bg='pink')
        self.table.redraw()

    def _table_data_all_good(self) -> bool:
        return self._num_bad_cells == 0

    def _add_more_table_rows(self):
        self.table.insert_rows(rows=10, redraw=True)

    def _shrink_table_to_data(self):
        # first find the extents of the data
        current_visible_rows = self.table.total_rows()
        max_row_index_found = 0
        for row in range(current_visible_rows):
            for col in range(self.table.total_columns()):
                if self.table.get_cell_data(row, col) != '':
                    max_row_index_found = max(max_row_index_found, row)
        # constrain it to the minimums
        minimum_rows = 2  # with the use of correction factors, we are ok allowing just one row here
        desired_row_count = max(max_row_index_found, minimum_rows)
        # if table is larger than desired, start at the end and remove until we get to the desired value
        if current_visible_rows > desired_row_count:
            for r in range(current_visible_rows - 1, desired_row_count, -1):
                self.table.delete_row(r)
        self.table.redraw()

    def any_blank_cells(self):
        for row in range(self.table.total_rows()):
            for col in range(self.table.total_columns()):
                if self.table.get_cell_data(row, col) == '':
                    return True
        return False

    # def _repair(self): pass

    def _quick_convert_ip(self):
        for col_num in range(self.table.total_columns()):
            self.table.set_cell_data(0, col_num, self.columnar_ip_unit_string[col_num], redraw=True)
        self._units_changed()

    def _quick_convert_si(self):
        for col_num in range(self.table.total_columns()):
            self.table.set_cell_data(0, col_num, self.columnar_preferred_unit_string[col_num], redraw=True)
        self._units_changed()

    def _units_changed(self, dropdown_edit_cell_event=None):
        this_column = dropdown_edit_cell_event.column if dropdown_edit_cell_event else None
        self.need_to_conform_units = False
        for c in range(self.table.total_columns()):
            if c == this_column:
                units_value_this_column = dropdown_edit_cell_event.text  # currently being modified
            else:
                units_value_this_column = self.table.get_cell_data(0, c)  # just get the data from the cell
            if units_value_this_column != self.columnar_preferred_unit_string[c]:
                self.need_to_conform_units = True
        self._cells_pasted()  # simulate a paste event
        self.refresh_done_conform_button_text()

    def refresh_done_conform_button_text(self):
        if self.need_to_conform_units:
            self.done_conform_text.set("Conform units")
        else:
            self.done_conform_text.set("Done, Continue")
        self.table.redraw()

    def _update_from_traces(self):
        pass

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
                    self,
                    "Problem with Table Size",
                    "It appears the table column size does not match the expected size, this is odd, cancel and retry"
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
            self.exit_code = MainDataForm.MainDataExitCode.Done
            self.final_base_data_rows = []
            for row in range(self.table.total_rows()):
                if row == 0:  # unit row
                    continue
                this_row = []
                for column in range(self.table.total_columns()):
                    this_row.append(float(self.table.get_cell_data(row, column)))
                self.final_base_data_rows.append(this_row)
            self.grab_release()
            self.destroy()

    def conform_units(self):
        """This is a pretty convoluted way to do this, think harder"""
        for c in range(self.table.total_columns()):
            current_units_string = self.table.get_cell_data(0, c)
            if current_units_string != self.columnar_preferred_unit_string[c]:
                try:
                    current_unit_id = self.columnar_unit_type_classes[c].get_id_from_unit_string(current_units_string)
                except EnergyPlusPetException:
                    pmf = PetMessageForm(self, "Unit ID Problem", "Could not match unit ID; this is a developer issue.")
                    self.wait_window(pmf)
                    self.cancel()
                    return
                for r in range(self.table.total_rows()):
                    if r == 0:
                        self.table.set_cell_data(r, c, self.columnar_preferred_unit_string[c])
                    else:
                        cell_value = float(self.table.get_cell_data(r, c))
                        unit_value = unit_instance_factory(cell_value, self.columnar_unit_types[c])
                        unit_value.units = current_unit_id
                        unit_value.convert_to_calculation_unit()
                        self.table.set_cell_data(r, c, unit_value.value)
        self.need_to_conform_units = False
        self.refresh_done_conform_button_text()

    def cancel(self):
        self.exit_code = MainDataForm.MainDataExitCode.Cancel
        self.grab_release()
        self.destroy()


if __name__ == "__main__":
    from tkinter import Tk
    from energyplus_pet.equipment.wahp_heating_curve import WaterToAirHeatPumpHeatingCurveFit

    root = Tk()
    MainDataForm(root, WaterToAirHeatPumpHeatingCurveFit())
    root.mainloop()
