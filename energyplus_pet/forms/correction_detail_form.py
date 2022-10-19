from enum import Enum, auto
from tkinter import Toplevel, Frame  # containers
from tkinter import Button, Label, Entry, OptionMenu  # widgets
from tkinter import HORIZONTAL, TOP, X, W, EW, BOTH  # appearance attributes
from tkinter import StringVar, DoubleVar  # dynamic variables
from tkinter.ttk import Separator

from tksheet import Sheet

from energyplus_pet.correction_factor import CorrectionFactor, CorrectionFactorType
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.units import unit_instance_factory


class DetailedCorrectionFactorForm(Toplevel):
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
        self.title(f"Enter Correction Factor Data {cf_num}/{num_cfs}")
        m_or_r = 'multiplier' if _cf.correction_type == CorrectionFactorType.Multiplier else 'replacement'
        base_column_name = eq.headers().name_array()[_cf.base_column_index]
        dep_column_names = ""
        for mod_column in _cf.get_columns_to_modify():
            dep_column_names += f"  -- {eq.headers().name_array()[mod_column]}\n"
        Label(self, text=f"""Entering correction data for ~~ {_cf.name} ~~

This correction factor requires {_cf.num_corrections} {m_or_r} values for {base_column_name}.

The correction factor requires multiplier values for the following {len(_cf.get_columns_to_modify())} column(s):
{dep_column_names}""").pack(side=TOP, fill=X, anchor=W, expand=False, padx=p, pady=p)
        #
        Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
        #
        if _cf.correction_is_wb_db:
            db_frame = Frame(self)
            db_label = Label(db_frame, text="Dry Bulb Value/Units:")
            self.db_value = DoubleVar()
            db_value = Entry(db_frame, textvariable=self.db_value)
            options = ["Fahrenheit", "Celsius"]  # TODO: Get from TempUnits
            self.db_units_string = StringVar(value=options[0])
            db_units = OptionMenu(db_frame, self.db_units_string, *options)
            db_label.grid(row=0, column=0, padx=p, pady=p)
            db_value.grid(row=0, column=1, padx=p, pady=p)
            db_units.grid(row=0, column=2, padx=p, pady=p)
            db_frame.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
            Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=p, pady=p)

        if _cf.correction_type == CorrectionFactorType.Replacement:
            replacement_frame = Frame(self)
            replacement_label = Label(replacement_frame, text="Specify the units of the replacement data (column 1):")
            base_column_units_type = eq.headers().unit_array()[_cf.base_column_index]
            dummy_units_instance = unit_instance_factory(0.0, base_column_units_type)
            self.replacement_column_unit_type = eq.headers().unit_array()[_cf.base_column_index]
            self.replacement_unit_strings = dummy_units_instance.get_unit_strings()
            self.preferred_replacement_unit_index = dummy_units_instance.calculation_unit()
            self.preferred_replacement_unit_string = dummy_units_instance.get_unit_strings()[
                self.preferred_replacement_unit_index
            ]
            self.replacement_units_string = StringVar(value=self.preferred_replacement_unit_string)
            replacement_option = OptionMenu(
                replacement_frame, self.replacement_units_string,
                *self.replacement_unit_strings, command=self._units_changed
            )
            replacement_label.grid(row=0, column=0, padx=p, pady=p)
            replacement_option.grid(row=0, column=1, sticky=EW, padx=p, pady=p)
            replacement_frame.pack(side=TOP, fill=X, expand=False, padx=p, pady=p)
            Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=p, pady=p)

        self.tabular_frame = Frame(self)
        # TODO: Does db/wb get two independent value columns?
        column_titles = [eq.headers().name_array()[_cf.base_column_index]]
        for mod_column in _cf.get_columns_to_modify():
            column_titles.append(eq.headers().name_array()[mod_column])
        # TODO: should the following be +2 for db/wb replacement?
        self.table = Sheet(self.tabular_frame)
        pretend_data = []  # TODO: Make sure num_corrections is updated if table size changes
        for row in range(_cf.num_corrections):
            this_row = []
            for col in range(len(_cf.get_columns_to_modify()) + 1):
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
        self.done_conform_text = StringVar(value="Done")
        btn_done_conform = Button(button_frame, textvariable=self.done_conform_text, command=self._done_or_conform)
        btn_cancel = Button(button_frame, text="Cancel", command=self.cancel)
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
        self.need_to_conform_units = False
        if proposed_units != self.preferred_replacement_unit_string:
            self.need_to_conform_units = True
        self._refresh_done_conform_button_text()

    def _refresh_done_conform_button_text(self):
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
            self.completed_factor.base_correction = [
                float(self.table.get_cell_data(row, 0)) for row in range(self.table.total_rows())
            ]
            for col_num, equipment_column_index in enumerate(self.completed_factor.get_columns_to_modify()):
                this_column = []
                for row in range(self.table.total_rows()):
                    this_column.append(float(self.table.get_cell_data(row, col_num)))
                self.completed_factor.mod_correction_data_column_map[equipment_column_index] = this_column
            self.grab_release()
            self.destroy()

    def conform_units(self):
        """This is a pretty convoluted way to do this, think harder"""
        # create a dummy value for this unit type -- wrong
        current_units_string = self.replacement_units_string.get()
        # get the full set of unit strings to look the index back up
        units_index_now = self.replacement_unit_strings.index(current_units_string)
        for r in range(self.table.total_rows()):
            cell_value = float(self.table.get_cell_data(r, 0))
            unit_value = unit_instance_factory(cell_value, self.replacement_column_unit_type)
            unit_value.units = units_index_now
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
    from energyplus_pet.equipment.wwhp_heating_curve import WaterToWaterHeatPumpHeatingCurveFit

    root = Tk()
    def b(*_): print("hey")
    Button(root, text="Hey", command=b).pack()
    cf = CorrectionFactor('Load Side Temperature Correction')
    cf.num_corrections = 5
    cf.base_column_index = 0
    cf.set_columns_to_modify([4, 5, 6])
    cf.correction_type = CorrectionFactorType.Replacement
    DetailedCorrectionFactorForm(root, cf, WaterToWaterHeatPumpHeatingCurveFit(), 1, 2)
    root.mainloop()
