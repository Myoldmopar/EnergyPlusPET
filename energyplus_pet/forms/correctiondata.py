from enum import Enum, auto
from tkinter import Toplevel, Button, Frame, Label, simpledialog, HORIZONTAL, TOP, X, StringVar, \
    Entry, DoubleVar, OptionMenu, Variable, EW, BooleanVar, Checkbutton, Tk, NSEW, BOTH
from tkinter.ttk import Separator
from tksheet import Sheet

from energyplus_pet.forms.tableview import TableView


class DetailedCorrectionExitCode(Enum):
    Done = auto()
    Cancel = auto()


class DetailedCorrectionFactorForm(Toplevel):
    def __init__(self, parent_window):
        super().__init__(parent_window, height=200, width=200)
        p = 4
        self.data = list(list())
        self.exit_code = DetailedCorrectionExitCode.Done
        # create all the objects
        self.intro = Label(self, text="(Update label)")
        #
        s_0 = Separator(self, orient=HORIZONTAL)
        #
        db_frame = Frame(self)
        db_label = Label(db_frame, text="Dry Bulb Value/Units (if applicable):")
        self.db_value = DoubleVar()
        db_value = Entry(db_frame, textvariable=self.db_value)
        options = ["Farenheit", "Celsius"]
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
        options_2 = ["Farenheit", "Celsius"]
        self.replacement_units_string = StringVar(value=options_2[0])
        replacement_option = OptionMenu(replacement_frame, self.replacement_units_string, *options_2)
        replacement_label.grid(row=0, column=0, padx=p, pady=p)
        replacement_option.grid(row=0, column=1, sticky=EW, padx=p, pady=p)
        #
        s_2 = Separator(self, orient=HORIZONTAL)
        #
        self.tabular_frame = Frame(self)
        # self.table = TableView(self, 5, 5)

        # self.entries = [[Entry(self.tabular_frame, width=10)] * 3] * 4
        # self.vars = [[StringVar(value="a")] * 3] * 4
        # for row_num, row in enumerate(self.entries):
        #     for col_num, entry in enumerate(row):
        #         entry.grid(row=row_num, column=col_num)
        #         self.vars[row_num][col_num].set(f"[{row_num}, {col_num}]")

        self.table = Sheet(self.tabular_frame, data=[[0, 1, 2], [2, 3, 1]])
        self.table.headers(
            newheaders=None, index=None, reset_col_positions=False, show_headers_if_not_sheet=True, redraw=False)
        self.table.enable_bindings()
        self.tabular_frame.grid_columnconfigure(0, weight=1)
        self.tabular_frame.grid_rowconfigure(0, weight=1)

        #
        s_3 = Separator(self, orient=HORIZONTAL)
        #
        button_frame = Frame(self)
        self.done_conform_text = StringVar(value="Done")
        btn_done_conform = Button(button_frame, textvariable=self.done_conform_text, command=self.done_or_conform)
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
        # self.table.frame.pack(side=TOP, expand=False, padx=p, pady=p)
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

    # def draw_factors(self):
    #     # destroy all widgets from frame
    #     for widget in self.tabular_frame.winfo_children():
    #         widget.destroy()
    #     for i, f in enumerate(self.factors):
    #         f.render_as_tk_frame(self.tabular_frame).grid(row=i, column=0, padx=3, pady=3)
    #     self.tabular_frame.grid_columnconfigure(0, weight=1)
    #
    # def add_factor(self):
    #     name = simpledialog.askstring("Correction Factor Name", "Give this correction factor a name", parent=self)
    #     if name is None:
    #         return
    #     self.factors.append(CorrectionFactor(name))
    #     self.draw_factors()

    def done_or_conform(self):
        if self.done_conform_text == "Done":
            self.exit_code = DetailedCorrectionExitCode.Done
            self.grab_release()
            self.destroy()
        else:
            self.conform_units()

    def conform_units(self):
        pass

    def cancel(self):
        self.exit_code = DetailedCorrectionExitCode.Cancel
        self.grab_release()
        self.destroy()


if __name__ == "__main__":
    root = Tk()
    d = DetailedCorrectionFactorForm(root)
    root.mainloop()
