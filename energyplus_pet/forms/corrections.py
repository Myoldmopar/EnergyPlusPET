from enum import Enum, auto
from tkinter import Toplevel, Button, Frame, Label, simpledialog, HORIZONTAL, TOP, X, StringVar
from tkinter.ttk import Separator
from typing import List

from energyplus_pet.corrections import CorrectionFactor


class CorrectionFactorFormResponse(Enum):
    Cancel = auto()
    Done = auto()
    Skip = auto()
    Error = auto()


class CorrectionFactorForm(Toplevel):
    def __init__(self, parent_window, existing_factors: List[CorrectionFactor] = None):
        super().__init__(parent_window, height=200, width=200)
        if existing_factors is None:
            existing_factors = []
        self.factors: List[CorrectionFactor] = existing_factors
        self.exit_code = CorrectionFactorFormResponse.Error
        # create all the objects
        lbl = Label(self, text="""In order to estimate parameters, all data categories should have at least two values.
If all values are constant, a curve fit cannot be generated.
It is common for manufacturers to only give a constant value for certain data.
This is typically entering temperatures or flow rates.
They will then give correction factor data in order to modify this value.
These correction factors can be new flow rate/temperature values, or multipliers from the base values.
If you have any correction factors, add them here, otherwise, press done to continue.""")
        s_0 = Separator(self, orient=HORIZONTAL)
        self.factor_frame = Frame(self, height=20)
        s_1 = Separator(self, orient=HORIZONTAL)
        button_frame = Frame(self)
        btn_add = Button(button_frame, text="Add Factor", command=self.add_factor)
        self.txt_ok_skip = StringVar()
        btn_ok_skip = Button(button_frame, textvariable=self.txt_ok_skip, command=self.ok_skip)
        btn_cancel = Button(button_frame, text="Cancel", command=self.cancel)
        # pack everything
        lbl.pack(side=TOP, fill=X, expand=True, padx=3, pady=3)
        s_0.pack(side=TOP, fill=X, expand=True, padx=3, pady=3)
        self.factor_frame.pack(side=TOP, fill=X, expand=True, padx=3, pady=3)
        s_1.pack(side=TOP, fill=X, expand=True, padx=3, pady=3)
        button_frame.pack(side=TOP, fill=X, expand=True, padx=3, pady=3)
        btn_add.grid(row=0, column=0, padx=3, pady=3)
        btn_ok_skip.grid(row=0, column=1, padx=3, pady=3)
        btn_cancel.grid(row=0, column=2, padx=3, pady=3)
        # configure the grid
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        # draw factors, in case there already are any
        self.draw_factors()
        # set up connections/config calls as needed
        pass
        # finalize UI operations
        self.wait_visibility()
        self.grab_set()
        self.transient(parent_window)

    def draw_factors(self):
        # destroy all widgets from frame
        for widget in self.factor_frame.winfo_children():
            widget.destroy()
        for i, f in enumerate(self.factors):
            f.render_as_tk_frame(self.factor_frame).grid(row=i, column=0, padx=3, pady=3)
        self.factor_frame.grid_columnconfigure(0, weight=1)

    def add_factor(self):
        name = simpledialog.askstring("Correction Factor Name", "Give this correction factor a name", parent=self)
        if name is None:
            return
        self.factors.append(CorrectionFactor(name))
        self.draw_factors()

    def ok_skip(self):
        if self.txt_ok_skip == "OK":
            self.exit_code = CorrectionFactorFormResponse.Done
        else:
            self.exit_code = CorrectionFactorFormResponse.Skip
        self.grab_release()
        self.destroy()

    def cancel(self):
        self.grab_release()
        self.destroy()
