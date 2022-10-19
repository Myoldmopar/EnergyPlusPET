from enum import Enum, auto
from tkinter import Toplevel, Frame  # containers
from tkinter import Button, Label, Entry, OptionMenu  # widgets
from tkinter import HORIZONTAL, TOP, X, EW, BOTH  # appearance attributes
from tkinter import StringVar, DoubleVar  # dynamic variables
from tkinter.ttk import Separator

from tksheet import Sheet

from energyplus_pet.correction_factor import CorrectionFactor
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.units import unit_instance_factory


class DetailedCorrectionFactorForm(Toplevel):
    class DetailedCorrectionExitCode(Enum):
        Done = auto()
        Cancel = auto()

    def __init__(self, parent_window, _cf: CorrectionFactor, eq: BaseEquipment):
        super().__init__(parent_window, height=200, width=200)
        p = 4
        self.completed_factor = _cf
        self.equipment_instance = eq
        self.exit_code = DetailedCorrectionFactorForm.DetailedCorrectionExitCode.Done
        self.need_to_conform_units = False
        # create all the objects
        self.intro = Label(self, text="(Update label)")
        #
        s_0 = Separator(self, orient=HORIZONTAL)
        #
        db_frame = Frame(self)
        db_label = Label(db_frame, text="Dry Bulb Value/Units (if applicable):")
        self.db_value = DoubleVar()
        db_value = Entry(db_frame, textvariable=self.db_value)
        options = ["Fahrenheit", "Celsius"]
        self.db_units_string = StringVar(value=options[0])
        db_units = OptionMenu(db_frame, self.db_units_string, *options)
        db_label.grid(row=0, column=0, padx=p, pady=p)
        db_value.grid(row=0, column=1, padx=p, pady=p)
        db_units.grid(row=0, column=2, padx=p, pady=p)
        #
        s_1 = Separator(self, orient=HORIZONTAL)
        #
        replacement_frame = Frame(self)
        replacement_label = Label(replacement_frame, text="Replacement Data Units (if applicable):")
        options_2 = ["Fahrenheit", "Celsius"]
        self.replacement_units_string = StringVar(value=options_2[0])
        replacement_option = OptionMenu(replacement_frame, self.replacement_units_string, *options_2)
        replacement_label.grid(row=0, column=0, padx=p, pady=p)
        replacement_option.grid(row=0, column=1, sticky=EW, padx=p, pady=p)
        #
        s_2 = Separator(self, orient=HORIZONTAL)
        #
        self.tabular_frame = Frame(self)
        # TODO: Does db/wb get two independent value columns?
        column_titles = [eq.headers().name_array()[_cf.base_column_index]]
        for mod_column in _cf.columns_to_modify:
            column_titles.append(eq.headers().name_array()[mod_column])
        column_units = [eq.headers().unit_array()[_cf.base_column_index]]
        for mod_column in _cf.columns_to_modify:
            column_units.append(eq.headers().unit_array()[mod_column])
        # TODO: should the following be +2 for db/wb replacement?
        self.table = Sheet(self.tabular_frame)
        pretend_data = []
        # TODO: Can we just tag a column with a dict of extra data rather than separate lists?
        self.columnar_unit_types = []
        self.columnar_preferred_unit_strings = []  # keep this for convenience
        self.columnar_units_are_preferred = []
        for row in range(_cf.num_corrections + 1):
            this_row = []
            if row == 0:
                for col in range(len(_cf.columns_to_modify) + 1):
                    unit_type = column_units[col]
                    unit_instance = unit_instance_factory(0.0, unit_type)
                    preferred_unit = unit_instance.calculation_unit()
                    all_unit_strings = unit_instance.get_unit_strings()
                    preferred_unit_string = all_unit_strings[preferred_unit]
                    self.columnar_unit_types.append(unit_type)
                    self.columnar_preferred_unit_strings.append(preferred_unit_string)
                    self.columnar_units_are_preferred.append(True)
                    this_row.append(f"{preferred_unit_string}")
                    self.table.create_dropdown(
                        r=row,
                        c=col,
                        values=all_unit_strings,
                        set_value=preferred_unit_string,
                        state="readonly",
                        redraw=False,
                        selection_function=self._units_dropdown_changed,
                        modified_function=None
                    )
            else:
                for col in range(len(_cf.columns_to_modify) + 1):
                    # this_row.append(f"{row},{col}")
                    this_row.append(row * col)
            pretend_data.append(this_row)
        self.table.headers(column_titles)
        self.table.set_sheet_data(pretend_data)
        self.table.enable_bindings()
        self.table.set_options(expand_sheet_if_paste_too_big=False)
        self.table.hide(canvas="row_index")
        self.table.hide(canvas="top_left")
        self.table.set_all_cell_sizes_to_text(redraw=True)
        self.table.pack(side=TOP, expand=True, fill=BOTH, padx=p, pady=p)
        # https://github.com/ragardner/tksheet/blob/master/DOCUMENTATION.md#25-example-custom-right-click-and-text-editor-functionality

        # bind specific events to my own functions
        # self.table.extra_bindings("end_edit_cell", func=self.cell_edited)
        # self.table.extra_bindings("end_paste", func=self.cells_pasted)

        #
        s_3 = Separator(self, orient=HORIZONTAL)
        #
        button_frame = Frame(self)
        self.done_conform_text = StringVar(value="Done")
        btn_done_conform = Button(button_frame, textvariable=self.done_conform_text, command=self._done_or_conform)
        btn_cancel = Button(button_frame, text="Cancel", command=self.cancel)
        btn_done_conform.grid(row=4, column=0, padx=p, pady=p)
        btn_cancel.grid(row=4, column=1, padx=p, pady=p)

        # pack everything
        self.intro.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
        s_0.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
        db_frame.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
        s_1.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
        replacement_frame.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
        s_2.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
        self.tabular_frame.pack(side=TOP, fill=BOTH, expand=True, padx=p, pady=p)
        s_3.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
        button_frame.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)

        # configure the grid
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        # draw factors, in case there already are any
        # self.draw_factors()
        # set up connections/config calls as needed
        pass
        # finalize UI operations
        # self.wait_visibility()
        # self.grab_set()
        # self.transient(parent_window)

    def _units_dropdown_changed(self, edit_cell_event):
        this_column = edit_cell_event.column
        self.need_to_conform_units = False
        for c in range(self.table.total_columns()):
            if c == this_column:
                units_value_this_column = edit_cell_event.text  # currently being modified
            else:
                units_value_this_column = self.table.get_cell_data(0, c)  # just get the data from the cell
            if units_value_this_column != self.columnar_preferred_unit_strings[c]:
                self.need_to_conform_units = True
        self.refresh_done_conform_button_text()

    def refresh_done_conform_button_text(self):
        if self.need_to_conform_units:
            self.done_conform_text.set("Conform")
        else:
            self.done_conform_text.set("Done")
        self.table.redraw()

    def _update_from_traces(self):
        pass

    def _done_or_conform(self):
        if self.need_to_conform_units:
            self.conform_units()
        else:
            self.exit_code = DetailedCorrectionFactorForm.DetailedCorrectionExitCode.Done
            self.grab_release()
            self.destroy()

    def conform_units(self):
        """This is a pretty convoluted way to do this, think harder"""
        for c in range(self.table.total_columns()):
            units_value_this_column = self.table.get_cell_data(0, c)
            if units_value_this_column != self.columnar_preferred_unit_strings[c]:
                # create a dummy value for this unit type -- wrong
                unit_instance_this_column = unit_instance_factory(0.0, self.columnar_unit_types[c])
                # get the full set of unit strings to look the index back up
                unit_strings = unit_instance_this_column.get_unit_strings()
                units_index_now = unit_strings.index(units_value_this_column)
                for r in range(self.table.total_rows()):
                    # if r == 0:
                    #     pass
                    if r == 0:
                        self.table.set_cell_data(r, c, unit_strings[unit_instance_this_column.calculation_unit()])
                    else:
                        cell_value = float(self.table.get_cell_data(r, c))
                        unit_value = unit_instance_factory(cell_value, self.columnar_unit_types[c])
                        unit_value.units = units_index_now
                        unit_value.convert_to_calculation_unit()
                        self.table.set_cell_data(r, c, unit_value.value)
        self.need_to_conform_units = False
        self.refresh_done_conform_button_text()

    def cancel(self):
        self.exit_code = DetailedCorrectionFactorForm.DetailedCorrectionExitCode.Cancel
        self.grab_release()
        self.destroy()


if __name__ == "__main__":
    from tkinter import Tk
    from energyplus_pet.equipment.wwhp_heating_curve import WaterToWaterHeatPumpHeatingCurveFit

    root = Tk()
    cf = CorrectionFactor('blah')
    cf.num_corrections = 5
    cf.base_column_index = 1
    cf.columns_to_modify = [4, 5, 6]
    DetailedCorrectionFactorForm(root, cf, WaterToWaterHeatPumpHeatingCurveFit())
    root.mainloop()
